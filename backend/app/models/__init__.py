"""ORM model exports and metadata registration."""

from app.models.acquisition_case import AcquisitionCase
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.intervention import Intervention
from app.models.prediction import Prediction
from app.models.project import Project
from app.models.recommendation import Recommendation
from app.models.risk_factor import RiskFactor
from app.models.user import User

__all__ = [
    "AcquisitionCase",
    "Alert",
    "AuditLog",
    "Base",
    "Intervention",
    "Prediction",
    "Project",
    "Recommendation",
    "RiskFactor",
    "User",
]
