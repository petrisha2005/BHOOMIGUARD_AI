"""Train, compare, evaluate, and save BhoomiGuard delay classifiers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

try:
    from .config import (CLASSIFIER_MODEL_PATH, FEATURE_COLUMNS, MODEL_METADATA_PATH, MODEL_VERSION,
                         RANDOM_SEED, RAW_DATA_PATH, RISK_THRESHOLDS, TEST_SIZE)
    from .preprocessing import build_preprocessor, get_feature_frame, get_targets
except ImportError:  # Allows: python ml/src/train.py
    from config import (CLASSIFIER_MODEL_PATH, FEATURE_COLUMNS, MODEL_METADATA_PATH, MODEL_VERSION,
                        RANDOM_SEED, RAW_DATA_PATH, RISK_THRESHOLDS, TEST_SIZE)
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


def evaluate_classifier(model: Pipeline, features: pd.DataFrame, target: pd.Series) -> dict[str, Any]:
    """Calculate classification metrics from an untouched held-out test set."""
    predictions = model.predict(features)
    probabilities = model.predict_proba(features)[:, 1]
    tn, fp, fn, tp = confusion_matrix(target, predictions, labels=[0, 1]).ravel()
    return {
        "accuracy": round(float(accuracy_score(target, predictions)), 4),
        "precision": round(float(precision_score(target, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(target, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(target, predictions, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(target, probabilities)), 4),
        "true_positives": int(tp), "true_negatives": int(tn),
        "false_positives": int(fp), "false_negatives": int(fn),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
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
