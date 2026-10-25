"""
Tests for the new /api/jobs/stats and /api/jobs/{job_id} endpoints.
"""
import pytest
from app.services.storage_service import storage_service


def test_job_stats_structure(client):
    """GET /api/jobs/stats must return expected shape."""
    res = client.get("/api/jobs/stats")
    assert res.status_code == 200
    data = res.json()

    assert "total" in data
    assert data["total"] > 0

    assert "remote_count" in data
    assert isinstance(data["remote_count"], int)

    assert "remote_percentage" in data
    assert 0 <= data["remote_percentage"] <= 100

    assert "top_skills" in data
    assert isinstance(data["top_skills"], list)
    assert len(data["top_skills"]) <= 10

    assert "top_companies" in data
    assert isinstance(data["top_companies"], list)

    assert "top_locations" in data
    assert isinstance(data["top_locations"], list)

    assert "employment_types" in data
    assert isinstance(data["employment_types"], dict)


def test_job_stats_top_skills_format(client):
    """Each top skill entry must have 'skill' and 'count' keys with correct types."""
    res = client.get("/api/jobs/stats")
    data = res.json()
    for entry in data["top_skills"]:
        assert "skill" in entry
        assert "count" in entry
        assert isinstance(entry["skill"], str)
        assert isinstance(entry["count"], int)
        assert entry["count"] > 0


def test_job_stats_top_companies_format(client):
    res = client.get("/api/jobs/stats")
    data = res.json()
    for entry in data["top_companies"]:
        assert "company" in entry
        assert "count" in entry
        assert entry["count"] > 0


def test_job_stats_remote_count_consistent(client):
    """remote_count should equal jobs that contain 'remote' in location."""
    res = client.get("/api/jobs/stats")
    data = res.json()

    # Independently verify
    all_jobs = storage_service.load_jobs()
    expected_remote = sum(1 for j in all_jobs if "remote" in j.get("location", "").lower())
    assert data["remote_count"] == expected_remote


def test_get_single_job_by_valid_id(client):
    """GET /api/jobs/{job_id} returns full job details for a valid ID."""
    jobs = storage_service.load_jobs()
    target = jobs[0]
    res = client.get(f"/api/jobs/{target['job_id']}")
    assert res.status_code == 200
    data = res.json()
    assert data["job_id"] == target["job_id"]
    assert data["title"] == target["title"]
    assert data["company"] == target["company"]
    assert "source_url" in data
    assert "source_link" in data
    assert "skills" in data
    assert isinstance(data["skills"], list)


def test_get_single_job_not_found(client):
    """GET /api/jobs/{job_id} with unknown ID returns 404."""
    res = client.get("/api/jobs/NOTREAL-00000")
    assert res.status_code == 404
    err = res.json()
    assert "error" in err or "detail" in err


def test_get_single_job_case_insensitive(client):
    """job_id lookup must be case-insensitive."""
    jobs = storage_service.load_jobs()
    job_id = jobs[0]["job_id"]
    # Try uppercase version
    res = client.get(f"/api/jobs/{job_id.upper()}")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == jobs[0]["title"]


def test_get_multiple_jobs_by_id(client, sample_jobs):
    """Spot-check 5 different jobs to verify consistent single-job lookup."""
    for job in sample_jobs:
        res = client.get(f"/api/jobs/{job['job_id']}")
        assert res.status_code == 200
        data = res.json()
        assert data["job_id"] == job["job_id"]
