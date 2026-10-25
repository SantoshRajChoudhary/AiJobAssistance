"""
Application Manager Tool.
Handles recording, verifying, deduplication, and persistence of job applications.

Constraints:
  - Validates that the target job_id exists in jobs.json.
  - Verifies whether the job has already been applied to within the user/session.
  - Uses atomic writes and thread locking (via storage_service).
  - Uses the documented initial status 'recorded'.
  - Rejects unknown jobs with JobNotFoundError (404).
  - Explicitly flags or rejects duplicate applications with DuplicateApplicationError (409).
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from app.services.storage_service import storage_service
from app.utils.errors import JobNotFoundError, DuplicateApplicationError
from app.models.schemas import ApplicationRecord, ApplyResponse


def record_application(
    job_id: str,
    session_id: Optional[str] = None,
    title: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    source_url: Optional[str] = None,
) -> ApplyResponse:
    """
    Submits and tracks an application for a valid job in jobs.json.
    Raises JobNotFoundError if job does not exist.
    Raises DuplicateApplicationError if already applied in this session.
    """
    if not job_id or not job_id.strip():
        raise JobNotFoundError("Empty job ID")

    # 1. Verify that job exists in dataset
    job_record = storage_service.get_job_by_id(job_id)
    if not job_record:
        raise JobNotFoundError(job_id)

    # Use ground truth from dataset
    final_title = job_record.get("title") or title or "Position"
    final_company = job_record.get("company") or company or "Company"
    final_location = job_record.get("location") or location or "Remote"
    final_url = job_record.get("source_url") or job_record.get("source_link") or source_url or ""

    app_id = f"app_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.utcnow().isoformat() + "Z"

    record = {
        "application_id": app_id,
        "session_id": session_id,
        "job_id": job_record.get("job_id"),
        "title": final_title,
        "company": final_company,
        "location": final_location,
        "source_url": final_url,
        "source_link": final_url,
        "applied_date": now_iso,
        "status": "recorded",  # Documented initial status (tracked locally)
    }

    # 2. Save via atomic locked storage service
    save_result = storage_service.save_application(record)

    if save_result.get("is_duplicate"):
        existing = save_result.get("existing", {})
        raise DuplicateApplicationError(
            message=f"You have already applied to '{final_title}' at '{final_company}' ({job_id}) on {existing.get('applied_date', '')[:10]}.",
            details={"job_id": job_id, "existing_application": existing},
        )

    saved_app = ApplicationRecord(**record)
    return ApplyResponse(
        success=True,
        message=f"Application for '{final_title}' at '{final_company}' successfully recorded.",
        application=saved_app,
        is_duplicate=False,
    )
