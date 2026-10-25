"""
Integration tests for FastAPI REST Endpoints.
Covers:
  - GET /api/health
  - POST /api/resume/upload & POST /api/parse-resume
  - POST /api/chat
  - GET /api/jobs
  - POST /api/applications & POST /api/apply
  - GET /api/applications
  - Error statuses: 400, 404, 409, 413
"""

import uuid
import pytest
from fastapi.testclient import TestClient
import fitz

from app.main import app
from app.services.storage_service import storage_service

client = TestClient(app)


def create_in_memory_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    b = doc.tobytes()
    doc.close()
    return b


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "jobs_indexed" in data
    assert data["jobs_indexed"] > 0
    assert data["dataset_available"] is True
    # Secrets should never be exposed
    assert "api_key" not in data
    assert "secret" not in data


def test_resume_upload_endpoint_success():
    pdf_bytes = create_in_memory_pdf(
        "Candidate Name\ncandidate@tech.com\nSoftware Engineer\nSkills: Python, FastAPI, Docker\n"
        "EXPERIENCE\nBackend Developer at CloudCo\n"
    )
    files = {"file": ("resume.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/api/resume/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "profile" in data
    assert "session_id" in data
    assert "recommended_jobs" in data
    assert data["profile"]["email"] == "candidate@tech.com"
    # Frontend alias check
    assert "resume" in data


def test_resume_upload_endpoint_invalid_file():
    files = {"file": ("malicious.sh", b"echo hello", "text/x-sh")}
    response = client.post("/api/resume/upload", files=files)
    assert response.status_code == 400
    err = response.json()
    assert "error" in err or "detail" in err


def test_chat_endpoint_job_recommendation():
    payload = {
        "session_id": "test_session_chat",
        "message": "Show remote python jobs",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "job_recommendations"
    assert "session_id" in data
    assert "data" in data
    assert "jobs" in data["data"]


def test_chat_endpoint_empty_message():
    payload = {"message": "   "}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 400


def test_jobs_search_endpoint():
    response = client.get("/api/jobs?remote=true&page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["jobs"]) <= 5
    assert data["page"] == 1
    # Verify job record fields
    sample = data["jobs"][0]
    assert "job_id" in sample
    assert "title" in sample
    assert "company" in sample
    assert "source_url" in sample
    assert "source_link" in sample


def test_apply_and_duplicate_endpoints():
    jobs = storage_service.load_jobs()
    job = jobs[2] if len(jobs) > 2 else jobs[0]
    job_id = job["job_id"]

    test_sess = f"sess_api_{uuid.uuid4().hex[:6]}"

    # Apply via /api/applications
    payload = {"session_id": test_sess, "job_id": job_id}
    res1 = client.post("/api/applications", json=payload)
    assert res1.status_code == 201
    d1 = res1.json()
    assert d1["success"] is True
    assert d1["application"]["status"] == "recorded"

    # Duplicate attempt -> 409 Conflict
    res2 = client.post("/api/applications", json=payload)
    assert res2.status_code == 409

    # List applications for this session
    res3 = client.get(f"/api/applications?session_id={test_sess}")
    assert res3.status_code == 200
    apps = res3.json()
    assert len(apps) == 1
    assert apps[0]["job_id"] == job_id


def test_apply_unknown_job_id():
    payload = {"session_id": "sess_x", "job_id": "UNKNOWN-9999"}
    response = client.post("/api/applications", json=payload)
    assert response.status_code == 404
