"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings for the backend."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(validation_alias="DATABASE_URL")
    jwt_secret_key: SecretStr | None = Field(default=None, validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    auth_required: bool = Field(default=True, validation_alias="AUTH_REQUIRED")
    cors_origins: str = Field(
        default="http://127.0.0.1:5173,http://localhost:5173",
        validation_alias="CORS_ORIGINS",
    )
    ml_service_url: str | None = Field(default=None, validation_alias="ML_SERVICE_URL")
    copilot_service_url: str | None = Field(default=None, validation_alias="COPILOT_SERVICE_URL")

    @property
    def cors_origin_list(self) -> list[str]:
        """Return configured CORS origins as a normalized list."""

        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
