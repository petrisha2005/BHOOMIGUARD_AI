# API inventory

The FastAPI application exposes the following current routes. With `AUTH_REQUIRED=true`, all routes except `POST /auth/login` and `GET /auth/status` require a bearer token. FastAPI exposes the generated OpenAPI document at `/openapi.json` while the service is running.

## Authentication

- `GET /auth/status`
- `POST /auth/login`
- `GET /auth/me`

## Projects

- `GET /projects`
- `POST /projects`
- `POST /projects/import/preview`
- `POST /projects/import`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/detail`
- `PUT /projects/{project_id}`
- `DELETE /projects/{project_id}`

## Acquisition cases

- `GET /cases`
- `POST /cases`
- `GET /cases/{case_id}`
- `PUT /cases/{case_id}`
- `DELETE /cases/{case_id}`

## Predictions and operational records

- `GET /projects/{project_id}/predictions`
- `GET /predictions/{prediction_id}/risk-factors`
- `POST /projects/{project_id}/predictions/refresh` — adapts the stored project into the canonical local ML schema, runs the saved ML pipeline, and persists its prediction, officer-facing factors, recommendations, and alerts.
- `POST /projects/{project_id}/what-if` — accepts a mapping of changed canonical ML fields and returns the ML-owned non-persistent scenario comparison.
- `GET /recommendations`, `POST /recommendations`, `PUT /recommendations/{recommendation_id}`, `DELETE /recommendations/{recommendation_id}`
- `GET /alerts`, `POST /alerts`, `PUT /alerts/{alert_id}/acknowledge`
- `GET /interventions`, `POST /interventions`, `GET /interventions/{intervention_id}`, `PUT /interventions/{intervention_id}`, `DELETE /interventions/{intervention_id}`

## Dashboard, GIS, reports, and integration status

- `GET /analytics/overview`
- `GET /analytics/attention`
- `GET /gis/projects`
- `GET /reports/projects/{project_id}`
- `GET /integrations/status`

Request and response models live in `backend/app/schemas/`. This document intentionally does not duplicate the canonical Role 1 ML feature list or ML payload contract.
