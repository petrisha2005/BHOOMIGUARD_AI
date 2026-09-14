from pathlib import Path

from src.config import FEATURE_COLUMNS, STAGE_NAMES, TARGET_COLUMNS
from src.data_generator import generate_dataset, validate_dataset


def test_dataset_generation_is_reproducible_and_has_expected_schema() -> None:
    data = generate_dataset(rows=100, seed=7)
    assert data.shape[0] == 100
    assert set(("project_id",) + FEATURE_COLUMNS + TARGET_COLUMNS) == set(data.columns)
    assert data["project_id"].is_unique
    assert generate_dataset(rows=100, seed=7).equals(data)


def test_data_ranges_and_targets_are_valid() -> None:
    data = generate_dataset(rows=250)
    assert data["current_stage"].isin(STAGE_NAMES).all()
    assert data["delay_flag"].isin([0, 1]).all()
    assert (data["actual_delay_days"] >= 0).all()
    assert (data.loc[data.delay_flag.eq(0), "actual_delay_days"] == 0).all()
    assert (data.loc[data.delay_flag.eq(1), "actual_delay_days"] > 0).all()
    for column in (name for name in data if name.endswith("_pct")):
        assert data[column].between(0, 100).all()
    summary = validate_dataset(data)
    assert all(summary[key] == 0 for key in (
        "missing_values", "duplicate_project_ids", "invalid_percentages", "negative_values",
        "invalid_categories", "impossible_combinations", "suspicious_perfect_correlations",
    ))

