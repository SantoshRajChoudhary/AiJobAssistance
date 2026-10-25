# Hidani Tech — AI Job Chat Assistant: Backend

A production-quality FastAPI backend powering an intelligent multi-agent job matching and application assistant with a real dataset of 1,800+ scraped job listings.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Environment Variables](#environment-variables)
4. [API Reference](#api-reference)
5. [Agent System](#agent-system)
6. [LLM Service](#llm-service)
7. [Storage Architecture](#storage-architecture)
8. [Test Suite](#test-suite)
9. [Project Structure](#project-structure)

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                           │
│  ┌──────────┐  ┌───────────┐  ┌────────┐  ┌──────────────────┐   │
│  │  /chat   │  │  /resume  │  │ /jobs  │  │  /applications   │   │
│  └────┬─────┘  └─────┬─────┘  └───┬────┘  └────────┬─────────┘   │
│       │               │            │                 │             │
│  ┌────▼───────────────▼────┐  ┌────▼─────────────────▼────────┐  │
│  │     Orchestrator Agent  │  │       Storage Service          │  │
│  │  (Intent Classification │  │  (Atomic JSON · Thread-safe)   │  │
│  │   + Tool Dispatch)      │  └──────────────────────────────  ┘  │
│  └────┬──────────┬─────────┘                                       │
│       │          │                                                  │
│  ┌────▼────┐  ┌──▼──────────────┐                                 │
│  │  LLM    │  │  Specialized     │                                 │
│  │ Service │  │  Agent Tools     │                                 │
│  │(4 LLMs) │  │ · resume_parser  │                                 │
│  │+ offline│  │ · job_matcher    │                                 │
│  │fallback │  │ · app_manager    │                                 │
│  └─────────┘  │ · app_status     │                                 │
│               └──────────────────┘                                 │
└────────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Deterministic offline fallback** — the full system works with zero API keys via a heuristic resume parser and rule-based scoring engine.
- **Prompt injection defense** — all untrusted user text is wrapped in `<untrusted_data>` tags in LLM prompts.
- **Atomic writes** — JSON files are written via `tempfile + os.replace` to guarantee no corruption on crash.
- **Session isolation** — each user session has its own opaque UUID, preventing cross-user data leakage.

---

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Run the server

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or use the convenience script:

```bat
start.bat
```

### Verify

- Health check: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Application environment |
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server port |
| `DEBUG` | `false` | Enable debug mode and verbose logging |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins (comma-separated or JSON array) |
| `LLM_PROVIDER` | `gemini` | Active LLM provider: `gemini` \| `openai` \| `anthropic` \| `groq` |
| `LLM_MODEL` | `gemini-1.5-flash` | Model name for the configured provider |
| `LLM_TIMEOUT_SECONDS` | `15` | Per-request timeout for LLM API calls |
| `LLM_MAX_RETRIES` | `2` | Retry attempts before falling back |
| `GEMINI_API_KEY` | _(empty)_ | Google Gemini API key |
| `OPENAI_API_KEY` | _(empty)_ | OpenAI API key |
| `ANTHROPIC_API_KEY` | _(empty)_ | Anthropic Claude API key |
| `GROQ_API_KEY` | _(empty)_ | Groq API key |
| `MAX_UPLOAD_SIZE_BYTES` | `5242880` | Max resume upload size (5 MB) |
| `JOBS_FILE` | `data/jobs.json` | Path to the job dataset |
| `APPLICATIONS_FILE` | `data/applications.json` | Path to applications store |
| `SESSIONS_FILE` | `data/sessions.json` | Path to sessions store |

> **Note:** If **no API keys** are configured, the system automatically falls back to a high-precision deterministic rule-based engine. All 33+ tests pass with zero keys.

---

## API Reference

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Service status, jobs indexed count, version |

**Response:**
```json
{
  "status": "ok",
  "jobs_indexed": 1847,
  "dataset_available": true,
  "version": "1.0.0",
  "storage_type": "JSON File Storage (Persistent Atomic)"
}
```

---

### Resume

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/resume/upload` | Upload and parse a PDF or DOCX resume (assessment spec) |
| `POST` | `/api/parse-resume` | Alias for frontend compatibility |

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | ✅ | PDF or DOCX resume (max 5 MB) |
| `session_id` | string | ❌ | Existing session ID to associate resume with |

**Response `200`:**
```json
{
  "profile": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+1-555-123-4567",
    "designation": "Backend Engineer",
    "skills": ["Python", "FastAPI", "Docker"],
    "experience": [{ "role": "SDE", "company": "Acme", "duration": "2 years", "description": "..." }],
    "education": [{ "degree": "B.Tech CSE", "institution": "IIT", "year": "2022" }],
    "projects": [{ "name": "API Gateway", "tech_stack": ["Python"], "description": "..." }],
    "contact": { "email": "jane@example.com", "phone": "...", "location": "Bangalore" },
    "total_experience_years": 2.0
  },
  "session_id": "sess_<uuid>",
  "recommended_jobs": [ /* top 10 matched JobItem objects */ ],
  "message": "Resume parsed successfully."
}
```

**Error responses:**

| Code | Reason |
|---|---|
| `400` | Invalid file format or empty file |
| `413` | File exceeds 5 MB limit |

---

### Chat

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Conversational job assistant — intent classification + tool dispatch |

**Request body:**
```json
{
  "message": "Show me remote Python jobs",
  "session_id": "sess_abc123",
  "resume": { /* optional ResumeProfile dict */ },
  "applied_jobs": [ /* optional list of applied job dicts */ ],
  "recommended_jobs": [ /* optional list of displayed recommendation dicts */ ]
}
```

**Response `200` — possible `type` values:**

| `type` | When | Payload |
|---|---|---|
| `job_recommendations` | Job search/filter/recommend | `data.jobs` array |
| `application_status` | User asks for applied history | `data.applications` array |
| `application_success` | Apply succeeds | `data.application` object |
| `clarification` | Ambiguous apply intent | clarifying question message |
| `text` | General chat or duplicate apply | text response |

---

### Jobs

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/jobs` | Browse/filter paginated job dataset |
| `GET` | `/api/jobs/stats` | Aggregate dataset statistics |
| `GET` | `/api/jobs/{job_id}` | Single job lookup by ID |

#### `GET /api/jobs`

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | `1` | Page number (1-indexed) |
| `limit` | int | `20` | Items per page (max 100) |
| `remote` | bool | — | Filter remote positions |
| `location` | string | — | Filter by location substring |
| `skill` | string | — | Filter by required skill |
| `title` | string | — | Filter by job title substring |
| `experience` | string | — | Filter by experience required |

**Response `200`:**
```json
{
  "total": 342,
  "page": 1,
  "limit": 20,
  "jobs": [ /* JobItem array */ ]
}
```

#### `GET /api/jobs/stats`

**Response `200`:**
```json
{
  "total": 1847,
  "remote_count": 924,
  "remote_percentage": 50.1,
  "top_skills": [
    { "skill": "Python", "count": 438 },
    { "skill": "React", "count": 312 }
  ],
  "top_companies": [
    { "company": "Acme Corp", "count": 12 }
  ],
  "top_locations": [
    { "location": "Remote", "count": 924 }
  ],
  "employment_types": { "Full-time": 1200, "Contract": 400, "Part-time": 247 }
}
```

#### `GET /api/jobs/{job_id}`

Returns the full `JobItem` for a specific job ID (case-insensitive). Returns `404` if not found.

---

### Applications

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/applications` | Apply to a job (assessment spec) |
| `POST` | `/api/apply` | Apply to a job (frontend alias) |
| `GET` | `/api/applications` | List applications (filterable by session/job/status) |
| `GET` | `/api/applications/{job_id}` | Get a specific application by job ID |

**Apply request body:**
```json
{
  "session_id": "sess_abc123",
  "job_id": "ROK-E016AC"
}
```

**Apply response `201`:**
```json
{
  "success": true,
  "message": "Application for 'Backend Engineer' at 'Acme Corp' successfully recorded.",
  "application": {
    "application_id": "app_a1b2c3d4",
    "session_id": "sess_abc123",
    "job_id": "ROK-E016AC",
    "title": "Backend Engineer",
    "company": "Acme Corp",
    "location": "Remote",
    "source_url": "https://remoteok.com/...",
    "applied_date": "2026-10-25T08:45:00Z",
    "status": "recorded"
  },
  "is_duplicate": false
}
```

**Error responses:**

| Code | Reason |
|---|---|
| `404` | Job ID not found in dataset |
| `409` | Already applied to this job in this session |

---

## Agent System

### Orchestrator (`app/agents/orchestrator.py`)

The central reasoning engine. Classifies user intent, extracts structured parameters, and dispatches to the correct specialized tool.

**Intent classification (deterministic regex):**

| Intent | Example messages |
|---|---|
| `APPLY` | "apply to job 1", "apply to ROK-123" |
| `APPLICATION_STATUS` | "show my applications", "what did I apply for" |
| `FILTER_JOBS` | "remote React jobs", "junior Python roles in Berlin" |
| `RECOMMEND_JOBS` | "recommend jobs for me", "find suitable roles" |
| `GENERAL_CHAT` | "hello", "what can you do?" |

**Job resolution (for APPLY intent):**
1. By direct Job ID pattern (e.g., `ROK-E016AC`)
2. By list index (`"job 2"`, `"#3"`)
3. By ordinal words (`"first"`, `"second"`)
4. By company name mention
5. Returns clarification question if ambiguous

### Resume Parser (`app/agents/tools/resume_parser.py`)

Extracts structured profile data from uploaded resumes:
- **PDF** via PyMuPDF (fitz) — handles multi-page, encrypted detection
- **DOCX** via python-docx — handles paragraphs and tables
- Delegates to LLM for structuring, with full heuristic fallback

### Job Matcher (`app/agents/tools/job_matcher.py`)

Transparent deterministic scoring algorithm (0–100):

| Component | Weight | Method |
|---|---|---|
| Skill overlap | **60%** | Resume skills ∩ (job skills + description) |
| Title relevance | **20%** | Direct match + synonym group matching |
| Experience fit | **10%** | Numeric range matching with deficit penalty |
| Location preference | **10%** | Remote preference + city match |

Final score is clamped to **[10, 99]** to avoid false certainty at extremes.

### Application Manager (`app/agents/tools/application_manager.py`)

- Validates `job_id` exists in the dataset before recording
- Prevents duplicate applications (per session or globally)
- Uses atomic JSON writes via `StorageService`
- Initial status is always `"recorded"`

---

## LLM Service

**Supported providers** (set `LLM_PROVIDER` in `.env`):

| Provider | Key Variable | Notes |
|---|---|---|
| `gemini` | `GEMINI_API_KEY` | Default. Uses `gemini-1.5-flash` |
| `openai` | `OPENAI_API_KEY` | Uses GPT-4o-mini by default |
| `anthropic` | `ANTHROPIC_API_KEY` | Uses Claude 3 Haiku by default |
| `groq` | `GROQ_API_KEY` | Uses Llama 3.1 8B Instant |

**Fallback chain:** configured provider → other providers with keys → heuristic offline engine.

**Security measures:**
- Resume text is wrapped in `<untrusted_candidate_resume>` tags to defend against prompt injection
- API keys are never logged or returned to clients
- `DEBUG=false` prevents stack traces from leaking in production

---

## Storage Architecture

All persistence uses **atomic JSON writes** via `tempfile.NamedTemporaryFile` + `os.replace`, guaranteeing no corruption on crash.

| File | Purpose | Format |
|---|---|---|
| `data/jobs.json` | 1,800+ scraped job listings | `{ "metadata": {...}, "jobs": [...] }` |
| `data/applications.json` | Application records | JSON array |
| `data/sessions.json` | Session state + resume profiles | JSON object keyed by session ID |

**Thread safety:** `threading.RLock` guards all read/write operations within a single process.

> **Production note:** For multi-worker deployments (Gunicorn, Kubernetes), replace the JSON store with PostgreSQL + SQLAlchemy. The `StorageService` interface is designed for easy swap.

---

## Test Suite

Run all tests:

```bash
cd backend
pytest -v
```

Run a specific file:

```bash
pytest tests/test_job_matcher_extended.py -v
```

Run with coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

### Test inventory

| File | Tests | What it covers |
|---|---|---|
| `test_api_endpoints.py` | 8 | All REST endpoints, error codes, field presence |
| `test_application_manager.py` | 3 | Apply, duplicate prevention, session isolation |
| `test_job_matcher.py` | 6 | Scoring range, filters, ranking, explanations |
| `test_job_matcher_extended.py` | 20 | Location/skill/title/experience score edge cases, combined filters, fallback |
| `test_llm_and_orchestrator.py` | 5 | LLM fallback, mocked output, intent classification, orchestrate flows |
| `test_llm_service_extended.py` | 14 | JSON extraction, heuristic parser, Anthropic, fallback chain, chat reply |
| `test_new_endpoints.py` | 8 | `/api/jobs/stats` structure and `/api/jobs/{job_id}` lookup |
| `test_orchestrator_extended.py` | 17 | All intents, filter extraction, resolve logic, full orchestrate flows |
| `test_resume_parser.py` | 7 | PDF/DOCX extraction, validation, error handling |
| `test_storage_session.py` | 4 | Atomic writes, JSON recovery, session bounds |

**Total: 90+ tests**

---

## Project Structure

```
backend/
├── app/
│   ├── agents/
│   │   ├── orchestrator.py          # Central intent router
│   │   └── tools/
│   │       ├── resume_parser.py     # PDF/DOCX → ResumeProfile
│   │       ├── job_matcher.py       # Deterministic scoring engine
│   │       ├── application_manager.py  # Apply + dedup
│   │       └── application_status.py   # History retrieval
│   ├── api/
│   │   └── routes/
│   │       ├── health.py
│   │       ├── resume.py
│   │       ├── chat.py
│   │       ├── jobs.py
│   │       ├── job_stats.py         # NEW: /stats + /{job_id}
│   │       └── applications.py
│   ├── models/
│   │   └── schemas.py               # All Pydantic models
│   ├── services/
│   │   ├── llm_service.py           # Multi-provider LLM + offline fallback
│   │   ├── session_service.py       # Session lifecycle
│   │   └── storage_service.py       # Atomic JSON persistence
│   ├── utils/
│   │   ├── errors.py                # Custom exceptions + handlers
│   │   └── file_validation.py       # Upload validation
│   ├── config.py                    # Pydantic settings
│   └── main.py                      # FastAPI app factory
├── data/
│   ├── jobs.json                    # 1,800+ scraped job listings
│   ├── applications.json            # Application records (auto-created)
│   └── sessions.json                # Session store (auto-created)
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── test_api_endpoints.py
│   ├── test_application_manager.py
│   ├── test_job_matcher.py
│   ├── test_job_matcher_extended.py
│   ├── test_llm_and_orchestrator.py
│   ├── test_llm_service_extended.py
│   ├── test_new_endpoints.py
│   ├── test_orchestrator_extended.py
│   ├── test_resume_parser.py
│   └── test_storage_session.py
├── scripts/
│   └── scrape_jobs.py               # Job scraper (Remoteok, Arbeitnow)
├── .env.example
├── main.py                          # Uvicorn entrypoint alias
├── pytest.ini
├── requirements.txt
└── start.bat
```
