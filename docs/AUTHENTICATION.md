# Authentication activation

The application has JWT bearer authentication with bcrypt password verification. The current local configuration deliberately uses `AUTH_REQUIRED=false` because no user account exists in Supabase yet.

## Provision the first officer account

Use a trusted administrator terminal after the PostgreSQL schema already exists. The script prompts for a password privately; do not pass a password on the command line and do not add it to `.env`.

```bash
BHOOMIGUARD_ALLOW_DEVELOPMENT_SEED=true \
backend/.venv/bin/python scripts/provision_officer.py \
  --name "Development Officer" --email "officer@example.gov.in"
```

The script refuses to overwrite an existing account and enforces a minimum 12-character password. It prints no password, hash, database URL, or JWT secret. It is a development-only bootstrap helper, not a production user-management system.

## Enable authentication

1. Change the root `.env` value to `AUTH_REQUIRED=true`.
2. Ensure `JWT_SECRET_KEY` is a long, unique secret stored only in the deployment secret store.
3. Restart FastAPI.
4. Sign in at `/login` using the provisioned account.

When enabled, all operational API routers require an `Authorization: Bearer <token>` header. `POST /auth/login` and `GET /auth/status` remain public; `GET /auth/me` verifies the current signed-in account.

## Production notes

- Provision accounts through this approved script or an equivalent protected administrator process.
- Do not commit `.env`, passwords, token values, or password hashes.
- Rotate the JWT secret only through planned deployment, because tokens signed with the old secret will become invalid.
