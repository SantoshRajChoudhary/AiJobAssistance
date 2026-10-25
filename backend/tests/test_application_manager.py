"""
Tests for Application Manager Tool.
Covers:
  - Unknown job ID rejection (JobNotFoundError)
  - Successful application recording with status 'recorded'
  - Duplicate application prevention (DuplicateApplicationError)
  - Application history retrieval by session
"""

import uuid
import pytest
from app.agents.tools.application_manager import record_application
from app.agents.tools.application_status import get_applications_for_session
from app.utils.errors import JobNotFoundError, DuplicateApplicationError
from app.services.storage_service import storage_service


def test_unknown_job_id_raises_404():
    fake_id = "JOB-NONEXISTENT-999"
    with pytest.raises(JobNotFoundError):
        record_application(job_id=fake_id, session_id="test_sess_1")


def test_successful_application_and_duplicate_prevention():
    jobs = storage_service.load_jobs()
    assert len(jobs) > 0
    valid_job = jobs[0]
    valid_job_id = valid_job["job_id"]

    test_session = f"test_sess_{uuid.uuid4().hex[:6]}"

    # First attempt: should succeed
    res = record_application(job_id=valid_job_id, session_id=test_session)
    assert res.success is True
    assert res.application.job_id == valid_job_id
    assert res.application.status == "recorded"
    assert res.application.session_id == test_session

    # Verify present in session history
    apps = get_applications_for_session(session_id=test_session)
    assert any(a.job_id == valid_job_id for a in apps)

    # Second attempt with same job and session: MUST raise DuplicateApplicationError
    with pytest.raises(DuplicateApplicationError):
        record_application(job_id=valid_job_id, session_id=test_session)


def test_session_isolation_in_applications():
    """Different sessions can apply to the same job without conflicting with each other."""
    jobs = storage_service.load_jobs()
    valid_job = jobs[1] if len(jobs) > 1 else jobs[0]
    valid_job_id = valid_job["job_id"]

    sess_a = f"test_sess_A_{uuid.uuid4().hex[:6]}"
    sess_b = f"test_sess_B_{uuid.uuid4().hex[:6]}"

    res_a = record_application(job_id=valid_job_id, session_id=sess_a)
    assert res_a.success is True

    # Sess B can also apply to this job
    res_b = record_application(job_id=valid_job_id, session_id=sess_b)
    assert res_b.success is True

    # History isolation
    apps_a = get_applications_for_session(session_id=sess_a)
    apps_b = get_applications_for_session(session_id=sess_b)

    assert len(apps_a) == 1
    assert apps_a[0].session_id == sess_a
    assert len(apps_b) == 1
    assert apps_b[0].session_id == sess_b
