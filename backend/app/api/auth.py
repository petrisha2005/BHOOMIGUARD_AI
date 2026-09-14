"""Authentication endpoints for existing user records."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_current_user, require_jwt_secret, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas.auth import AuthenticationStatusResponse, CurrentUserResponse, LoginRequest, TokenResponse


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/status", response_model=AuthenticationStatusResponse)
def authentication_status() -> AuthenticationStatusResponse:
    """Expose only whether the browser should require an authenticated session."""

    return AuthenticationStatusResponse(auth_required=settings.auth_required)


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate an existing bcrypt-backed user when JWT configuration is present."""

    require_jwt_secret()
    user = db.scalar(select(User).where(User.email == credentials.email))
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role),
        user_id=user.id,
        name=user.name,
        role=user.role,
    )


@router.get("/me", response_model=CurrentUserResponse)
def current_user(user: User = Depends(get_current_user)) -> CurrentUserResponse:
    """Return the authenticated account identity without returning sensitive fields."""

    if user is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication is not enabled")
    return CurrentUserResponse(user_id=user.id, name=user.name, role=user.role)
