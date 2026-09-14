"""SHAP explanations derived from the saved BhoomiGuard ML pipeline."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

# Keep Matplotlib's cache within the writable ML workspace when plots are requested.
try:
    from .config import (CLASSIFIER_MODEL_PATH, FEATURE_COLUMNS, FEATURE_DISPLAY_NAMES, RAW_DATA_PATH, REPORTS_DIR,
                         SHAP_BACKGROUND_ROWS, SHAP_GLOBAL_SAMPLE_ROWS)
    from .predict import predict_case
except ImportError:  # Allows direct execution/import from ml/src.
    from config import (CLASSIFIER_MODEL_PATH, FEATURE_COLUMNS, FEATURE_DISPLAY_NAMES, RAW_DATA_PATH, REPORTS_DIR,
                        SHAP_BACKGROUND_ROWS, SHAP_GLOBAL_SAMPLE_ROWS)
    from predict import predict_case

os.environ.setdefault("MPLCONFIGDIR", str(REPORTS_DIR / ".matplotlib"))

import joblib
import numpy as np
import pandas as pd
import shap


def _load_components(model_path: Path = CLASSIFIER_MODEL_PATH) -> tuple[Any, Any]:
    """Load the saved pipeline and expose its fitted preprocessor and classifier."""
    pipeline = joblib.load(model_path)
    if not hasattr(pipeline, "named_steps") or {"preprocessor", "classifier"} - set(pipeline.named_steps):
        raise ValueError("Expected a saved pipeline with 'preprocessor' and 'classifier' steps.")
    return pipeline.named_steps["preprocessor"], pipeline.named_steps["classifier"]


def _feature_frame(record: Mapping[str, Any]) -> pd.DataFrame:
    """Create the original-schema one-row input required by the stored preprocessor."""
    missing = set(FEATURE_COLUMNS).difference(record)
    if missing:
        raise ValueError(f"Record is missing required feature fields: {sorted(missing)}")
    return pd.DataFrame([{column: record[column] for column in FEATURE_COLUMNS}])


def _transformed_frame(features: pd.DataFrame, model_path: Path = CLASSIFIER_MODEL_PATH) -> tuple[pd.DataFrame, Any]:
    """Apply only the fitted preprocessor from the saved artifact, never a duplicate transform."""
    preprocessor, classifier = _load_components(model_path)
    transformed = preprocessor.transform(features)
    names = preprocessor.get_feature_names_out()
    return pd.DataFrame(transformed, columns=names, index=features.index), classifier


def _make_explainer(classifier: Any, reference: pd.DataFrame) -> shap.LinearExplainer:
    """Create the appropriate SHAP explainer for the persisted Logistic Regression model."""
    return shap.LinearExplainer(classifier, reference)


def _readable_feature(transformed_name: str) -> tuple[str, str | None, str | None]:
    """Translate a transformed feature while preserving one-hot categories as separate factors."""
    _, encoded = transformed_name.split("__", maxsplit=1)
    for categorical in ("project_type", "state", "district", "current_stage"):
        prefix = f"{categorical}_"
        if encoded.startswith(prefix):
            category = encoded[len(prefix):]
            return f"{FEATURE_DISPLAY_NAMES[categorical]} = {category}", categorical, category
    return FEATURE_DISPLAY_NAMES.get(encoded, encoded.replace("_", " ").title()), encoded, None


def explain_prediction(
    record: Mapping[str, Any], top_k: int = 5, model_path: Path = CLASSIFIER_MODEL_PATH,
    reference_data: pd.DataFrame | None = None, prediction: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return non-causal, per-feature SHAP contributions for one saved-model prediction.

    SHAP values are on the Logistic Regression decision-function (log-odds) scale. One-hot
    categorical contributions remain separate; they are not aggregated into a single variable.
    """
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    features = _feature_frame(record)
    transformed, classifier = _transformed_frame(features, model_path)
    if reference_data is None:
        reference_data = pd.read_csv(RAW_DATA_PATH)
    reference_features = reference_data.loc[:, list(FEATURE_COLUMNS)].head(SHAP_BACKGROUND_ROWS)
    reference_transformed, _ = _transformed_frame(reference_features, model_path)
    shap_result = _make_explainer(classifier, reference_transformed)(transformed)
    values = shap_result.values[0]
    ranked_indices = np.argsort(np.abs(values))[::-1][:top_k]
    factors: list[dict[str, Any]] = []
    for index in ranked_indices:
        transformed_name = transformed.columns[index]
        label, raw_column, category = _readable_feature(transformed_name)
        raw_value = record.get(raw_column) if raw_column else None
        item: dict[str, Any] = {
            "feature": label, "value": raw_value, "shap_value": round(float(values[index]), 6),
            "direction": "increases_risk" if values[index] > 0 else "reduces_risk",
            "transformed_feature": transformed_name,
        }
        if category is not None:
            item["encoded_value"] = int(transformed.iloc[0, index])
        factors.append(item)
    prediction = prediction or predict_case(record, model_path)
    return {
        "delay_probability": prediction["delay_probability"], "risk_score": prediction["risk_score"],
        "risk_category": prediction["risk_category"], "predicted_delay": prediction["predicted_delay"],
        "base_value": round(float(shap_result.base_values[0]), 6), "base_value_scale": "log_odds",
        "top_factors": factors,
    }


def get_global_feature_importance(
    data: pd.DataFrame | None = None, top_k: int | None = 20, model_path: Path = CLASSIFIER_MODEL_PATH,
) -> list[dict[str, Any]]:
    """Rank transformed features by mean absolute SHAP value on supplied prototype data."""
    if data is None:
        data = pd.read_csv(RAW_DATA_PATH)
    # A deterministic representative sample keeps global SHAP practical while still
    # deriving every reported importance from actual supplied prototype records.
    features = data.loc[:, list(FEATURE_COLUMNS)].head(SHAP_GLOBAL_SAMPLE_ROWS)
    transformed, classifier = _transformed_frame(features, model_path)
    values = _make_explainer(classifier, transformed)(transformed).values
    importances = np.abs(values).mean(axis=0)
    order = np.argsort(importances)[::-1]
    if top_k is not None:
        order = order[:top_k]
    return [
        {"feature": _readable_feature(transformed.columns[index])[0], "importance": round(float(importances[index]), 6),
         "transformed_feature": transformed.columns[index]}
        for index in order
    ]


def save_global_importance_plot(output_path: Path | None = None, top_k: int = 20) -> Path:
    """Save a SHAP mean-absolute-value bar plot for development and research."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path = output_path or REPORTS_DIR / "global_feature_importance.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    items = get_global_feature_importance(top_k=top_k)
    labels = [item["feature"] for item in items][::-1]
    values = [item["importance"] for item in items][::-1]
    figure, axis = plt.subplots(figsize=(10, max(4, len(items) * .35)))
    axis.barh(labels, values, color="#2d6a4f")
    axis.set_xlabel("Mean absolute SHAP value (log-odds)")
    axis.set_title("BhoomiGuard: Global model feature importance")
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)
    return output_path


def save_individual_explanation_plot(record: Mapping[str, Any], output_path: Path | None = None, top_k: int = 10) -> Path:
    """Save a development-oriented bar chart of one record's top SHAP contributions."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path = output_path or REPORTS_DIR / "individual_explanation.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    factors = explain_prediction(record, top_k=top_k)["top_factors"]
    labels = [factor["feature"] for factor in factors][::-1]
    values = [factor["shap_value"] for factor in factors][::-1]
    colors = ["#d1495b" if value > 0 else "#2d6a4f" for value in values]
    figure, axis = plt.subplots(figsize=(10, max(4, len(factors) * .45)))
    axis.barh(labels, values, color=colors)
    axis.axvline(0, color="black", linewidth=.8)
    axis.set_xlabel("SHAP contribution to delay prediction (log-odds)")
    axis.set_title("BhoomiGuard: Individual model explanation")
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)
    return output_path
