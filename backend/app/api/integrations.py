"""Safe integration status routes without exposing configuration values."""

from fastapi import APIRouter

from app.schemas.analytics import IntegrationStatusResponse


router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/status", response_model=IntegrationStatusResponse)
def get_integration_status() -> IntegrationStatusResponse:
    return IntegrationStatusResponse(
        ml_service_configured=True,
        copilot_service_configured=False,
    )
