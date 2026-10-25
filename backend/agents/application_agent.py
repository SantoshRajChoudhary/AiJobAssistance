"""
Application Agent Bridge.
Bridges legacy calls to the new atomic application manager and status tools.
"""

from typing import List, Dict, Any, Optional
from app.agents.tools.application_manager import record_application
from app.agents.tools.application_status import get_applications_for_session
from app.services.storage_service import storage_service


def get_all_applications() -> List[Dict[str, Any]]:
    return storage_service.get_applications()


def apply_to_job(
    job_id: str,
    title: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    source_link: Optional[str] = None,
) -> Dict[str, Any]:
    res = record_application(
        job_id=job_id,
        title=title,
        company=company,
        location=location,
        source_url=source_link,
    )
    return res.application.model_dump()


def get_application_status(job_id: str) -> Optional[Dict[str, Any]]:
    apps = storage_service.get_applications(job_id=job_id)
    return apps[0] if apps else None
