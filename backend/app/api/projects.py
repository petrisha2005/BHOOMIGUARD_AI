"""Project CRUD API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Alert, Prediction, Project, Recommendation
from app.schemas.project import (
    ProjectCreate,
    BatchAnalysisProjectResult,
    BatchAnalysisResponse,
    ProjectDetailResponse,
    ProjectImportPreviewResponse,
    ProjectImportRequest,
    ProjectImportResult,
    ProjectImportRowError,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.database import get_project_or_404
from app.services.ml_integration import (
    FEATURE_COLUMNS,
    persist_assessment,
    run_assessment,
    validate_ml_input,
)


router = APIRouter(prefix="/projects", tags=["projects"])


def importable_project_fields() -> set[str]:
    """Return accepted request fields, including existing schema aliases."""

    fields = set(ProjectCreate.model_fields)
    for field in ProjectCreate.model_fields.values():
        choices = getattr(field.validation_alias, "choices", ())
        fields.update(str(choice) for choice in choices)
    return fields


def validate_import_rows(rows: list[dict[object, object]]) -> tuple[list[ProjectCreate], list[ProjectImportRowError]]:
    """Validate parsed CSV rows with the existing ProjectCreate contract."""

    valid_rows: list[ProjectCreate] = []
    errors: list[ProjectImportRowError] = []
    project_codes: set[str] = set()
    accepted_fields = importable_project_fields()
    for row_number, raw_row in enumerate(rows, start=2):
        cleaned = {
            str(field).strip(): value
            for field, value in raw_row.items()
            if str(field).strip() and value not in (None, "")
        }
        unsupported = sorted(set(cleaned) - accepted_fields)
        if unsupported:
            errors.extend(
                ProjectImportRowError(
                    row_number=row_number,
                    field=field,
                    message="Unsupported CSV column for the project import contract",
                )
                for field in unsupported
            )
            continue
        try:
            project = ProjectCreate.model_validate(cleaned)
        except ValueError as error:
            for item in error.errors():
                location = item.get("loc", ["row"])
                errors.append(ProjectImportRowError(
                    row_number=row_number,
                    field=str(location[-1]),
                    message=item.get("msg", "Invalid value"),
                ))
            continue
        try:
            validate_ml_input(project.model_dump())
        except ValueError as error:
            errors.append(ProjectImportRowError(
                row_number=row_number, field="ml_inference", message=str(error),
            ))
            continue
        normalized_code = project.project_code.strip().lower()
        if normalized_code in project_codes:
            errors.append(ProjectImportRowError(
                row_number=row_number,
                field="project_code",
                message="Duplicate project code in this CSV upload",
            ))
            continue
        project_codes.add(normalized_code)
        valid_rows.append(project)
    return valid_rows, errors


def _project_for_import_code(project_code: str, db: Session) -> Project | None:
    """Find the latest project for an import code without changing existing project design."""

    return db.scalar(
        select(Project)
        .where(func.lower(Project.project_code) == project_code.strip().lower())
        .order_by(Project.created_at.desc())
    )


def _latest_prediction(project_id: UUID, db: Session) -> Prediction | None:
    return db.scalar(
        select(Prediction)
        .where(Prediction.project_id == project_id)
        .order_by(Prediction.predicted_at.desc())
    )


def _ml_record_counts(project_id: UUID, db: Session) -> tuple[int, int]:
    """Count only adapter-owned records, leaving officer-maintained records distinct."""

    recommendations = db.scalar(
        select(func.count()).select_from(Recommendation).where(
            Recommendation.project_id == project_id,
            Recommendation.title.like("ML: %"),
        )
    )
    alerts = db.scalar(
        select(func.count()).select_from(Alert).where(
            Alert.project_id == project_id,
            Alert.alert_type.like("ML:%"),
        )
    )
    return int(recommendations or 0), int(alerts or 0)


def _batch_result(
    project: Project,
    prediction: Prediction | None,
    status_label: str,
    recommendation_count: int = 0,
    alert_count: int = 0,
    error: str | None = None,
) -> BatchAnalysisProjectResult:
    return BatchAnalysisProjectResult(
        project_id=project.id,
        project_code=project.project_code,
        name=project.name,
        status=status_label,
        risk_score=prediction.risk_score if prediction else None,
        delay_probability=prediction.delay_probability if prediction else None,
        risk_category=prediction.risk_category if prediction else None,
        recommendation_count=recommendation_count,
        alert_count=alert_count,
        error=error,
    )


@router.get("", response_model=list[ProjectResponse], status_code=status.HTTP_200_OK)
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    """List all projects."""

    return list(db.scalars(select(Project).order_by(Project.created_at.desc())).all())


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    """Create a project."""

    project = Project(**project_in.model_dump(exclude_unset=True))
    db.add(project)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project could not be created with the supplied data",
        ) from error
    db.refresh(project)
    return project


@router.post("/import/preview", response_model=ProjectImportPreviewResponse)
def preview_project_import(import_in: ProjectImportRequest) -> ProjectImportPreviewResponse:
    """Validate a parsed CSV before any project is written to Supabase."""

    valid_rows, errors = validate_import_rows(import_in.rows)
    return ProjectImportPreviewResponse(
        valid_rows=len(valid_rows),
        invalid_rows=len({error.row_number for error in errors}),
        errors=errors,
        preview=valid_rows[:20],
    )


@router.post("/import", response_model=ProjectImportResult, status_code=status.HTTP_201_CREATED)
def import_projects(import_in: ProjectImportRequest, db: Session = Depends(get_db)) -> ProjectImportResult:
    """Create only a fully valid CSV batch in one transaction."""

    valid_rows, errors = validate_import_rows(import_in.rows)
    if errors or len(valid_rows) != len(import_in.rows):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV contains invalid rows. Preview and correct the file before importing.",
        )
    db.add_all(Project(**project.model_dump(exclude_unset=True)) for project in valid_rows)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Projects could not be imported with the supplied data",
        ) from error
    return ProjectImportResult(created_count=len(valid_rows))


@router.post("/import/analyze", response_model=BatchAnalysisResponse, status_code=status.HTTP_201_CREATED)
def import_and_analyze_projects(
    import_in: ProjectImportRequest, db: Session = Depends(get_db)
) -> BatchAnalysisResponse:
    """Import a validated CSV and orchestrate the existing ML assessment per project.

    Each CSV row is validated before any database write. Projects are then committed
    before assessment so one ML failure cannot discard other accepted import rows.
    Repeating the same CSV reuses an already analysed matching project code instead
    of creating another prediction or adapter-owned operational record.
    """

    valid_rows, errors = validate_import_rows(import_in.rows)
    if errors or len(valid_rows) != len(import_in.rows):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV contains invalid rows. Preview and correct the file before running ML analysis.",
        )

    projects: list[tuple[Project, bool]] = []
    for project_in in valid_rows:
        existing = _project_for_import_code(project_in.project_code, db)
        if existing is not None:
            projects.append((existing, False))
        else:
            project = Project(**project_in.model_dump(exclude_unset=True))
            db.add(project)
            projects.append((project, True))
    try:
        db.commit()
        for project, created in projects:
            if created:
                db.refresh(project)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Projects could not be imported with the supplied data",
        ) from error

    results: list[BatchAnalysisProjectResult] = []
    for project, _created in projects:
        existing_prediction = _latest_prediction(project.id, db)
        if existing_prediction is not None:
            recommendation_count, alert_count = _ml_record_counts(project.id, db)
            results.append(_batch_result(
                project,
                existing_prediction,
                "Already analysed",
                recommendation_count,
                alert_count,
            ))
            continue
        try:
            prediction = persist_assessment(db, project, run_assessment(project))
            recommendation_count, alert_count = _ml_record_counts(project.id, db)
            results.append(_batch_result(
                project,
                prediction,
                "Analysed",
                recommendation_count,
                alert_count,
            ))
        except Exception:
            db.rollback()
            results.append(_batch_result(
                project,
                None,
                "Failed",
                error="ML analysis could not be completed for this project.",
            ))

    processed = sum(result.status != "Failed" for result in results)
    return BatchAnalysisResponse(
        total_projects=len(results),
        processed_projects=processed,
        failed_projects=len(results) - processed,
        results=results,
    )


@router.get("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def get_project(project_id: UUID, db: Session = Depends(get_db)) -> Project:
    """Get a project by UUID."""

    return get_project_or_404(project_id, db)


@router.get("/{project_id}/detail", response_model=ProjectDetailResponse)
def get_project_detail(project_id: UUID, db: Session = Depends(get_db)) -> dict[str, object]:
    """Return a project with persisted cases, prediction, and operational records."""

    project = db.scalar(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.acquisition_cases),
            selectinload(Project.predictions).selectinload(Prediction.risk_factors),
            selectinload(Project.recommendations),
            selectinload(Project.alerts),
            selectinload(Project.interventions),
        )
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    predictions = sorted(project.predictions, key=lambda item: item.predicted_at, reverse=True)
    return {
        "project": project,
        "acquisition_cases": project.acquisition_cases,
        "latest_prediction": predictions[0] if predictions else None,
        "recommendations": project.recommendations,
        "alerts": project.alerts,
        "interventions": project.interventions,
    }


@router.put("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def update_project(
    project_id: UUID, project_in: ProjectUpdate, db: Session = Depends(get_db)
) -> Project:
    """Update a project by UUID."""

    updates = project_in.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update",
        )

    project = get_project_or_404(project_id, db)
    for field, value in updates.items():
        setattr(project, field, value)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project could not be updated with the supplied data",
        ) from error
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, db: Session = Depends(get_db)) -> Response:
    """Delete a project by UUID."""

    project = get_project_or_404(project_id, db)
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
