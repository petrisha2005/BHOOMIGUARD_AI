"""Password and JSON Web Token helpers."""

from datetime import UTC, datetime, timedelta
from typing import Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import User


bearer_scheme = HTTPBearer(auto_error=False)


def require_jwt_secret() -> str:
    """Return the configured JWT secret or explain why authentication is unavailable."""

    if settings.jwt_secret_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured on this server",
        )
    return settings.jwt_secret_key.get_secret_value()


def verify_password(password: str, password_hash: str | None) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""

    if not password_hash:
        return False
    try:
        import bcrypt

        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ImportError, ValueError):
        return False


def hash_password(password: str) -> str:
    """Hash a password for controlled account provisioning; never persist plaintext."""

    try:
        import bcrypt
    except ImportError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication dependencies are not installed",
        ) from error
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(subject: str, role: str) -> str:
    """Create a signed, expiring access token for an existing user."""

    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "role": role, "exp": expires_at}
    try:
        import jwt
    except ImportError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication dependencies are not installed",
        ) from error
    return jwt.encode(payload, require_jwt_secret(), algorithm=settings.jwt_algorithm)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Validate the bearer token and resolve an existing user for protected endpoints."""

    if not settings.auth_required:
        return None
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required")
    try:
        import jwt

        payload = jwt.decode(
            credentials.credentials,
            require_jwt_secret(),
            algorithms=[settings.jwt_algorithm],
        )
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise ValueError("Missing token subject")
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token") from error
    user = db.get(User, subject)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")
    return user
