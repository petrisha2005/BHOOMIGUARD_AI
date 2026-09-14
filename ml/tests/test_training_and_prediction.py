import json

import joblib

from src.config import FEATURE_COLUMNS, TARGET_COLUMNS
from src.data_generator import generate_dataset
from src.predict import predict_case, risk_from_probability
from src.train import train_and_save


def test_training_creates_loadable_artifact_without_target_leakage(tmp_path) -> None:
    dataset_path = tmp_path / "cases.csv"
    model_path = tmp_path / "delay_classifier.joblib"
    metadata_path = tmp_path / "model_metadata.json"
    generate_dataset(rows=300).to_csv(dataset_path, index=False)
    _, metadata = train_and_save(dataset_path, model_path, metadata_path)
    assert model_path.exists() and metadata_path.exists()
    assert metadata["model_name"] in {"Logistic Regression", "Random Forest", "XGBoost"}
    assert not set(TARGET_COLUMNS).intersection(metadata["feature_names"])
    assert "project_id" not in metadata["feature_names"]
    loaded = joblib.load(model_path)
    assert hasattr(loaded, "predict_proba")
    assert json.loads(metadata_path.read_text())["target"] == "delay_flag"


def test_saved_pipeline_returns_valid_prediction() -> None:
    data = generate_dataset(rows=5)
    result = predict_case(data.loc[0, list(FEATURE_COLUMNS)].to_dict())
    assert 0 <= result["delay_probability"] <= 1
    assert 0 <= result["no_delay_probability"] <= 1
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_category"] in {"Low", "Moderate", "High", "Critical"}
    assert isinstance(result["predicted_delay"], bool)


def test_risk_categories_use_centralized_boundaries() -> None:
    assert risk_from_probability(.00) == (0.0, "Low")
    assert risk_from_probability(.25) == (25.0, "Moderate")
    assert risk_from_probability(.50) == (50.0, "High")
    assert risk_from_probability(1.00) == (100.0, "Critical")
