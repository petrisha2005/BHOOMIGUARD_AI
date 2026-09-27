"""Focused tests for CSV import orchestration without changing ML behavior."""

import csv
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import projects as project_api
from app.schemas.project import ProjectImportRequest


def sample_rows() -> list[dict[str, str]]:
    root = Path(__file__).resolve().parents[2]
    with (root / "sample_data" / "bhoomiguard_project_import_sample.csv").open(newline="") as source:
        return list(csv.DictReader(source))[:2]


class FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.projects_by_code = {}
        self.predictions = {}
        self.rollbacks = 0

    def add(self, item) -> None:
        self.added.append(item)

    def commit(self) -> None:
        for project in self.added:
            if project.id is None:
                project.id = uuid4()
            self.projects_by_code[project.project_code.lower()] = project

    def refresh(self, _item) -> None:
        return None

    def rollback(self) -> None:
        self.rollbacks += 1


def configure_orchestration(monkeypatch: pytest.MonkeyPatch, db: FakeSession) -> None:
    monkeypatch.setattr(project_api, "_project_for_import_code", lambda code, _db: db.projects_by_code.get(code.lower()))
    monkeypatch.setattr(project_api, "_latest_prediction", lambda project_id, _db: db.predictions.get(project_id))
    monkeypatch.setattr(project_api, "_ml_record_counts", lambda project_id, _db: (0, 0) if project_id not in db.predictions else (2, 2))

    def persist(_db, project, _assessment):
        prediction = SimpleNamespace(
            risk_score=Decimal("10.00"),
            delay_probability=Decimal("0.1000"),
            risk_category="Low",
        )
        db.predictions[project.id] = prediction
        return prediction

    monkeypatch.setattr(project_api, "run_assessment", lambda project: {"project": project.id})
    monkeypatch.setattr(project_api, "persist_assessment", persist)


def test_batch_imports_and_analyses_each_valid_row(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeSession()
    configure_orchestration(monkeypatch, db)

    result = project_api.import_and_analyze_projects(ProjectImportRequest(rows=sample_rows()), db)

    assert result.total_projects == 2
    assert result.processed_projects == 2
    assert result.failed_projects == 0
    assert [item.status for item in result.results] == ["Analysed", "Analysed"]
    assert all(item.risk_category == "Low" for item in result.results)


def test_batch_rejects_invalid_rows_before_ml_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeSession()
    configure_orchestration(monkeypatch, db)
    invalid = sample_rows()
    invalid[0]["historical_delay_rate"] = "25"
    called = False

    def should_not_run(_project):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(project_api, "run_assessment", should_not_run)
    with pytest.raises(HTTPException) as error:
        project_api.import_and_analyze_projects(ProjectImportRequest(rows=invalid), db)

    assert error.value.status_code == 422
    assert called is False
    assert db.added == []


def test_batch_reports_one_project_failure_without_losing_other_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeSession()
    configure_orchestration(monkeypatch, db)
    rows = sample_rows()

    def assessment(project):
        if project.project_code == rows[1]["project_code"]:
            raise RuntimeError("simulated ML failure")
        return {}

    monkeypatch.setattr(project_api, "run_assessment", assessment)
    result = project_api.import_and_analyze_projects(ProjectImportRequest(rows=rows), db)

    assert result.processed_projects == 1
    assert result.failed_projects == 1
    assert [item.status for item in result.results] == ["Analysed", "Failed"]
    assert result.results[1].error == "ML analysis could not be completed for this project."
    assert len(db.projects_by_code) == 2


def test_repeated_batch_reuses_existing_analysed_projects(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeSession()
    configure_orchestration(monkeypatch, db)
    first = project_api.import_and_analyze_projects(ProjectImportRequest(rows=sample_rows()), db)
    second = project_api.import_and_analyze_projects(ProjectImportRequest(rows=sample_rows()), db)

    assert first.processed_projects == 2
    assert [item.status for item in second.results] == ["Already analysed", "Already analysed"]
    assert len(db.projects_by_code) == 2
    assert len(db.predictions) == 2
