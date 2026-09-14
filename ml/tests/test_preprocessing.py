import pandas as pd

from src.config import FEATURE_COLUMNS, TARGET_COLUMNS
from src.data_generator import generate_dataset
from src.preprocessing import build_preprocessor, get_feature_frame, get_targets


def test_preprocessor_handles_missing_values_and_unseen_categories() -> None:
    data = generate_dataset(rows=60)
    features = get_feature_frame(data)
    features.loc[0, "land_area_acres"] = None
    features.loc[1, "state"] = None
    transformer = build_preprocessor()
    transformed = transformer.fit_transform(features)
    assert transformed.shape[0] == 60
    assert transformed.shape[1] > len(FEATURE_COLUMNS)
    unseen = features.iloc[:1].copy()
    unseen["state"] = "Unseen State"
    assert transformer.transform(unseen).shape[0] == 1


def test_targets_are_not_features() -> None:
    data = generate_dataset(rows=10)
    features = get_feature_frame(data)
    targets = get_targets(data)
    assert not set(TARGET_COLUMNS).intersection(features.columns)
    assert list(targets.columns) == list(TARGET_COLUMNS)
    assert "project_id" not in features.columns

