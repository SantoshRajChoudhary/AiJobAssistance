"""
Application Management Routes.
Supports applying to jobs (/api/applications and /api/apply) and retrieving application history.
"""

from typing import Optional, List
from fastapi import APIRouter, Query, status

from app.models.schemas import ApplyRequest, ApplyResponse, ApplicationRecord
from app.agents.tools.application_manager import record_application
from app.agents.tools.application_status import get_applications_for_session
from app.services.storage_service import storage_service
from app.utils.errors import JobNotFoundError

router = APIRouter(tags=["Applications"])


def _process_application(req: ApplyRequest) -> ApplyResponse:
    """Helper executing application recording logic."""
    return record_application(
        job_id=req.job_id,
        session_id=req.session_id,
        title=req.title,
        company=req.company,
        location=req.location,
        source_url=req.source_url or req.source_link,
    )


@router.post(
    "/api/applications",
    response_model=ApplyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to a job by job_id (Assessment Spec)",
)
def apply_to_job_spec(req: ApplyRequest):
    return _process_application(req)


@router.post(
    "/api/apply",
    response_model=ApplyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to a job (React Frontend Compatible Alias)",
)
def apply_to_job_alias(req: ApplyRequest):
    return _process_application(req)


@router.get(
    "/api/applications",
    response_model=List[ApplicationRecord],
    summary="Get application history (filtered by session_id or job_id if provided)",
)
def list_applications(
    session_id: Optional[str] = Query(default=None, description="Scope applications to a specific session"),
    job_id: Optional[str] = Query(default=None, description="Filter by specific job_id"),
    status: Optional[str] = Query(default=None, description="Filter by status (e.g. recorded, applied)"),
):
    apps = get_applications_for_session(session_id=session_id, job_id=job_id, status_filter=status)
    return apps


@router.get(
    "/api/applications/{job_id}",
    response_model=ApplicationRecord,
    summary="Get status of a specific job application",
)
def get_single_application(job_id: str):
    apps = storage_service.get_applications(job_id=job_id)
    if not apps:
        raise JobNotFoundError(job_id)
    first = apps[0]
    return ApplicationRecord(
        application_id=first.get("application_id", f"app_{job_id}"),
        session_id=first.get("session_id"),
        job_id=first["job_id"],
        title=first["title"],
        company=first["company"],
        location=first.get("location", "Remote"),
        source_url=first.get("source_url") or first.get("source_link") or "",
        source_link=first.get("source_link") or first.get("source_url") or "",
        applied_date=first.get("applied_date", ""),
        status=first.get("status", "recorded"),
    )
