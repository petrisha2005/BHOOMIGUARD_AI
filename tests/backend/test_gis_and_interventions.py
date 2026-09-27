"""Focused regression coverage for persisted GIS and intervention workflows."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.api import gis, interventions
from app.schemas.intervention import InterventionCreate, InterventionUpdate


class ScalarRows:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class GisSession:
    def __init__(self, projects):
        self.projects = projects

    def scalars(self, _statement):
        return ScalarRows(self.projects)


class InterventionSession:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, item):
        self.added.append(item)

    def commit(self):
        self.commits += 1

    def refresh(self, _item):
        return None


def test_gis_response_uses_persisted_coordinates_and_latest_prediction(monkeypatch):
    project_id = uuid4()
    project = SimpleNamespace(
        id=project_id,
        project_code="BG-GIS-001",
        name="Synthetic mapped project",
        district="Pune",
        current_stage="Possession",
        latitude=Decimal("18.5204300"),
        longitude=Decimal("73.8567440"),
        corridor_geometry=None,
        status="Active",
    )
    latest_prediction = SimpleNamespace(
        risk_category="High", delay_probability=Decimal("0.6281")
    )
    monkeypatch.setattr(gis, "latest_predictions_by_project", lambda _db: {project_id: latest_prediction})

    response = gis.list_project_locations(GisSession([project]))

    assert len(response) == 1
    assert response[0].id == project_id
    assert response[0].latitude == Decimal("18.5204300")
    assert response[0].longitude == Decimal("73.8567440")
    assert response[0].risk_category == "High"


def test_intervention_is_persisted_officer_action_without_ml_reassessment(monkeypatch):
    project_id = uuid4()
    db = InterventionSession()
    monkeypatch.setattr(interventions, "get_project_or_404", lambda _project_id, _db: object())

    item = interventions.create_intervention(
        InterventionCreate(
            project_id=project_id,
            intervention_type="Document review",
            action="Assign a records review and confirm missing documents.",
            owner_role="Documentation Officer",
            status="In Progress",
            due_date=date(2026, 10, 1),
            notes="Synthetic demonstration intervention.",
        ),
        db,
    )

    assert db.added == [item]
    assert db.commits == 1
    assert item.project_id == project_id
    assert item.status == "In Progress"
    assert "reassess" not in interventions.__dict__


def test_intervention_update_changes_only_intervention_fields(monkeypatch):
    item = SimpleNamespace(id=uuid4(), status="Pending", notes=None, updated_at=None)
    db = InterventionSession()
    monkeypatch.setattr(interventions, "get_intervention_or_404", lambda _id, _db: item)

    updated = interventions.update_intervention(
        item.id, InterventionUpdate(status="Completed", notes="Officer recorded completion."), db
    )

    assert updated.status == "Completed"
    assert updated.notes == "Officer recorded completion."
    assert db.commits == 1
