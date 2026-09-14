from copy import deepcopy

import pandas as pd
import pytest

from src.config import FEATURE_COLUMNS
from src.what_if import simulate_scenario, validate_scenario_changes


def _record() -> dict:
    data = pd.read_csv("ml/data/raw/land_acquisition_cases.csv")
    return data.loc[0, list(FEATURE_COLUMNS)].to_dict()


def test_single_and_multiple_feature_changes_use_baseline_and_scenario_predictions() -> None:
    record = _record()
    single = simulate_scenario(record, {"pending_approvals": 0})
    multi = simulate_scenario(record, {
        "pending_approvals": 0, "compensation_completion_pct": 95, "documentation_completion_pct": 95,
    })
    assert single["changes"]["pending_approvals"]["after"] == 0
    assert set(multi["changes"]) == {"pending_approvals", "compensation_completion_pct", "documentation_completion_pct"}
    assert {"delay_probability", "risk_score", "risk_category", "predicted_delay"}.issubset(single["baseline"])
    assert multi["impact"]["delay_days_change"] is None
    assert multi["impact"]["delay_days_available"] is False


def test_simulation_never_mutates_original_input_or_baseline_snapshot() -> None:
    record = _record()
    before = deepcopy(record)
    result = simulate_scenario(record, {"pending_approvals": 0})
    assert record == before
    assert result["baseline_input"] == before
    assert result["scenario_input"]["pending_approvals"] == 0


def test_risk_comparison_transition_and_interpretation_are_consistent() -> None:
    record = _record()
    result = simulate_scenario(record, {"pending_approvals": record["pending_approvals"]})
    assert result["impact"]["risk_score_change_percentage_points"] == 0
    assert result["impact"]["risk_category_transition"] == "No meaningful improvement"
    assert "minimal change" in result["interpretation"]


def test_increased_risk_scenario_is_detected() -> None:
    record = _record()
    result = simulate_scenario(record, {"legal_disputes": record["legal_disputes"] + 10})
    assert result["impact"]["risk_increased"] is True
    assert "increases predicted delay risk" in result["interpretation"]


def test_risk_category_transition_is_reported() -> None:
    record = _record()
    result = simulate_scenario(record, {
        "legal_disputes": 20, "ownership_conflicts": 45, "pending_court_cases": 60,
        "pending_approvals": 30, "approval_delay_days": 500, "historical_delay_rate": 1,
        "previous_stage_delay_days": 600,
    })
    assert result["impact"]["risk_category_transition"] == "High → Critical"


@pytest.mark.parametrize("changes", [
    {"unknown_factor": 1}, {"pending_approvals": "none"}, {"compensation_completion_pct": 101},
    {"pending_approvals": -1}, {"state": "Invalid State"}, {"district": "Invalid District"},
])
def test_invalid_scenario_changes_are_rejected(changes: dict) -> None:
    with pytest.raises(ValueError):
        validate_scenario_changes(_record(), changes)


def test_invalid_state_district_combination_is_rejected() -> None:
    with pytest.raises(ValueError, match="not valid for state"):
        simulate_scenario(_record(), {"state": "Karnataka", "district": "Chennai"})


def test_same_input_produces_deterministic_output() -> None:
    record = _record()
    changes = {"pending_approvals": 0, "documentation_completion_pct": 95}
    assert simulate_scenario(record, changes) == simulate_scenario(record, changes)
