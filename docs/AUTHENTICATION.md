# Authentication activation

The application has JWT bearer authentication with bcrypt password verification. The current local configuration deliberately uses `AUTH_REQUIRED=false` because no user account exists in Supabase yet.

## Provision the first officer account

Use a trusted administrator terminal. The script prompts for a password privately; do not pass a password on the command line and do not add it to `.env`.

```powershell
$env:PYTHONPATH = "$PWD\backend;$PWD\backend\.venv\Lib\site-packages"
& "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\python3.12.exe" scripts\provision_officer.py --name "Authorized Officer" --email "officer@example.gov.in"
```

The script refuses to overwrite an existing account and enforces a minimum 12-character password. It prints no password, hash, database URL, or JWT secret.

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
