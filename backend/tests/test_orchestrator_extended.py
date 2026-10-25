"""
Extended Orchestrator tests — filter extraction, all intent branches,
resume context propagation, security constraints.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.orchestrator import Orchestrator
from app.services.storage_service import storage_service


# ─── Intent Classification — edge cases ────────────────────────────────────────

def test_intent_general_chat():
    orch = Orchestrator()
    assert orch.classify_intent("Hello there!") == "GENERAL_CHAT"
    assert orch.classify_intent("What is the weather?") == "GENERAL_CHAT"
    assert orch.classify_intent("Tell me about yourself") == "GENERAL_CHAT"


def test_intent_apply_variants():
    orch = Orchestrator()
    assert orch.classify_intent("I want to apply") == "APPLY"
    assert orch.classify_intent("Apply to job #2 please") == "APPLY"
    assert orch.classify_intent("Can you apply to the first one?") == "APPLY"


def test_intent_application_status_variants():
    orch = Orchestrator()
    assert orch.classify_intent("List my applied jobs") == "APPLICATION_STATUS"
    assert orch.classify_intent("Track my applications") == "APPLICATION_STATUS"
    assert orch.classify_intent("what did i apply for") == "APPLICATION_STATUS"


def test_intent_filter_jobs_experience():
    orch = Orchestrator()
    assert orch.classify_intent("Show me junior jobs") == "FILTER_JOBS"
    assert orch.classify_intent("Entry level engineer roles") == "FILTER_JOBS"
    assert orch.classify_intent("Find senior backend positions") == "FILTER_JOBS"


def test_intent_filter_jobs_tech():
    orch = Orchestrator()
    assert orch.classify_intent("Find python jobs") == "FILTER_JOBS"
    assert orch.classify_intent("React developer openings") == "FILTER_JOBS"
    assert orch.classify_intent("Looking for golang roles") == "FILTER_JOBS"


def test_intent_recommend_jobs():
    orch = Orchestrator()
    assert orch.classify_intent("Suggest jobs for me") == "RECOMMEND_JOBS"
    assert orch.classify_intent("What are the best matching jobs?") == "RECOMMEND_JOBS"
    assert orch.classify_intent("Find suitable roles") == "RECOMMEND_JOBS"


# ─── Filter Extraction ─────────────────────────────────────────────────────────

def test_extract_remote_filter():
    orch = Orchestrator()
    filters = orch.extract_filters("Show remote Python jobs")
    assert filters.get("remote") is True


def test_extract_location_filter():
    orch = Orchestrator()
    filters = orch.extract_filters("Find jobs in Berlin")
    assert "berlin" in (filters.get("location") or "").lower()


def test_extract_skill_filter():
    orch = Orchestrator()
    filters = orch.extract_filters("I need a React developer role")
    assert filters.get("skill") is not None
    assert "react" in filters["skill"].lower()


def test_extract_title_filter():
    orch = Orchestrator()
    filters = orch.extract_filters("Looking for backend engineer jobs")
    assert filters.get("title") is not None


def test_extract_multiple_filters():
    orch = Orchestrator()
    filters = orch.extract_filters("Remote Python backend jobs")
    assert filters.get("remote") is True
    assert filters.get("skill") is not None


# ─── Resolve Target Job ────────────────────────────────────────────────────────

def test_resolve_by_ordinal():
    orch = Orchestrator()
    recs = [
        {"job_id": "JOB-A", "title": "Engineer", "company": "Acme"},
        {"job_id": "JOB-B", "title": "Developer", "company": "Nova"},
    ]
    job_id, clarification = orch.resolve_target_job("Apply to the first one", "sess_x", recs)
    assert job_id == "JOB-A"
    assert clarification is None


def test_resolve_by_number():
    orch = Orchestrator()
    recs = [
        {"job_id": "JOB-1", "title": "Engineer", "company": "Acme"},
        {"job_id": "JOB-2", "title": "Developer", "company": "Nova"},
    ]
    job_id, clarification = orch.resolve_target_job("Apply to job 2", "sess_x", recs)
    assert job_id == "JOB-2"
    assert clarification is None


def test_resolve_by_company_name():
    orch = Orchestrator()
    recs = [{"job_id": "JOB-99", "title": "Engineer", "company": "CloudPulse"}]
    job_id, clarification = orch.resolve_target_job("Apply at CloudPulse", "sess_x", recs)
    assert job_id == "JOB-99"
    assert clarification is None


def test_resolve_out_of_range():
    orch = Orchestrator()
    recs = [{"job_id": "JOB-1", "title": "Engineer", "company": "Acme"}]
    job_id, clarification = orch.resolve_target_job("Apply to job 99", "sess_x", recs)
    assert job_id is None
    assert clarification is not None


def test_resolve_no_recommendations_ambiguous():
    orch = Orchestrator()
    job_id, clarification = orch.resolve_target_job("Apply now", "sess_x", [])
    assert job_id is None
    assert clarification is not None


# ─── Orchestrate: Full Flow Tests ─────────────────────────────────────────────

async def test_orchestrate_filter_jobs_response():
    orch = Orchestrator()
    res = await orch.orchestrate(
        message="Show remote Python developer jobs",
        session_id=f"sess_{uuid.uuid4().hex[:8]}",
    )
    assert res.type == "job_recommendations"
    assert len(res.data.get("jobs", [])) > 0


async def test_orchestrate_recommend_with_resume():
    orch = Orchestrator()
    resume = {
        "name": "Test Dev",
        "designation": "Backend Engineer",
        "skills": ["Python", "FastAPI"],
        "total_experience_years": 2.0,
    }
    res = await orch.orchestrate(
        message="Recommend jobs for me",
        session_id=f"sess_{uuid.uuid4().hex[:8]}",
        client_resume=resume,
    )
    assert res.type == "job_recommendations"
    assert "backend engineer" in res.message.lower() or "recommended" in res.message.lower()


async def test_orchestrate_application_status_empty():
    orch = Orchestrator()
    unique_sess = f"sess_new_{uuid.uuid4().hex}"
    res = await orch.orchestrate(
        message="Show my applications",
        session_id=unique_sess,
    )
    assert res.type == "application_status"
    assert "not submitted" in res.message.lower() or "no" in res.message.lower() or "have not" in res.message.lower()


async def test_orchestrate_general_chat_fallback():
    orch = Orchestrator()
    with patch.object(
        orch,
        "classify_intent",
        return_value="GENERAL_CHAT"
    ), patch(
        "app.agents.orchestrator.llm_service.generate_chat_reply",
        new=AsyncMock(return_value="I'm here to help you find jobs!")
    ):
        res = await orch.orchestrate(
            message="Hello",
            session_id=f"sess_{uuid.uuid4().hex[:8]}",
        )
        assert res.type == "text"
        assert len(res.message) > 0


async def test_orchestrate_apply_resolves_direct_job_id():
    orch = Orchestrator()
    jobs = storage_service.load_jobs()
    target = jobs[5]  # Use an index unlikely to conflict with other tests
    sess = f"sess_apply_{uuid.uuid4().hex[:8]}"

    res = await orch.orchestrate(
        message=f"Apply to {target['job_id']}",
        session_id=sess,
    )
    assert res.type == "application_success"
    assert target["job_id"] in res.message


async def test_orchestrate_duplicate_returns_text_not_error():
    """Orchestrator should NOT raise, just return a text 'duplicate' message."""
    orch = Orchestrator()
    jobs = storage_service.load_jobs()
    target = jobs[6]
    sess = f"sess_dup_{uuid.uuid4().hex[:8]}"

    # First apply
    await orch.orchestrate(
        message=f"Apply to {target['job_id']}",
        session_id=sess,
    )
    # Second — duplicate
    res = await orch.orchestrate(
        message=f"Apply to {target['job_id']}",
        session_id=sess,
    )
    assert res.type == "text"
    assert "duplicate" in res.message.lower() or "already applied" in res.message.lower()
