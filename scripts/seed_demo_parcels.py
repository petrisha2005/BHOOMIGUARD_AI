"""Seed clearly labelled synthetic parcel polygons for an existing demo project.

Usage: backend/.venv/bin/python scripts/seed_demo_parcels.py
The command is idempotent for BG-DEMO-001 and never fetches cadastral data.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.db.session import SessionLocal
from app.models import AcquisitionCase, LandParcel, Project


PROJECT_CODE = "BG-DEMO-001"
DEMO_CASE_NUMBER = "DEMO-BG-001-P01"


def polygon(longitude: float, latitude: float, offset: float) -> dict[str, object]:
    """Return a small closed synthetic demo polygon around the project point."""

    ring = [
        [round(longitude - offset, 7), round(latitude - offset, 7)],
        [round(longitude + offset, 7), round(latitude - offset, 7)],
        [round(longitude + offset, 7), round(latitude + offset, 7)],
        [round(longitude - offset, 7), round(latitude + offset, 7)],
    ]
    ring.append(ring[0])
    return {"type": "Polygon", "coordinates": [ring]}


def corridor(longitude: float, latitude: float) -> dict[str, object]:
    """Return a deterministic synthetic highway-style visual corridor, not a legal boundary."""

    return {
        "type": "LineString",
        "coordinates": [
            [round(longitude - 0.010, 7), round(latitude - 0.007, 7)],
            [round(longitude - 0.003, 7), round(latitude - 0.002, 7)],
            [round(longitude + 0.003, 7), round(latitude + 0.002, 7)],
            [round(longitude + 0.010, 7), round(latitude + 0.007, 7)],
        ],
    }


def main() -> None:
    db = SessionLocal()
    try:
        project = db.scalar(select(Project).where(Project.project_code == PROJECT_CODE))
        if project is None:
            raise SystemExit(f"No {PROJECT_CODE} project exists. Import the synthetic demo CSV first.")
        if project.latitude is None or project.longitude is None:
            raise SystemExit(f"{PROJECT_CODE} needs latitude and longitude before synthetic parcels can be seeded.")
        if project.corridor_geometry is None:
            project.corridor_geometry = corridor(float(project.longitude), float(project.latitude))
        parcels = db.scalars(select(LandParcel).where(LandParcel.project_id == project.id)).all()
        if not parcels:
            longitude, latitude = float(project.longitude), float(project.latitude)
            templates = [
                ("BG-DEMO-001-P01", "PRIVATE", "IN_PROGRESS", "1.20", -0.006, -0.004),
                ("BG-DEMO-001-P02", "GOVERNMENT", "ACQUIRED", "0.85", -0.002, -0.004),
                ("BG-DEMO-001-P03", "PRIVATE", "DISPUTED", "1.45", 0.002, -0.004),
                ("BG-DEMO-001-P04", "PRIVATE", "NOT_STARTED", "0.95", -0.006, 0.002),
                ("BG-DEMO-001-P05", "GOVERNMENT", "ACQUIRED", "1.10", -0.002, 0.002),
                ("BG-DEMO-001-P06", "PRIVATE", "ON_HOLD", "1.35", 0.002, 0.002),
            ]
            parcels = [
                LandParcel(
                    project_id=project.id,
                    parcel_id=parcel_id,
                    ownership_type=ownership,
                    acquisition_status=acquisition_status,
                    area_acres=Decimal(area_acres),
                    geometry=polygon(longitude + longitude_offset, latitude + latitude_offset, 0.0012),
                )
                for parcel_id, ownership, acquisition_status, area_acres, longitude_offset, latitude_offset in templates
            ]
            db.add_all(parcels)
            db.flush()
        available_cases = db.scalars(
            select(AcquisitionCase).where(
                AcquisitionCase.project_id == project.id, AcquisitionCase.parcel_id.is_(None)
            ).order_by(AcquisitionCase.created_at)
        ).all()
        for case, parcel in zip(available_cases, parcels, strict=False):
            case.parcel_id = parcel.id
        first_parcel = next(parcel for parcel in parcels if parcel.parcel_id == "BG-DEMO-001-P01")
        demo_case = db.scalar(select(AcquisitionCase).where(AcquisitionCase.case_number == DEMO_CASE_NUMBER))
        if demo_case is None:
            db.add(AcquisitionCase(
                project_id=project.id,
                parcel_id=first_parcel.id,
                case_number=DEMO_CASE_NUMBER,
                village="Synthetic demonstration village",
                current_stage="Possession",
                case_status="Open",
                compensation_status="In Progress",
                dispute_status="No dispute recorded",
                documentation_status="Complete",
                days_pending=5,
            ))
        db.commit()
        print(f"Ensured {len(parcels)} SYNTHETIC/DEMO parcel polygons and one synthetic acquisition case for {PROJECT_CODE}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
