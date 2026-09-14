"""Authentication request and response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    name: str
    role: str


class CurrentUserResponse(BaseModel):
    user_id: UUID
    name: str
    role: str


class AuthenticationStatusResponse(BaseModel):
    auth_required: bool
