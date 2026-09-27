"""Focused coverage for the synthetic project corridor GIS layer."""

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api import gis
from app.schemas.analytics import MapProjectResponse


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


def demo_corridor():
    return {
        "type": "LineString",
        "coordinates": [[73.8467, 18.5134], [73.8537, 18.5184], [73.8637, 18.5274]],
    }


def test_project_map_response_includes_valid_synthetic_corridor(monkeypatch):
    project_id = uuid4()
    project = SimpleNamespace(
        id=project_id,
        project_code="BG-DEMO-001",
        name="Synthetic corridor project",
        district="Pune",
        current_stage="Possession",
        latitude=Decimal("18.5204"),
        longitude=Decimal("73.8567"),
        status="Active",
        corridor_geometry=demo_corridor(),
    )
    monkeypatch.setattr(gis, "latest_predictions_by_project", lambda _db: {})

    response = gis.list_project_locations(GisSession([project]))

    assert response[0].corridor_geometry == demo_corridor()
    assert response[0].corridor_geometry["type"] == "LineString"


@pytest.mark.parametrize("geometry", [
    {"type": "Polygon", "coordinates": []},
    {"type": "LineString", "coordinates": [[73.8, 18.5]]},
    {"type": "LineString", "coordinates": [[181, 18.5], [73.8, 18.6]]},
])
def test_project_map_response_rejects_invalid_corridor_geometry(geometry):
    with pytest.raises(ValueError):
        MapProjectResponse(
            id=uuid4(), project_code="BG-DEMO-001", name="Demo", district=None,
            current_stage=None, latitude=Decimal("18.5"), longitude=Decimal("73.8"),
            status="Active", risk_category=None, delay_probability=None,
            corridor_geometry=geometry,
        )
