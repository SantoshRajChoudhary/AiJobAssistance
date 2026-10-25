"""
Job Search & Browsing Routes.
Supports full dataset browsing with query parameters for skills, title, location, remote, experience, and pagination.
"""

from typing import Optional
from fastapi import APIRouter, Query
from app.services.storage_service import storage_service
from app.models.schemas import JobListResponse, JobItem

router = APIRouter(tags=["Jobs"])


@router.get(
    "/api/jobs",
    response_model=JobListResponse,
    summary="Browse and filter the indexed job dataset with pagination",
)
def get_jobs(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    location: Optional[str] = Query(default=None, description="Filter by location substring"),
    skill: Optional[str] = Query(default=None, description="Filter by required technical skill"),
    title: Optional[str] = Query(default=None, description="Filter by job title substring"),
    remote: Optional[bool] = Query(default=None, description="Filter remote positions"),
    experience: Optional[str] = Query(default=None, description="Filter by experience required"),
):
    all_jobs = storage_service.load_jobs()
    results = all_jobs

    if remote is True:
        results = [j for j in results if "remote" in j.get("location", "").lower()]
    elif remote is False:
        results = [j for j in results if "remote" not in j.get("location", "").lower()]

    if location:
        loc_clean = location.lower().strip()
        results = [j for j in results if loc_clean in j.get("location", "").lower()]

    if skill:
        skill_clean = skill.lower().strip()
        results = [
            j for j in results
            if skill_clean in " ".join(j.get("skills", [])).lower()
            or skill_clean in j.get("description", "").lower()
        ]

    if title:
        title_clean = title.lower().strip()
        results = [j for j in results if title_clean in j.get("title", "").lower()]

    if experience:
        exp_clean = experience.lower().strip()
        results = [j for j in results if exp_clean in j.get("experience_required", "").lower()]

    total = len(results)
    start = (page - 1) * limit
    end = start + limit
    paginated_slice = results[start:end]

    job_items = [
        JobItem(
            job_id=j["job_id"],
            title=j["title"],
            company=j["company"],
            location=j.get("location", "Remote"),
            experience_required=j.get("experience_required", "0-2 years"),
            skills=j.get("skills", []),
            description=j.get("description", ""),
            source_url=j.get("source_url") or j.get("source_link") or "https://example.com/job",
            source_link=j.get("source_link") or j.get("source_url") or "https://example.com/job",
            employment_type=j.get("employment_type", "Full-time"),
            remote_type=j.get("remote_type", "Remote"),
            posted_date=j.get("posted_date"),
            source_name=j.get("source") or j.get("source_name"),
        )
        for j in paginated_slice
    ]

    return JobListResponse(
        total=total,
        page=page,
        limit=limit,
        jobs=job_items,
    )
