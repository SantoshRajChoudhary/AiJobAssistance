"""
Job Matcher Agent Bridge.
Bridges legacy calls to the new deterministic job matcher tool.
"""

from typing import List, Dict, Any, Optional
from app.agents.tools.job_matcher import match_and_rank_jobs, score_job
from app.services.storage_service import storage_service


def load_jobs() -> List[Dict[str, Any]]:
    return storage_service.load_jobs()


def reload_jobs() -> int:
    return storage_service.reload_jobs()


def match_jobs(resume: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, top_n: int = 10) -> List[Dict[str, Any]]:
    jobs = match_and_rank_jobs(resume=resume, filters=filters, limit=top_n)
    return [j.model_dump() for j in jobs]
