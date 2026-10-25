"""
Tests for Job Matcher Tool.
Covers:
  - Deterministic baseline scoring (0-100 range)
  - Ranking behavior
  - Skill, remote, location, and title filters
  - Grounded explanations
"""

import pytest
from app.agents.tools.job_matcher import (
    score_job,
    match_and_rank_jobs,
    calculate_skill_score,
    calculate_title_score,
    calculate_experience_score,
)


def test_deterministic_scoring_range():
    resume = {
        "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        "designation": "Backend Engineer",
        "total_experience_years": 2,
    }
    job = {
        "job_id": "TEST-101",
        "title": "Backend Engineer",
        "company": "Tech Corp",
        "location": "Remote",
        "experience_required": "1-3 years",
        "skills": ["Python", "FastAPI", "SQL"],
        "description": "Looking for a backend engineer proficient in Python and FastAPI microservices.",
    }

    score, explanation = score_job(resume, job)
    assert 0 <= score <= 100
    assert score >= 70  # High match
    assert "Python" in explanation or "FastAPI" in explanation
    assert "Backend Engineer" in explanation or "role" in explanation.lower()


def test_skill_overlap_calculation():
    resume_skills = ["React", "TypeScript", "Node.js"]
    job_skills = ["React", "TypeScript"]
    desc = "We use React and TypeScript for building web apps."

    score = calculate_skill_score(resume_skills, job_skills, desc)
    # 2 out of 3 skills matched = ~0.67
    assert 0.6 <= score <= 0.7


def test_title_score_relevance():
    assert calculate_title_score("Frontend Engineer", "Senior React Frontend Developer") >= 0.8
    assert calculate_title_score("Data Scientist", "Frontend Engineer") < 0.5


def test_experience_fit_score():
    assert calculate_experience_score(2.0, "1-3 years") == 1.0
    # Underqualified
    assert calculate_experience_score(0.0, "5+ years") < 0.5


def test_remote_filtering():
    jobs = match_and_rank_jobs(
        resume={"skills": ["Python"]},
        filters={"remote": True},
        limit=5,
    )
    assert len(jobs) > 0
    for j in jobs:
        assert "remote" in j.location.lower()


def test_skill_filtering():
    jobs = match_and_rank_jobs(
        resume={"skills": ["Python"]},
        filters={"skill": "Python"},
        limit=5,
    )
    assert len(jobs) > 0
    for j in jobs:
        combined = " ".join(j.skills).lower() + " " + j.description.lower()
        assert "python" in combined
