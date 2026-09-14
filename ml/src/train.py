"""Train, compare, evaluate, and save BhoomiGuard delay classifiers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, brier_score_loss, confusion_matrix, f1_score, log_loss,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

try:
    from .config import (CALIBRATION_CV_FOLDS, CALIBRATION_MIN_BRIER_IMPROVEMENT,
                         CALIBRATION_RELIABILITY_BINS, CLASSIFIER_MODEL_PATH, FEATURE_COLUMNS,
                         MODEL_METADATA_PATH, MODEL_VERSION, RANDOM_SEED, RAW_DATA_PATH,
                         RISK_THRESHOLDS, TEST_SIZE)
    from .preprocessing import build_preprocessor, get_feature_frame, get_targets
except ImportError:  # Allows: python ml/src/train.py
    from config import (CALIBRATION_CV_FOLDS, CALIBRATION_MIN_BRIER_IMPROVEMENT,
                        CALIBRATION_RELIABILITY_BINS, CLASSIFIER_MODEL_PATH, FEATURE_COLUMNS,
                        MODEL_METADATA_PATH, MODEL_VERSION, RANDOM_SEED, RAW_DATA_PATH,
                        RISK_THRESHOLDS, TEST_SIZE)
    from preprocessing import build_preprocessor, get_feature_frame, get_targets


def build_candidate_models(seed: int = RANDOM_SEED) -> dict[str, Pipeline]:
    """Create candidate models, each with the exact same feature transformation."""
    classifiers = {
        "Logistic Regression": LogisticRegression(max_iter=1_000, class_weight="balanced", random_state=seed),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=3, class_weight="balanced", random_state=seed, n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=250, max_depth=5, learning_rate=.05, subsample=.85, colsample_bytree=.85,
            eval_metric="logloss", random_state=seed, n_jobs=1,
        ),
    }
    return {name: Pipeline([("preprocessor", build_preprocessor()), ("classifier", estimator)])
            for name, estimator in classifiers.items()}


def _reliability_bins(target: pd.Series, probabilities: np.ndarray) -> list[dict[str, Any]]:
    """Summarize probability reliability without suppressing empty bins."""
    bins: list[dict[str, Any]] = []
    for index in range(CALIBRATION_RELIABILITY_BINS):
        lower, upper = index / CALIBRATION_RELIABILITY_BINS, (index + 1) / CALIBRATION_RELIABILITY_BINS
        mask = ((probabilities >= lower) & (probabilities < upper)) if index < CALIBRATION_RELIABILITY_BINS - 1 else (
            (probabilities >= lower) & (probabilities <= upper)
        )
        count = int(mask.sum())
        bins.append({
            "lower": round(lower, 2), "upper": round(upper, 2), "count": count,
            "mean_predicted_probability": round(float(probabilities[mask].mean()), 6) if count else None,
            "observed_positive_rate": round(float(target.iloc[np.flatnonzero(mask)].mean()), 6) if count else None,
        })
    return bins


def evaluate_probabilities(target: pd.Series, probabilities: np.ndarray) -> dict[str, Any]:
    """Calculate discrimination, calibration, and distribution metrics on held-out data."""
    probabilities = np.asarray(probabilities, dtype=float)
    predictions = (probabilities >= .5).astype(int)
    tn, fp, fn, tp = confusion_matrix(target, predictions, labels=[0, 1]).ravel()
    return {
        "accuracy": round(float(accuracy_score(target, predictions)), 4),
        "precision": round(float(precision_score(target, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(target, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(target, predictions, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(target, probabilities)), 4),
        "brier_score": round(float(brier_score_loss(target, probabilities)), 6),
        "log_loss": round(float(log_loss(target, probabilities)), 6),
        "mean_predicted_probability": round(float(probabilities.mean()), 6),
        "observed_positive_rate": round(float(target.mean()), 6),
        "probability_range": [round(float(probabilities.min()), 6), round(float(probabilities.max()), 6)],
        "probability_distribution": [
            int((((probabilities >= index / 10) & (probabilities < (index + 1) / 10)) if index < 9
                 else ((probabilities >= .9) & (probabilities <= 1))).sum())
            for index in range(10)
        ],
        "high_probability_counts": {
            threshold: int((probabilities >= float(threshold)).sum())
            for threshold in ("0.90", "0.95", "0.99", "0.999")
        },
        "risk_band_distribution": {
            label: int(((probabilities * 100 >= lower) & (probabilities * 100 < upper)).sum())
            for lower, upper, label in ((0, 25, "Low"), (25, 50, "Moderate"), (50, 75, "High"), (75, 101, "Critical"))
        },
        "reliability_bins": _reliability_bins(target.reset_index(drop=True), probabilities),
        "true_positives": int(tp), "true_negatives": int(tn),
        "false_positives": int(fp), "false_negatives": int(fn),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }


def evaluate_classifier(model: Pipeline, features: pd.DataFrame, target: pd.Series) -> dict[str, Any]:
    """Calculate metrics from an untouched held-out test set."""
    return evaluate_probabilities(target, model.predict_proba(features)[:, 1])


def compare_calibration_strategies(
    base_model: Pipeline, x_train: pd.DataFrame, y_train: pd.Series,
    x_test: pd.DataFrame, y_test: pd.Series, seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    """Evaluate raw, sigmoid, and isotonic probabilities without calibration leakage.

    Mappings fit only on five-fold out-of-fold training predictions. The test partition is
    never used to fit a mapping and is used once for the final comparison.
    """
    folds = StratifiedKFold(n_splits=CALIBRATION_CV_FOLDS, shuffle=True, random_state=seed)
    oof_probabilities = cross_val_predict(
        clone(base_model), x_train, y_train, cv=folds, method="predict_proba", n_jobs=1,
    )[:, 1]
    raw_probabilities = base_model.predict_proba(x_test)[:, 1]
    sigmoid = LogisticRegression(random_state=seed).fit(oof_probabilities.reshape(-1, 1), y_train)
    isotonic = IsotonicRegression(out_of_bounds="clip").fit(oof_probabilities, y_train)
    strategy_probabilities = {
        "none": raw_probabilities,
        "sigmoid": sigmoid.predict_proba(raw_probabilities.reshape(-1, 1))[:, 1],
        "isotonic": isotonic.predict(raw_probabilities),
    }
    comparison = {name: evaluate_probabilities(y_test, probabilities)
                  for name, probabilities in strategy_probabilities.items()}
    raw = comparison["none"]
    sigmoid_metrics = comparison["sigmoid"]
    sigmoid_meets_criterion = (
        raw["brier_score"] - sigmoid_metrics["brier_score"] >= CALIBRATION_MIN_BRIER_IMPROVEMENT
        and sigmoid_metrics["log_loss"] <= raw["log_loss"]
    )
    # Phase 2 records evidence rather than silently changing production inference on a
    # synthetic dataset. The current 5,000-row baseline does not meet this criterion.
    selected_method = "none"
    selection_reason = (
        "No calibration mapping was adopted: sigmoid did not meet the minimum held-out Brier improvement "
        "without worsening log loss. Isotonic was evaluated as a diagnostic only because its flexible "
        "mapping has greater overfitting risk on this synthetic prototype distribution."
        if not sigmoid_meets_criterion else
        "A sigmoid mapping met the prototype numerical criterion on this run, but production adoption requires "
        "explicit review before changing the public probability contract."
    )
    return {
        "selected_method": selected_method, "selection_reason": selection_reason,
        "strategy": f"{CALIBRATION_CV_FOLDS}-fold stratified out-of-fold calibration on the training partition; untouched held-out test evaluation",
        "comparison": comparison,
        "calibration_training_rows": int(len(x_train)), "held_out_evaluation_rows": int(len(x_test)),
        "random_seed": seed,
    }


def _selection_score(metrics: dict[str, Any]) -> float:
    """Rank candidates with recall emphasized for early-warning decisions."""
    return .40 * metrics["recall"] + .30 * metrics["f1"] + .30 * metrics["roc_auc"]


def train_and_save(
    dataset_path: Path = RAW_DATA_PATH,
    model_path: Path = CLASSIFIER_MODEL_PATH,
    metadata_path: Path = MODEL_METADATA_PATH,
    seed: int = RANDOM_SEED,
) -> tuple[Pipeline, dict[str, Any]]:
    """Train candidates, select one using recall/F1/AUC, and save its complete pipeline."""
    data = pd.read_csv(dataset_path)
    features, targets = get_feature_frame(data), get_targets(data)
    excluded_columns = [column for column in data.columns if column not in FEATURE_COLUMNS]
    print(f"Total available columns: {len(data.columns)}")
    print(f"Model input columns ({len(FEATURE_COLUMNS)}): {list(FEATURE_COLUMNS)}")
    print(f"Excluded columns: {excluded_columns}")
    if set(("project_id", "delay_flag", "actual_delay_days")).intersection(FEATURE_COLUMNS):
        raise ValueError("Target or identifier leakage detected in model features.")

    x_train, x_test, y_train, y_test = train_test_split(
        features, targets["delay_flag"], test_size=TEST_SIZE, random_state=seed, stratify=targets["delay_flag"]
    )
    metrics_by_model: dict[str, dict[str, Any]] = {}
    fitted_models: dict[str, Pipeline] = {}
    for name, candidate in build_candidate_models(seed).items():
        candidate.fit(x_train, y_train)
        fitted_models[name] = candidate
        metrics_by_model[name] = evaluate_classifier(candidate, x_test, y_test)

    selected_name = max(metrics_by_model, key=lambda name: _selection_score(metrics_by_model[name]))
    selected_model = fitted_models[selected_name]
    calibration = compare_calibration_strategies(selected_model, x_train, y_train, x_test, y_test, seed)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(selected_model, model_path)
    metadata: dict[str, Any] = {
        "model_name": selected_name, "model_version": MODEL_VERSION,
        "training_datetime_utc": datetime.now(timezone.utc).isoformat(), "random_seed": seed,
        "feature_names": list(FEATURE_COLUMNS), "target": "delay_flag",
        "train_size": len(x_train), "test_size": len(x_test), "dataset_path": str(dataset_path),
        "evaluation_metrics": metrics_by_model, "selection_criterion": (
            "Highest weighted score: 40% recall, 30% F1, 30% ROC-AUC. Recall is emphasized "
            "because missed delayed projects are costly in an early-warning workflow."
        ),
        "calibration": {
            "base_model_type": selected_name,
            "selected_method": calibration["selected_method"],
            "probability_source": "base_pipeline.predict_proba" if calibration["selected_method"] == "none"
            else "validated_calibration_mapping",
            "calibration_artifact": None,
            "evaluation": calibration,
        },
        "risk_thresholds": {label: f"< {upper}" for upper, label in RISK_THRESHOLDS},
        "synthetic_data_disclaimer": (
            "Performance is measured on synthetic prototype data and does not establish real-world "
            "government deployment accuracy."
        ),
        "duration_regression_status": "Placeholder only; Step 2A will implement actual_delay_days regression.",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return selected_model, metadata


def print_comparison(metadata: dict[str, Any]) -> None:
    """Print the held-out evaluation comparison without claiming real-world performance."""
    print("\nHeld-out test-set model comparison")
    print("| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for name, metrics in metadata["evaluation_metrics"].items():
        print(f"| {name} | {metrics['accuracy']:.4f} | {metrics['precision']:.4f} | "
              f"{metrics['recall']:.4f} | {metrics['f1']:.4f} | {metrics['roc_auc']:.4f} |")
        print(f"  TP={metrics['true_positives']} TN={metrics['true_negatives']} "
              f"FP={metrics['false_positives']} FN={metrics['false_negatives']}")
    print(f"Selected model: {metadata['model_name']}")


if __name__ == "__main__":
    _, trained_metadata = train_and_save()
    print_comparison(trained_metadata)
