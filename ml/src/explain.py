"""SHAP explanations derived from the saved BhoomiGuard ML pipeline."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

# Keep Matplotlib's cache within the writable ML workspace when plots are requested.
try:
    from .config import (CATEGORICAL_COLUMNS, CLASSIFIER_MODEL_PATH, FEATURE_COLUMNS, FEATURE_DISPLAY_NAMES,
                         RAW_DATA_PATH, REPORTS_DIR, SHAP_BACKGROUND_ROWS, SHAP_GLOBAL_SAMPLE_ROWS)
    from .predict import predict_case
except ImportError:  # Allows direct execution/import from ml/src.
    from config import (CATEGORICAL_COLUMNS, CLASSIFIER_MODEL_PATH, FEATURE_COLUMNS, FEATURE_DISPLAY_NAMES,
                        RAW_DATA_PATH, REPORTS_DIR, SHAP_BACKGROUND_ROWS, SHAP_GLOBAL_SAMPLE_ROWS)
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
    for categorical in CATEGORICAL_COLUMNS:
        prefix = f"{categorical}_"
        if encoded.startswith(prefix):
            category = encoded[len(prefix):]
            return f"{FEATURE_DISPLAY_NAMES[categorical]} = {category}", categorical, category
    return FEATURE_DISPLAY_NAMES.get(encoded, encoded.replace("_", " ").title()), encoded, None


def _feature_sources(preprocessor: Any) -> dict[str, str]:
    """Map every fitted transformed column to its original schema feature.

    The mapping is derived from the fitted ColumnTransformer's configured input columns
    and generated output names, so it stays aligned with the saved preprocessing artifact.
    """
    sources: dict[str, str] = {}
    for transformer_name, _, columns in preprocessor.transformers_:
        if transformer_name == "remainder" or not columns:
            continue
        prefix = f"{transformer_name}__"
        for transformed_name in preprocessor.get_feature_names_out():
            if not transformed_name.startswith(prefix):
                continue
            encoded = transformed_name.removeprefix(prefix)
            if encoded in columns:
                sources[transformed_name] = encoded
                continue
            # OneHotEncoder output is source-column plus category. Longest match
            # handles source names that themselves contain underscores.
            matches = [str(column) for column in columns if encoded.startswith(f"{column}_")]
            if matches:
                sources[transformed_name] = max(matches, key=len)
    return sources


def _audit_factor(
    transformed_name: str, value: float, transformed_value: float, record: Mapping[str, Any], source_feature: str,
) -> dict[str, Any]:
    """Build one mathematically direct transformed-feature SHAP evidence item."""
    label, raw_column, category = _readable_feature(transformed_name)
    raw_value = record.get(raw_column) if raw_column else None
    item: dict[str, Any] = {
        "feature": label, "value": raw_value, "shap_value": round(float(value), 6),
        "direction": "increases_risk" if value > 0 else "reduces_risk",
        "transformed_feature": transformed_name, "source_feature": source_feature,
        "transformed_value": round(float(transformed_value), 6),
    }
    if category is not None:
        item["encoded_value"] = int(transformed_value)
    return item


def _officer_facing_factors(audit_factors: list[dict[str, Any]], record: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Aggregate audit SHAP evidence by original feature for officer presentation.

    Categorical one-hot contributions are summed by their source feature. The nested
    ``transformed_contributions`` retain the exact individual values for auditability.
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    for factor in audit_factors:
        grouped.setdefault(str(factor["source_feature"]), []).append(factor)
    combined: list[dict[str, Any]] = []
    for source_feature, factors in grouped.items():
        contribution = sum(float(factor["shap_value"]) for factor in factors)
        if contribution == 0:
            continue
        item: dict[str, Any] = {
            "feature": source_feature, "label": FEATURE_DISPLAY_NAMES.get(source_feature, source_feature.replace("_", " ").title()),
            "value": record.get(source_feature), "shap_value": round(contribution, 6),
            "direction": "increases_risk" if contribution > 0 else "reduces_risk",
            "transformed_contributions": factors,
        }
        if source_feature in CATEGORICAL_COLUMNS:
            item["active_category"] = record.get(source_feature)
        combined.append(item)
    increasing = sorted((item for item in combined if item["shap_value"] > 0),
                        key=lambda item: (-abs(float(item["shap_value"])), item["feature"]))
    reducing = sorted((item for item in combined if item["shap_value"] < 0),
                      key=lambda item: (-abs(float(item["shap_value"])), item["feature"]))
    for items in (increasing, reducing):
        for rank, item in enumerate(items, start=1):
            item["rank"] = rank
    return {"risk_increasing": increasing, "risk_reducing": reducing}


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
    sources = _feature_sources(_load_components(model_path)[0])
    audit_factors = [
        _audit_factor(name, values[index], float(transformed.iloc[0, index]), record, sources.get(name, name))
        for index, name in enumerate(transformed.columns)
    ]
    ranked_indices = np.argsort(np.abs(values))[::-1][:top_k]
    # ``top_factors`` remains the existing transformed-feature contract consumed by
    # recommendations. Officer presentation is provided separately below.
    factors = [audit_factors[index] for index in ranked_indices]
    prediction = prediction or predict_case(record, model_path)
    return {
        "delay_probability": prediction["delay_probability"], "risk_score": prediction["risk_score"],
        "risk_category": prediction["risk_category"], "predicted_delay": prediction["predicted_delay"],
        "base_value": round(float(shap_result.base_values[0]), 6), "base_value_scale": "log_odds",
        "top_factors": factors, "audit_factors": audit_factors,
        "officer_facing_factors": _officer_facing_factors(audit_factors, record),
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
