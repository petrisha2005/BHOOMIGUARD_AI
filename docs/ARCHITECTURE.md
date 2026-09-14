# Architecture

BhoomiGuard AI is an SIH26017 land-acquisition monitoring application. This repository contains the Role 2 platform implementation.

## Runtime components

- **Frontend:** React 19 and Vite provide the officer console. The frontend uses `frontend/src/services/apiClient.js` and `bhoomiApi.js` for every backend request. `VITE_API_BASE_URL` may override the local `/api` proxy at deployment time.
- **Backend:** FastAPI registers routers for authentication, projects, acquisition cases, predictions, recommendations, alerts, interventions, analytics, GIS, reports, and integration status.
- **Data layer:** SQLAlchemy 2.x models and Pydantic schemas access the existing Supabase PostgreSQL tables through `DATABASE_URL` and `psycopg`.
- **GIS:** The map page obtains persisted locations from `GET /gis/projects`, then renders them with MapLibre GL over OpenStreetMap tiles.
- **Reports:** FastAPI builds project PDFs with ReportLab from persisted records.
- **Authentication:** JWT/bcrypt code is present. Runtime protection depends on `AUTH_REQUIRED`; local development may intentionally disable it.

## Ownership boundary

Role 2 owns the application UI, FastAPI API, database application layer, GIS, reports, authentication code, documentation, deployment guidance, and testing structure.

Role 1 owns model training, model artifacts, SHAP, prediction/recommendation/alert intelligence, What-If logic, and the approved ML-service contract. The backend `ml_client.py` is a boundary only: it returns a clear unavailable error when `ML_SERVICE_URL` is not configured and does not synthesize a prediction. `ml_integration/client.py` and `ml_integration/contracts.py` remain intentionally empty hand-off stubs until Role 1 supplies the agreed implementation and contract.

## Data flow

```text
Officer console → FastAPI routers → SQLAlchemy → Supabase PostgreSQL
                       │
                       ├→ ReportLab PDF generation
                       ├→ GIS project-location response → MapLibre/OpenStreetMap
                       └→ Optional approved Role 1 ML service
```

No local database, ML model, fabricated prediction, or fabricated geographic record is included in this repository.
