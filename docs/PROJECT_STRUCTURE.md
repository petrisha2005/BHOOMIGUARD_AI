# Source project structure

```text
BhoomiGuard-AI/
├── backend/              FastAPI application, ORM, schemas, Alembic configuration
├── database/             Documentation for the remote Supabase data layer
├── docs/                 Architecture, API, database, authentication, deployment notes
├── frontend/             React/Vite officer console
├── gis/                  GIS implementation notes
├── infra/                Deployment-infrastructure placeholder and guidance
├── ml_integration/       Role 1 integration-boundary stubs only
├── reports/              PDF-report implementation notes
├── scripts/              Deliberate administrator scripts
└── tests/                Empty test-suite structure with honest status documentation
```

Generated local artifacts are deliberately omitted from this source view: `.venv/`, `node_modules/`, `dist/`, `__pycache__/`, and `.git/`.

The frontend source is organized into components, layout, pages, hooks, services, utilities, and assets. The backend source is organized into API routers, configuration, database session handling, ORM models, Pydantic schemas, and services. The full current file inventory can be obtained with `rg --files` while excluding generated directories.
