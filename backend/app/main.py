"""BhoomiGuard AI FastAPI application entry point."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alerts import router as alerts_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.cases import router as cases_router
from app.api.gis import router as gis_router
from app.api.integrations import router as integrations_router
from app.api.interventions import router as interventions_router
from app.api.predictions import router as predictions_router
from app.api.projects import router as projects_router
from app.api.recommendations import router as recommendations_router
from app.api.reports import router as reports_router
from app.core.config import settings
from app.core.security import get_current_user


app = FastAPI(title="BhoomiGuard AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
protected = [Depends(get_current_user)]
app.include_router(projects_router, dependencies=protected)
app.include_router(cases_router, dependencies=protected)
app.include_router(predictions_router, dependencies=protected)
app.include_router(recommendations_router, dependencies=protected)
app.include_router(alerts_router, dependencies=protected)
app.include_router(interventions_router, dependencies=protected)
app.include_router(analytics_router, dependencies=protected)
app.include_router(gis_router, dependencies=protected)
app.include_router(reports_router, dependencies=protected)
app.include_router(integrations_router, dependencies=protected)
