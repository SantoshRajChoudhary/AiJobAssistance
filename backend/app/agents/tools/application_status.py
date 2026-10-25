"""
Application Status Tool.
Retrieves and filters application history for the active session.
Handles empty history, date formatting, and status queries.
"""

from typing import List, Optional, Dict, Any
from app.services.storage_service import storage_service
from app.models.schemas import ApplicationRecord


def get_applications_for_session(
    session_id: Optional[str] = None,
    job_id: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> List[ApplicationRecord]:
    """
    Fetches applications filtered by session_id, job_id, or status.
    Returns an empty list when no applications exist.
    """
    raw_apps = storage_service.get_applications(session_id=session_id, job_id=job_id)

    records = []
    for item in raw_apps:
        if status_filter and item.get("status", "").lower() != status_filter.lower():
            continue

        # Ensure consistent schema
        records.append(
            ApplicationRecord(
                application_id=item.get("application_id") or f"app_{item.get('job_id')}",
                session_id=item.get("session_id"),
                job_id=item.get("job_id"),
                title=item.get("title", "Position"),
                company=item.get("company", "Company"),
                location=item.get("location", "Remote"),
                source_url=item.get("source_url") or item.get("source_link") or "",
                source_link=item.get("source_link") or item.get("source_url") or "",
                applied_date=item.get("applied_date", ""),
                status=item.get("status", "recorded"),
            )
        )

    return records


def format_application_history_text(applications: List[ApplicationRecord]) -> str:
    """Formats application list into readable markdown text for conversational responses."""
    if not applications:
        return "You have not submitted or recorded any job applications in this session yet."

    lines = ["Here are your tracked applications:\n"]
    for idx, app in enumerate(applications, 1):
        date_str = app.applied_date[:10] if app.applied_date else "Recent"
        lines.append(
            f"{idx}. **{app.title}** at **{app.company}**\n"
            f"   • Job ID: `{app.job_id}`\n"
            f"   • Location: {app.location}\n"
            f"   • Status: `{app.status.capitalize()}` ({date_str})\n"
        )
    return "\n".join(lines)
