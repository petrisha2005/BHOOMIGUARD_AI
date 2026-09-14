"""Configurable HTTP boundary for the Role 1 prediction service."""

from typing import Any
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.core.config import settings


def request_prediction(payload: dict[str, Any]) -> dict[str, Any]:
    """Request a prediction from Role 1 without providing a fallback model."""

    if not settings.ml_service_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML prediction service is not configured",
        )

    try:
        import httpx

        response = httpx.post(settings.ml_service_url, json=jsonable_encoder(payload), timeout=20.0)
        response.raise_for_status()
    except ImportError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML integration dependencies are not installed",
        ) from error
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ML prediction service could not be reached",
        ) from error

    data = response.json()
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ML prediction service returned an invalid response",
        )
    return data
