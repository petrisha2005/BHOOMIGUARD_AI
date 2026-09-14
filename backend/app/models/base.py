"""Shared SQLAlchemy declarative base for BhoomiGuard ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all mapped application models."""
