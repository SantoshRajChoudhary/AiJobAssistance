"""
Session Management and Memory Service.

Responsibilities:
  - Generates opaque cryptographically unique session IDs (e.g. 'sess_<uuid4>').
  - Stores and retrieves candidate resume profiles by session ID.
  - Maintains bounded conversation history per session (e.g. up to 20 recent messages).
  - Persists session context to disk (via storage_service) so context survives service restarts.
  - Ensures complete session isolation: user A cannot access user B's profile or history.
"""

import uuid
from typing import Dict, Any, Optional, List
from app.services.storage_service import storage_service

MAX_CONVERSATION_HISTORY = 20


class SessionService:
    def __init__(self):
        pass

    def create_session(self) -> str:
        """Generates a new opaque session identifier."""
        session_id = f"sess_{uuid.uuid4().hex}"
        session_data = {
            "session_id": session_id,
            "resume_profile": None,
            "history": [],
            "filters": {},
        }
        storage_service.save_session(session_id, session_data)
        return session_id

    def get_or_create_session(self, session_id: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        """
        Retrieves existing session or creates a new one if not provided or not found.
        Returns (session_id, session_data).
        """
        if not session_id or not session_id.strip():
            new_id = self.create_session()
            return new_id, storage_service.get_session(new_id) or {}

        existing = storage_service.get_session(session_id)
        if existing:
            return session_id, existing

        # Create session with the requested ID if valid string
        session_data = {
            "session_id": session_id,
            "resume_profile": None,
            "history": [],
            "filters": {},
        }
        storage_service.save_session(session_id, session_data)
        return session_id, session_data

    def set_resume_profile(self, session_id: str, profile: Dict[str, Any]):
        """Associates a parsed resume profile with the given session."""
        _, session_data = self.get_or_create_session(session_id)
        session_data["resume_profile"] = profile
        storage_service.save_session(session_id, session_data)

    def get_resume_profile(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves resume profile for the session."""
        session_data = storage_service.get_session(session_id)
        if session_data:
            return session_data.get("resume_profile")
        return None

    def append_message(self, session_id: str, role: str, content: str):
        """Appends a message to bounded conversation history."""
        _, session_data = self.get_or_create_session(session_id)
        history: List[Dict[str, str]] = session_data.get("history", [])
        history.append({"role": role, "content": content})

        # Keep history bounded to avoid unbounded context growth
        if len(history) > MAX_CONVERSATION_HISTORY:
            history = history[-MAX_CONVERSATION_HISTORY:]

        session_data["history"] = history
        storage_service.save_session(session_id, session_data)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Returns bounded conversation history for session."""
        session_data = storage_service.get_session(session_id)
        if session_data:
            return session_data.get("history", [])
        return []


session_service = SessionService()
