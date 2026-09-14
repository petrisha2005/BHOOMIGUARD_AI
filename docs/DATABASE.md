# Database and Alembic status

## Live data store

The application uses the existing Supabase PostgreSQL database. The root `.env` supplies `DATABASE_URL`; it is not committed or documented with credential values. The `database/` directory is documentation-only and is not expected to contain a local database file.

## Application models

SQLAlchemy models map the nine existing tables:

- `users`
- `projects`
- `acquisition_cases`
- `predictions`
- `risk_factors`
- `recommendations`
- `alerts`
- `interventions`
- `audit_logs`

`projects` carries the officer-maintained canonical ML input fields. The live table already received the percentage-column renames and additional canonical columns. `project_id`, `delay_flag`, and `actual_delay_days` are tracking/output fields rather than officer ML inputs. The integration persists an assessment using the existing `predictions`, `risk_factors`, `recommendations`, and `alerts` tables; it does not migrate raw training data or create speculative tables.

## Alembic

Alembic is configured through `backend/alembic.ini` and `backend/alembic/env.py`, using the shared SQLAlchemy metadata. There are no migration revisions because the Supabase schema existed before this codebase gained revision history. Do not create a speculative baseline or run migrations against Supabase solely to populate history. See [the versions note](../backend/alembic/versions/README.md).

Future schema changes must be reviewed, captured as a new Alembic revision, tested against a non-production database, and applied deliberately. This repository must not reset Supabase or fabricate database records.
