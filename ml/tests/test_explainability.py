import importlib

import pandas as pd

from src.config import FEATURE_COLUMNS, TARGET_COLUMNS
from src.explain import explain_prediction, get_global_feature_importance
from src.predict import predict_case


def _sample_record() -> dict:
    data = pd.read_csv("ml/data/raw/land_acquisition_cases.csv")
    return data.loc[0, list(FEATURE_COLUMNS)].to_dict()


def test_shap_module_imports() -> None:
    assert importlib.import_module("src.explain")


def test_single_explanation_has_expected_contract() -> None:
    result = explain_prediction(_sample_record(), top_k=5)
    assert 0 <= result["delay_probability"] <= 1
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_category"] in {"Low", "Moderate", "High", "Critical"}
    assert 1 <= len(result["top_factors"]) <= 5
    for factor in result["top_factors"]:
        assert {"feature", "value", "shap_value", "direction"}.issubset(factor)
        assert factor["direction"] in {"increases_risk", "reduces_risk"}
        assert (factor["shap_value"] > 0) == (factor["direction"] == "increases_risk")


def test_explanation_matches_the_saved_prediction_pipeline() -> None:
    record = _sample_record()
    prediction = predict_case(record)
    explanation = explain_prediction(record, top_k=3)
    assert abs(prediction["delay_probability"] - explanation["delay_probability"]) < 1e-4
    assert prediction["risk_score"] == explanation["risk_score"]
    assert prediction["risk_category"] == explanation["risk_category"]


def test_global_importance_is_ranked_and_excludes_targets() -> None:
    data = pd.read_csv("ml/data/raw/land_acquisition_cases.csv").head(100)
    importance = get_global_feature_importance(data, top_k=8)
    assert importance
    assert all(item["importance"] >= 0 for item in importance)
    assert [item["importance"] for item in importance] == sorted(
        (item["importance"] for item in importance), reverse=True
    )
    assert not any(target in item["transformed_feature"] for item in importance for target in TARGET_COLUMNS)
