"""Shared ORM lookup helpers."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Project


def get_project_or_404(project_id: UUID, db: Session) -> Project:
    """Return the requested project or raise a standard 404 response."""

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project
