"""Focused coverage for the prototype parcel GIS backend foundation."""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api import cases, gis
from app.core import security
from app.schemas.land_parcel import LandParcelResponse


def demo_geometry() -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[[73.85, 18.51], [73.86, 18.51], [73.86, 18.52], [73.85, 18.52], [73.85, 18.51]]],
    }


def demo_parcel(project_id=None, parcel_id=None):
    return SimpleNamespace(
        id=parcel_id or uuid4(), project_id=project_id or uuid4(), parcel_id="BG-DEMO-001-P01",
        ownership_type="PRIVATE", acquisition_status="IN_PROGRESS", area_acres=Decimal("1.20"),
        geometry=demo_geometry(), acquisition_cases=[], created_at=datetime(2026, 9, 26, 10, 0),
        updated_at=datetime(2026, 9, 26, 10, 0),
    )


class ScalarRows:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class ParcelSession:
    def __init__(self, project, parcels, parcel=None):
        self.project = project
        self.parcels = parcels
        self.parcel = parcel

    def get(self, model, value):
        if model.__name__ == "Project":
            return self.project if self.project and self.project.id == value else None
        if model.__name__ == "LandParcel":
            return self.parcel if self.parcel and self.parcel.id == value else None
        return None

    def scalars(self, _statement):
        return ScalarRows(self.parcels)


def test_authenticated_parcel_listing_returns_project_parcels_and_project_risk(monkeypatch):
    project = SimpleNamespace(id=uuid4())
    parcel = demo_parcel(project.id)
    prediction = SimpleNamespace(risk_score=Decimal("62.81"), delay_probability=Decimal("0.6281"), risk_category="High")
    monkeypatch.setattr(gis, "latest_predictions_by_project", lambda _db: {project.id: prediction})

    response = gis.list_project_parcels(project.id, ParcelSession(project, [parcel]))

    assert len(response) == 1
    assert response[0].project_id == project.id
    assert response[0].ownership_type == "PRIVATE"
    assert response[0].latest_project_risk.risk_category == "High"


def test_project_can_return_multiple_synthetic_parcels(monkeypatch):
    project = SimpleNamespace(id=uuid4())
    first, second = demo_parcel(project.id), demo_parcel(project.id)
    second.id = uuid4()
    second.parcel_id = "BG-DEMO-001-P02"
    second.ownership_type = "GOVERNMENT"
    second.acquisition_status = "ACQUIRED"
    monkeypatch.setattr(gis, "latest_predictions_by_project", lambda _db: {})

    response = gis.list_project_parcels(project.id, ParcelSession(project, [first, second]))

    assert [item.parcel_id for item in response] == ["BG-DEMO-001-P01", "BG-DEMO-001-P02"]
    assert {item.ownership_type for item in response} == {"PRIVATE", "GOVERNMENT"}


def test_parcel_detail_returns_linked_acquisition_case(monkeypatch):
    project_id, case_id, parcel_id = uuid4(), uuid4(), uuid4()
    parcel = demo_parcel(project_id, parcel_id)
    parcel.acquisition_cases = [SimpleNamespace(id=case_id)]
    monkeypatch.setattr(gis, "latest_predictions_by_project", lambda _db: {})

    response = gis.get_parcel(parcel_id, ParcelSession(None, [], parcel))

    assert response.id == parcel_id
    assert response.acquisition_case_id == case_id
    assert response.latest_project_risk is None


def test_parcel_listing_rejects_unknown_project(monkeypatch):
    monkeypatch.setattr(gis, "latest_predictions_by_project", lambda _db: {})
    with pytest.raises(HTTPException, match="Project not found") as error:
        gis.list_project_parcels(uuid4(), ParcelSession(None, []))
    assert error.value.status_code == 404


def test_parcel_geometry_requires_closed_polygon_and_controlled_values():
    valid = LandParcelResponse(
        id=uuid4(), project_id=uuid4(), parcel_id="SYNTHETIC-P01", ownership_type="GOVERNMENT",
        acquisition_status="ACQUIRED", area_acres=Decimal("0.50"), geometry=demo_geometry(),
        created_at=datetime.now(), updated_at=datetime.now(),
    )
    assert valid.geometry["type"] == "Polygon"
    with pytest.raises(ValidationError):
        LandParcelResponse(
            id=uuid4(), project_id=uuid4(), parcel_id="BAD-P01", ownership_type="PRIVATE",
            acquisition_status="ON_HOLD", area_acres=Decimal("1"),
            geometry={"type": "Point", "coordinates": [73.85, 18.51]}, created_at=datetime.now(), updated_at=datetime.now(),
        )
    with pytest.raises(ValidationError):
        LandParcelResponse(
            id=uuid4(), project_id=uuid4(), parcel_id="BAD-P02", ownership_type="PRIVATE",
            acquisition_status="IN_PROGRESS", area_acres=Decimal("1"),
            geometry={"type": "Polygon", "coordinates": [[[73.85, 18.51], [73.86, 18.51], [73.86, 18.52], [73.85, 18.52]]]},
            created_at=datetime.now(), updated_at=datetime.now(),
        )
    with pytest.raises(ValidationError):
        LandParcelResponse(
            id=uuid4(), project_id=uuid4(), parcel_id="BAD-P03", ownership_type="COMMUNITY",
            acquisition_status="UNKNOWN", area_acres=Decimal("1"), geometry=demo_geometry(),
            created_at=datetime.now(), updated_at=datetime.now(),
        )


def test_case_rejects_parcel_from_a_different_project():
    project_id = uuid4()
    other_parcel = SimpleNamespace(project_id=uuid4())

    class CaseSession:
        def get(self, model, _value):
            return other_parcel if model.__name__ == "LandParcel" else None

    with pytest.raises(HTTPException) as error:
        cases.validate_case_parcel(project_id, uuid4(), CaseSession())
    assert error.value.status_code == 422


def test_parcel_access_without_bearer_token_is_rejected(monkeypatch):
    monkeypatch.setattr(security.settings, "auth_required", True)
    with pytest.raises(HTTPException) as error:
        security.get_current_user(None, object())
    assert error.value.status_code == 401
