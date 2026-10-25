"""
Job Matching Tool.
Scores and ranks real jobs from the dataset against candidate profiles and filters.
Implements a transparent deterministic baseline algorithm normalized to a 0-100 scale:
  - Skill Overlap (60% weight)
  - Title Relevance (20% weight)
  - Experience Fit (10% weight)
  - Location Preference (10% weight)
"""

import re
from typing import List, Dict, Any, Optional
from app.services.storage_service import storage_service
from app.models.schemas import JobItem

TITLE_SYNONYMS = {
    "frontend": ["frontend", "front-end", "react", "vue", "angular", "ui", "web"],
    "backend": ["backend", "back-end", "python", "node", "django", "fastapi", "spring", "api", "golang", "java"],
    "fullstack": ["fullstack", "full-stack", "full stack", "mern", "web developer"],
    "devops": ["devops", "sre", "cloud", "aws", "infrastructure", "kubernetes", "platform"],
    "data": ["data", "ml", "ai", "machine learning", "analytics", "scientist", "nlp"],
    "mobile": ["mobile", "ios", "android", "flutter", "react native"],
    "sde": ["software", "sde", "engineer", "developer", "programmer"],
}


def normalize_text(text: str) -> str:
    """Removes punctuation and lowercases text for robust matching."""
    if not text:
        return ""
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


def calculate_skill_score(resume_skills: List[str], job_skills: List[str], job_description: str) -> float:
    """
    Returns ratio (0.0 - 1.0) of resume skills matched in job skills or description.
    """
    if not resume_skills:
        return 0.5  # Neutral score if resume skills not provided

    job_text = normalize_text(" ".join(job_skills) + " " + job_description)
    matched = 0
    for s in resume_skills:
        clean_s = normalize_text(s)
        if clean_s and clean_s in job_text:
            matched += 1

    return min(1.0, matched / max(1, len(resume_skills)))


def calculate_title_score(resume_designation: str, job_title: str) -> float:
    """Returns title match relevance score (0.0 - 1.0)."""
    r_clean = normalize_text(resume_designation)
    j_clean = normalize_text(job_title)

    if not r_clean:
        return 0.5

    # Direct substring match
    if r_clean in j_clean or j_clean in r_clean:
        return 1.0

    # Group matching
    r_groups = {g for g, kws in TITLE_SYNONYMS.items() if any(kw in r_clean for kw in kws)}
    j_groups = {g for g, kws in TITLE_SYNONYMS.items() if any(kw in j_clean for kw in kws)}

    overlap = r_groups.intersection(j_groups)
    if overlap:
        return 0.9
    if "sde" in r_groups and "sde" in j_groups:
        return 0.6
    return 0.3


def calculate_experience_score(resume_exp_years: float, job_exp_str: str) -> float:
    """Returns experience fit score (0.0 - 1.0)."""
    nums = [int(n) for n in re.findall(r"\d+", job_exp_str)]
    if not nums:
        return 0.8  # No requirement means open to all

    min_exp = nums[0]
    max_exp = nums[-1] if len(nums) > 1 else min_exp + 2

    if min_exp <= resume_exp_years <= max_exp + 1:
        return 1.0
    if resume_exp_years < min_exp:
        deficit = min_exp - resume_exp_years
        return max(0.2, 1.0 - deficit * 0.25)
    # Overqualified
    return 0.7


def calculate_location_score(desired_location: str, is_remote_preferred: bool, job_location: str) -> float:
    """Returns location match score (0.0 - 1.0)."""
    j_loc = job_location.lower()
    is_job_remote = "remote" in j_loc

    if is_remote_preferred and is_job_remote:
        return 1.0
    if desired_location and normalize_text(desired_location) in normalize_text(j_loc):
        return 1.0
    if is_job_remote:
        return 0.85
    return 0.4


def score_job(resume: Dict[str, Any], job: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> tuple[int, str]:
    """
    Computes transparent baseline score (0-100) and concise explanation.
    Weights: Skills 60%, Title 20%, Experience 10%, Location 10%.
    """
    filters = filters or {}
    skills = resume.get("skills", [])
    designation = resume.get("designation", "")
    exp_years = float(resume.get("total_experience_years") or 1.0)
    user_location = filters.get("location") or (resume.get("contact") or {}).get("location") or ""
    remote_pref = filters.get("remote", True)

    skill_score = calculate_skill_score(skills, job.get("skills", []), job.get("description", ""))
    title_score = calculate_title_score(designation, job.get("title", ""))
    exp_score = calculate_experience_score(exp_years, job.get("experience_required", ""))
    loc_score = calculate_location_score(user_location, remote_pref, job.get("location", ""))

    composite = (skill_score * 0.60) + (title_score * 0.20) + (exp_score * 0.10) + (loc_score * 0.10)
    final_score = int(round(composite * 100))
    final_score = max(10, min(99, final_score))

    # Grounded explanation
    matched_skills = [
        s for s in skills if normalize_text(s) in normalize_text(" ".join(job.get("skills", [])) + " " + job.get("description", ""))
    ][:3]

    reasons = []
    if matched_skills:
        reasons.append(f"Strong overlap in {', '.join(matched_skills)}")
    if title_score >= 0.8:
        reasons.append(f"Role matches your designation as {designation or 'developer'}")
    if "remote" in job.get("location", "").lower():
        reasons.append("Remote flexibility matches preferences")
    if not reasons:
        reasons.append("Core skills and experience align with the technical requirements")

    explanation = f"{final_score}% match: " + "; ".join(reasons) + "."
    return final_score, explanation


def match_and_rank_jobs(
    resume: Optional[Dict[str, Any]] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 10,
) -> List[JobItem]:
    """
    Filters and ranks jobs from storage_service according to profile and filters.
    """
    all_jobs = storage_service.load_jobs()
    if not all_jobs:
        return []

    filters = filters or {}
    resume = resume or {}

    # Apply filters
    filtered_jobs = []
    for job in all_jobs:
        # Remote filter
        if filters.get("remote") is True:
            if "remote" not in job.get("location", "").lower():
                continue

        # Location filter
        req_loc = filters.get("location")
        if req_loc and req_loc.lower() not in job.get("location", "").lower():
            continue

        # Skill filter
        req_skill = filters.get("skill")
        if req_skill:
            req_skill_lower = req_skill.lower()
            job_skills = " ".join(job.get("skills", [])).lower()
            job_desc = job.get("description", "").lower()
            if req_skill_lower not in job_skills and req_skill_lower not in job_desc:
                continue

        # Title keyword filter
        req_title = filters.get("title")
        if req_title and req_title.lower() not in job.get("title", "").lower():
            continue

        # Experience required filter
        req_exp = filters.get("experience")
        if req_exp and req_exp.lower() not in job.get("experience_required", "").lower():
            continue

        filtered_jobs.append(job)

    # If filters returned zero jobs, fallback to all jobs with low score rather than failing
    candidate_jobs = filtered_jobs if filtered_jobs else all_jobs

    # Score and rank
    ranked_results = []
    for j in candidate_jobs:
        score, reason = score_job(resume, j, filters)
        job_copy = dict(j)
        job_copy["match_score"] = score
        job_copy["match_reason"] = reason
        # Ensure source_url and source_link are present
        url = job_copy.get("source_url") or job_copy.get("source_link") or "https://example.com/job"
        job_copy["source_url"] = url
        job_copy["source_link"] = url
        ranked_results.append(JobItem(**job_copy))

    # Sort descending by match_score
    ranked_results.sort(key=lambda x: (x.match_score or 0), reverse=True)
    return ranked_results[:limit]
