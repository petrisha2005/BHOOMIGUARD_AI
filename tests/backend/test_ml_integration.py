"""Contract tests for the application-to-ML adapter using the saved ML artifact."""

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pandas as pd
import pytest
from fastapi import HTTPException

from app.services.ml_integration import FEATURE_COLUMNS, project_to_ml_input, run_assessment, run_what_if


def project_from_sample() -> SimpleNamespace:
    root = Path(__file__).resolve().parents[2]
    row = pd.read_csv(root / "ml/data/raw/land_acquisition_cases.csv").iloc[0].to_dict()
    return SimpleNamespace(id=uuid4(), **{field: row[field] for field in FEATURE_COLUMNS})


def test_adapter_runs_existing_pipeline_and_preserves_structured_outputs() -> None:
    assessment = run_assessment(project_from_sample())

    assert assessment["prediction"]["risk_score"] >= 0
    assert "officer_facing_factors" in assessment["explanation"]
    assert "monitoring_signals" in assessment["recommendations"]
    assert isinstance(assessment["alerts"], list)


def test_what_if_remains_a_separate_non_duration_operation() -> None:
    project = project_from_sample()
    baseline = project_to_ml_input(project)
    result = run_what_if(project, {"compensation_completion_pct": baseline["compensation_completion_pct"]})

    assert result["impact"]["delay_days_change"] is None
    assert result["impact"]["delay_days_available"] is False


def test_adapter_rejects_incomplete_ml_input() -> None:
    project = project_from_sample()
    project.pending_approvals = None

    with pytest.raises(HTTPException) as error:
        project_to_ml_input(project)
    assert error.value.status_code == 422
