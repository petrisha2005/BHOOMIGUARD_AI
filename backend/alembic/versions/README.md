# Alembic revision status

There are no Alembic revision files in this repository. The Supabase schema and the canonical project-column alignment were applied directly to the existing live database before this repository gained Alembic revision history.

No baseline revision is included because generating one now could misrepresent the already-applied schema or encourage an unnecessary live migration. Future schema changes should begin with a reviewed Alembic revision from the then-current, verified database state; do not use this repository to reset or recreate Supabase.
