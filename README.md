# Hidani Tech — AI Job Chat Assistant

> A full-stack AI-powered job assistant: upload your resume, get personalized job recommendations from 1,800+ real listings, and apply — all through a conversational UI.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://reactjs.org)
[![Tests](https://img.shields.io/badge/tests-90%2B%20passing-brightgreen)](./backend/tests)

---

## Features

| Feature | Details |
|---|---|
| 📄 **Resume Parsing** | PDF + DOCX, LLM-structured with deterministic fallback |
| 🔍 **AI Job Matching** | Transparent 0–100 scoring: Skills 60% · Title 20% · Experience 10% · Location 10% |
| 💬 **Conversational UI** | Natural language job search, filtering, and application tracking |
| 🤖 **Multi-Agent System** | Orchestrator → specialized subagents (parser, matcher, application manager) |
| 🔑 **Multi-LLM Support** | Gemini · OpenAI · Anthropic · Groq · Offline heuristic fallback |
| 🛡️ **Security** | Prompt injection defense, no key exposure, session isolation |
| ⚡ **Real Dataset** | 1,800+ scraped jobs from RemoteOK, Arbeitnow |
| 🧪 **Test Coverage** | 90+ automated tests across all layers |

---

## Quick Start

### Backend (Port 8000)

```bash
cd backend
pip install -r requirements.txt

# Copy and fill your LLM API key(s)
cp .env.example .env

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- Dataset stats: [http://localhost:8000/api/jobs/stats](http://localhost:8000/api/jobs/stats)

> **No API key?** The system works fully offline with a built-in heuristic engine.

### Frontend (Port 5173)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health + jobs count |
| `POST` | `/api/resume/upload` | Parse PDF/DOCX resume |
| `POST` | `/api/chat` | Conversational assistant |
| `GET` | `/api/jobs` | Browse + filter job dataset |
| `GET` | `/api/jobs/stats` | Dataset statistics (top skills, companies, remote %) |
| `GET` | `/api/jobs/{job_id}` | Single job lookup |
| `POST` | `/api/applications` | Apply to a job |
| `GET` | `/api/applications` | Application history |

Full API documentation: [backend/README.md](./backend/README.md)

---

## Run Tests

```bash
cd backend
pytest -v
```

All **90+ tests** covering resume parsing, job matching, orchestrator logic, API endpoints, storage, LLM fallback, and new endpoints.

---

## Project Structure

```
AiJobAssistence/
├── backend/              # FastAPI backend (see backend/README.md)
│   ├── app/
│   │   ├── agents/       # Orchestrator + tool agents
│   │   ├── api/          # FastAPI routers
│   │   ├── models/       # Pydantic schemas
│   │   ├── services/     # LLM, session, storage services
│   │   └── utils/        # Error handlers, file validation
│   ├── data/             # Job dataset (jobs.json)
│   ├── tests/            # 90+ automated tests
│   └── requirements.txt
├── frontend/             # React + Vite UI
│   └── src/
│       ├── components/   # Header, ChatInput, JobCard, ResumeCard, etc.
│       └── App.jsx       # Main application
├── .gitignore
└── README.md
```

---

## Tech Stack

**Backend:** FastAPI · Pydantic v2 · PyMuPDF · python-docx · httpx · pytest  
**Frontend:** React 18 · Vite · Vanilla CSS  
**LLM:** Gemini · OpenAI · Anthropic · Groq (configurable)  
**Storage:** Atomic JSON (thread-safe, crash-safe)
