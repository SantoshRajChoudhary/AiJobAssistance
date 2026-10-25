"""
Extended tests for Job Matcher — location scoring, overqualification,
multi-filter combinations, and ranking order guarantees.
"""
import pytest
from app.agents.tools.job_matcher import (
    calculate_location_score,
    calculate_skill_score,
    calculate_title_score,
    calculate_experience_score,
    score_job,
    match_and_rank_jobs,
)


# ─── Location Score ────────────────────────────────────────────────────────────

def test_location_score_remote_preferred_and_remote_job():
    score = calculate_location_score("", True, "Remote — Worldwide")
    assert score == 1.0


def test_location_score_city_match():
    score = calculate_location_score("Bangalore", False, "Bangalore, India")
    assert score == 1.0


def test_location_score_remote_job_no_preference():
    """Remote job should still score well even if remote not explicitly preferred."""
    score = calculate_location_score("", False, "Remote")
    assert score >= 0.8


def test_location_score_mismatch():
    score = calculate_location_score("New York", False, "London, UK")
    assert score < 0.6


# ─── Skill Score Edge Cases ────────────────────────────────────────────────────

def test_skill_score_empty_resume_skills():
    """No resume skills → neutral score, not zero."""
    score = calculate_skill_score([], ["Python", "FastAPI"], "Uses Python and FastAPI.")
    assert score == 0.5


def test_skill_score_full_overlap():
    score = calculate_skill_score(["React", "TypeScript"], ["React", "TypeScript"], "React and TypeScript required.")
    assert score == 1.0


def test_skill_score_partial_overlap():
    score = calculate_skill_score(["React", "TypeScript", "Node.js"], ["React"], "We use React heavily.")
    # 1 of 3 matched
    assert 0.3 <= score <= 0.4


def test_skill_score_description_match():
    """Skills found in description (not skills list) still count."""
    score = calculate_skill_score(["GraphQL"], [], "We need strong GraphQL expertise.")
    assert score > 0


# ─── Title Score ───────────────────────────────────────────────────────────────

def test_title_score_exact_substring():
    assert calculate_title_score("Backend Engineer", "Senior Backend Engineer") == 1.0


def test_title_score_group_overlap():
    # 'react' triggers 'frontend' group; job is 'Frontend Developer'
    assert calculate_title_score("React Developer", "Frontend Developer") >= 0.8


def test_title_score_no_match():
    score = calculate_title_score("Data Scientist", "iOS Mobile Engineer")
    assert score < 0.5


def test_title_score_empty_designation():
    """Empty designation → neutral score."""
    assert calculate_title_score("", "Software Engineer") == 0.5


# ─── Experience Score ──────────────────────────────────────────────────────────

def test_experience_perfect_fit():
    assert calculate_experience_score(3.0, "2-4 years") == 1.0


def test_experience_overqualified():
    score = calculate_experience_score(10.0, "0-2 years")
    assert score == 0.7


def test_experience_underqualified():
    score = calculate_experience_score(0.5, "5+ years")
    assert score < 0.5


def test_experience_no_requirement():
    """No experience string → open position → high score."""
    assert calculate_experience_score(0.0, "") >= 0.7


# ─── Composite Scoring ─────────────────────────────────────────────────────────

def test_score_job_clamped_range():
    """Score must always be 10-99 regardless of weights."""
    resume = {"skills": [], "designation": "", "total_experience_years": 0}
    job = {
        "job_id": "X-001",
        "title": "Some Role",
        "company": "Co",
        "location": "Unknown City",
        "experience_required": "10+ years",
        "skills": ["COBOL", "Fortran"],
        "description": "Very niche legacy skills",
    }
    score, _ = score_job(resume, job)
    assert 10 <= score <= 99


def test_score_job_explanation_non_empty():
    resume = {"skills": ["Python"], "designation": "Engineer"}
    job = {
        "job_id": "X-002",
        "title": "Python Engineer",
        "company": "Co",
        "location": "Remote",
        "experience_required": "0-2 years",
        "skills": ["Python"],
        "description": "Python is needed.",
    }
    _, explanation = score_job(resume, job)
    assert len(explanation) > 10
    assert "%" in explanation


# ─── match_and_rank_jobs ───────────────────────────────────────────────────────

def test_ranking_order_is_descending(backend_resume):
    jobs = match_and_rank_jobs(resume=backend_resume, filters={}, limit=10)
    scores = [j.match_score for j in jobs]
    assert scores == sorted(scores, reverse=True)


def test_combined_filters_skill_and_remote(backend_resume):
    jobs = match_and_rank_jobs(
        resume=backend_resume,
        filters={"skill": "Python", "remote": True},
        limit=5,
    )
    for j in jobs:
        assert "python" in (" ".join(j.skills) + j.description).lower()
        assert "remote" in j.location.lower()


def test_fallback_when_filters_match_nothing():
    """If filters match 0 jobs, fallback to unfiltered list (never return empty)."""
    jobs = match_and_rank_jobs(
        resume={},
        filters={"skill": "ZZZImaginaryLanguageXXX"},
        limit=5,
    )
    # Should fall back to global list
    assert len(jobs) > 0


def test_match_score_in_job_item(backend_resume):
    jobs = match_and_rank_jobs(resume=backend_resume, filters={}, limit=3)
    for j in jobs:
        assert j.match_score is not None
        assert 10 <= j.match_score <= 99


def test_match_reason_in_job_item(backend_resume):
    jobs = match_and_rank_jobs(resume=backend_resume, filters={}, limit=3)
    for j in jobs:
        assert j.match_reason is not None
        assert len(j.match_reason) > 5


def test_limit_respected(backend_resume):
    jobs = match_and_rank_jobs(resume=backend_resume, filters={}, limit=3)
    assert len(jobs) <= 3


def test_title_filter():
    jobs = match_and_rank_jobs(
        resume={},
        filters={"title": "engineer"},
        limit=10,
    )
    assert len(jobs) > 0
    for j in jobs:
        assert "engineer" in j.title.lower()
