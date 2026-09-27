# Local real-mode development

The normal frontend command runs in real mode. It does not use browser-only demo data unless `VITE_DEMO_MODE=true` is explicitly set.

## Prerequisites

1. Use an already-migrated PostgreSQL database containing the BhoomiGuard tables.
2. Copy `.env.example` to `.env` and set a real `DATABASE_URL` and a unique `JWT_SECRET_KEY`.
3. Keep `AUTH_REQUIRED=true` for the real authentication flow.

The repository contains SQLAlchemy models and Alembic configuration, but no Alembic migration revision for constructing a new schema. Do not assume `alembic upgrade head` can create a fresh database. Use the existing approved PostgreSQL/Supabase schema before provisioning accounts.

## Start the real application

```bash
# Terminal 1 — API
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — frontend (real mode by default)
cd frontend
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/`.

## Provision a development officer

With the API database settings available in root `.env`, run:

```bash
BHOOMIGUARD_ALLOW_DEVELOPMENT_SEED=true \
backend/.venv/bin/python scripts/provision_officer.py \
  --name "Development Officer" --email "officer@example.gov.in"
```

The command prompts privately for a password and refuses duplicate emails. It creates a normal PostgreSQL `users` row with a bcrypt hash. It does not print or store the password in source code.

## Optional presentation mode

```bash
cd frontend
npm run dev:demo -- --host 127.0.0.1
```

This mode is browser-only and clearly labels its data as local demonstration data. It does not exercise FastAPI, PostgreSQL, the saved model artifact, or SHAP.
