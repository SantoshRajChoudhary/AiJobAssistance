"""
Tests for LLM Service extended — Anthropic provider, provider priority,
fallback chain, chat reply generation, JSON extraction edge cases.
"""
import pytest
from unittest.mock import patch, AsyncMock

from app.services.llm_service import LLMService


# ─── JSON Extraction ────────────────────────────────────────────────────────────

def test_extract_json_from_markdown_fence():
    llm = LLMService()
    text = '```json\n{"name": "Alice", "email": "alice@x.com"}\n```'
    result = llm._extract_json(text)
    assert result == {"name": "Alice", "email": "alice@x.com"}


def test_extract_json_from_raw_braces():
    llm = LLMService()
    text = 'Sure! Here is the data: {"name": "Bob", "skills": ["Python"]} done.'
    result = llm._extract_json(text)
    assert result["name"] == "Bob"
    assert "Python" in result["skills"]


def test_extract_json_empty_string():
    llm = LLMService()
    assert llm._extract_json("") is None


def test_extract_json_no_json():
    llm = LLMService()
    assert llm._extract_json("Hello, how can I help?") is None


def test_extract_json_malformed():
    llm = LLMService()
    # Should not raise, just return None
    result = llm._extract_json("{ broken json [[ ]}")
    assert result is None


# ─── Heuristic Resume Parse ────────────────────────────────────────────────────

def test_heuristic_parses_email():
    llm = LLMService()
    text = "John Doe\njohn.doe@company.com\nSoftware Engineer\nSkills: Python"
    result = llm._heuristic_resume_parse(text)
    assert result["email"] == "john.doe@company.com"


def test_heuristic_parses_phone():
    llm = LLMService()
    text = "Jane Smith\njane@x.com\n+1-555-123-4567\nBackend Developer"
    result = llm._heuristic_resume_parse(text)
    assert result["phone"] is not None


def test_heuristic_parses_skills():
    llm = LLMService()
    text = "Dev\ndev@x.com\nSkills: Python, React, Docker, PostgreSQL"
    result = llm._heuristic_resume_parse(text)
    assert "Python" in result["skills"]
    assert "React" in result["skills"]


def test_heuristic_no_fabrication_for_missing_fields():
    """If email/phone not in text, they must be None (never invented)."""
    llm = LLMService()
    text = "Developer\nPython, Docker"
    result = llm._heuristic_resume_parse(text)
    assert result["email"] is None
    assert result["phone"] is None


def test_heuristic_returns_all_schema_keys():
    llm = LLMService()
    text = "Dev\ndev@x.com\nPython"
    result = llm._heuristic_resume_parse(text)
    for key in ["name", "email", "phone", "designation", "skills", "experience", "education", "projects"]:
        assert key in result


# ─── Anthropic Provider ────────────────────────────────────────────────────────

async def test_anthropic_called_when_provider_is_anthropic():
    """When provider=anthropic and key is set, _call_anthropic should be invoked."""
    llm = LLMService()
    llm.provider = "anthropic"

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "fake-key"}), \
         patch.object(llm, "_call_anthropic", new=AsyncMock(return_value='{"name": "X"}')) as mock_fn:
        # Also patch settings.anthropic_api_key
        import app.services.llm_service as svc_module
        original_key = svc_module.settings.anthropic_api_key
        svc_module.settings.anthropic_api_key = "fake-key"

        result = await llm._execute_with_retry("system", "prompt")
        mock_fn.assert_called_once()

        svc_module.settings.anthropic_api_key = original_key


async def test_execute_retry_falls_back_to_secondary_provider():
    """If primary provider fails all retries, try the next available provider."""
    llm = LLMService()
    llm.provider = "gemini"
    llm.max_retries = 0

    import app.services.llm_service as svc_module
    svc_module.settings.gemini_api_key = "fake-gemini"
    svc_module.settings.openai_api_key = "fake-openai"
    svc_module.settings.anthropic_api_key = ""
    svc_module.settings.groq_api_key = ""

    with patch.object(llm, "_call_gemini", new=AsyncMock(side_effect=Exception("Gemini down"))), \
         patch.object(llm, "_call_openai", new=AsyncMock(return_value="OpenAI fallback reply")):
        result = await llm._execute_with_retry("system", "prompt")
        assert result == "OpenAI fallback reply"

    # Cleanup
    svc_module.settings.gemini_api_key = ""
    svc_module.settings.openai_api_key = ""


# ─── Chat Reply Generation ─────────────────────────────────────────────────────

async def test_chat_reply_returns_string_on_success():
    llm = LLMService()
    with patch.object(llm, "_execute_with_retry", new=AsyncMock(return_value="Here are some great Python jobs!")):
        reply = await llm.generate_chat_reply("Python jobs", "Context about Python jobs.")
        assert isinstance(reply, str)
        assert len(reply) > 0


async def test_chat_reply_returns_fallback_on_none():
    """When LLM returns None, generate_chat_reply must return a non-empty fallback string."""
    llm = LLMService()
    with patch.object(llm, "_execute_with_retry", new=AsyncMock(return_value=None)):
        reply = await llm.generate_chat_reply("Random question", "Context")
        assert isinstance(reply, str)
        assert len(reply) > 0


async def test_parse_resume_uses_heuristic_when_llm_fails():
    llm = LLMService()
    text = "Alice\nalice@example.com\n+91-9876543210\nSoftware Engineer\nSkills: Python, FastAPI"
    with patch.object(llm, "_execute_with_retry", new=AsyncMock(return_value=None)):
        result = await llm.parse_resume_to_json(text)
        assert result["email"] == "alice@example.com"
        assert "Python" in result["skills"]


async def test_parse_resume_extracts_from_valid_llm_json():
    llm = LLMService()
    mock_response = '```json\n{"name": "Carol", "email": "carol@y.com", "skills": ["Go", "Kubernetes"], "experience": [], "education": [], "projects": []}\n```'
    with patch.object(llm, "_execute_with_retry", new=AsyncMock(return_value=mock_response)):
        result = await llm.parse_resume_to_json("raw text")
        assert result["name"] == "Carol"
        assert "Go" in result["skills"]
