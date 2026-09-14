import importlib

import pandas as pd

from src.config import FEATURE_COLUMNS, TARGET_COLUMNS
from src.explain import _officer_facing_factors, explain_prediction, get_global_feature_importance
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


def test_officer_facing_explanation_aggregates_categorical_audit_evidence() -> None:
    record = _sample_record()
    result = explain_prediction(record, top_k=5)
    officer = result["officer_facing_factors"]
    district = next(
        item for group in officer.values() for item in group if item["feature"] == "district"
    )
    evidence = [item for item in result["audit_factors"] if item["source_feature"] == "district"]
    assert district["label"] == "District"
    assert district["active_category"] == record["district"]
    assert district["value"] == record["district"]
    assert len(evidence) > 1  # Active and inactive one-hot indicators remain auditable.
    assert district["transformed_contributions"] == evidence
    assert district["shap_value"] == round(sum(item["shap_value"] for item in evidence), 6)


def test_officer_factors_group_direction_and_ranking_are_deterministic() -> None:
    factors = [
        {"source_feature": "legal_disputes", "shap_value": 1.2, "transformed_feature": "numeric__legal_disputes"},
        {"source_feature": "district", "shap_value": .4, "transformed_feature": "categorical__district_Chennai"},
        {"source_feature": "district", "shap_value": -.1, "transformed_feature": "categorical__district_Salem"},
        {"source_feature": "missing_documents", "shap_value": -.8, "transformed_feature": "numeric__missing_documents"},
    ]
    result = _officer_facing_factors(factors, {"district": "Chennai"})
    assert [item["feature"] for item in result["risk_increasing"]] == ["legal_disputes", "district"]
    assert [item["rank"] for item in result["risk_increasing"]] == [1, 2]
    assert result["risk_reducing"][0]["feature"] == "missing_documents"
    assert result["risk_reducing"][0]["direction"] == "reduces_risk"


def test_global_importance_is_ranked_and_excludes_targets() -> None:
    data = pd.read_csv("ml/data/raw/land_acquisition_cases.csv").head(100)
    importance = get_global_feature_importance(data, top_k=8)
    assert importance
    assert all(item["importance"] >= 0 for item in importance)
    assert [item["importance"] for item in importance] == sorted(
        (item["importance"] for item in importance), reverse=True
    )
    assert not any(target in item["transformed_feature"] for item in importance for target in TARGET_COLUMNS)
