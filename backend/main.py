"""
Hidani Tech - AI Job Chat Assistant
Root FastAPI application runner & backward-compatibility bridge.

Exposes `app` from `app.main` so running `uvicorn main:app` from within the backend directory works directly.
"""

import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app
from app.agents.tools.resume_parser import parse_resume_document as parse_resume
from app.agents.tools.job_matcher import match_and_rank_jobs as match_jobs
from app.services.storage_service import storage_service
from app.agents.tools.application_manager import record_application
from app.agents.tools.application_status import get_applications_for_session
from app.agents.orchestrator import orchestrator

# Backwards compatible alias helpers
def load_jobs():
    return storage_service.load_jobs()

def reload_jobs():
    return storage_service.reload_jobs()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
