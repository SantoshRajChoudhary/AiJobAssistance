"""
Job Statistics Route.
Returns aggregate statistics about the indexed job dataset:
  - Total jobs, remote count, top skills, top companies, top locations.
Also provides a single-job lookup endpoint: GET /api/jobs/{job_id}.
"""

from collections import Counter
from fastapi import APIRouter
from app.services.storage_service import storage_service
from app.models.schemas import JobItem
from app.utils.errors import JobNotFoundError

router = APIRouter(tags=["Jobs"])


@router.get(
    "/api/jobs/stats",
    summary="Aggregate statistics about the indexed job dataset",
)
def get_job_stats():
    """
    Returns:
      - total: total jobs in dataset
      - remote_count: jobs with 'remote' in location
      - top_skills: 10 most demanded skills across all listings
      - top_companies: 10 companies with most listings
      - top_locations: 10 most common locations
      - employment_types: breakdown by employment type
    """
    all_jobs = storage_service.load_jobs()
    total = len(all_jobs)

    remote_count = sum(
        1 for j in all_jobs if "remote" in j.get("location", "").lower()
    )

    skill_counter: Counter = Counter()
    company_counter: Counter = Counter()
    location_counter: Counter = Counter()
    employment_counter: Counter = Counter()

    for job in all_jobs:
        for skill in job.get("skills", []):
            if skill and skill.strip():
                skill_counter[skill.strip()] += 1

        company = job.get("company", "").strip()
        if company:
            company_counter[company] += 1

        location = job.get("location", "").strip()
        if location:
            # Normalize: strip trailing country/state qualifiers
            loc_short = location.split(",")[0].strip()
            location_counter[loc_short] += 1

        emp_type = job.get("employment_type", "Full-time") or "Full-time"
        employment_counter[emp_type] += 1

    return {
        "total": total,
        "remote_count": remote_count,
        "remote_percentage": round(remote_count / total * 100, 1) if total else 0,
        "top_skills": [
            {"skill": sk, "count": cnt}
            for sk, cnt in skill_counter.most_common(10)
        ],
        "top_companies": [
            {"company": co, "count": cnt}
            for co, cnt in company_counter.most_common(10)
        ],
        "top_locations": [
            {"location": loc, "count": cnt}
            for loc, cnt in location_counter.most_common(10)
        ],
        "employment_types": dict(employment_counter),
    }


@router.get(
    "/api/jobs/{job_id}",
    response_model=JobItem,
    summary="Get full details of a single job by its job_id",
)
def get_job_by_id(job_id: str):
    """Looks up a single job by exact job_id. Raises 404 if not found."""
    job = storage_service.get_job_by_id(job_id)
    if not job:
        raise JobNotFoundError(job_id)

    url = job.get("source_url") or job.get("source_link") or ""
    return JobItem(
        job_id=job["job_id"],
        title=job["title"],
        company=job["company"],
        location=job.get("location", "Remote"),
        experience_required=job.get("experience_required", "0-2 years"),
        skills=job.get("skills", []),
        description=job.get("description", ""),
        source_url=url,
        source_link=url,
        employment_type=job.get("employment_type", "Full-time"),
        remote_type=job.get("remote_type", "Remote"),
        posted_date=job.get("posted_date"),
        source_name=job.get("source") or job.get("source_name"),
    )
