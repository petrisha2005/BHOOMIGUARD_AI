# Deployment readiness

## Backend

- Use a managed Python runtime and install `backend/requirements.txt`.
- Set the root environment values from `.env.example` in the deployment secret store. Never upload or commit a real `.env` file.
- Keep Supabase credentials in `DATABASE_URL`; use TLS as required by the Supabase connection string.
- Run the FastAPI app with a production ASGI process, for example `uvicorn app.main:app --host 0.0.0.0 --port $PORT` behind the host platform's TLS termination.
- Set `AUTH_REQUIRED=true`, set a unique `JWT_SECRET_KEY`, and provision at least one bcrypt-hashed officer account through an approved secure process before exposing the API. See [authentication activation](AUTHENTICATION.md).
- Set `CORS_ORIGINS` to exact deployed frontend origins. Do not use a wildcard when credentials are enabled.

## Frontend

- Set `VITE_API_BASE_URL` to the deployed API URL before building when the frontend and API are on different origins.
- Build with `npm run build`; deploy `frontend/dist/` to a static host.
- For same-origin deployment, proxy the frontend `/api` prefix to the FastAPI service.

## Supabase

- The data store is the existing Supabase PostgreSQL database; the local `database/` directory intentionally contains no database files.
- The canonical project-column migration is already applied. Do not run a schema migration during ordinary deployment.
- Ensure the application database role has only the required privileges and that routine backups are enabled in the Supabase project.

## Role 1 hand-off

- Supply `ML_SERVICE_URL` only when the approved Role 1 endpoint contract is deployed.
- The ML service must return its approved prediction/explanation contract. Role 2 does not fall back to synthetic predictions or explanations.
- The What-If route runs locally against the saved ML artifact and must be exercised with a complete canonical project record before deployment.

## Pre-release checklist

- [ ] Backend compilation and OpenAPI validation pass.
- [ ] Frontend lint and production build pass.
- [ ] Production CORS origins are exact.
- [ ] Authentication is enabled and a secure officer account is provisioned.
- [ ] Supabase connectivity works without exposing credentials.
- [ ] Role 1 service health and contracts are verified, or ML-dependent interfaces remain clearly unavailable.
