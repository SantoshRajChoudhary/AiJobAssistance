"""
Storage Service for Hidani Tech AI Job Assistant.

Responsibilities:
  - Centralized, thread-safe access to persistent JSON files (jobs.json, applications.json, sessions.json).
  - Atomic write operations using temporary files + os.replace to prevent corrupted data on abrupt stops.
  - Automatic directory and file initialization.
  - Recovery from malformed JSON files.
  - In-memory caching for read performance.

DOCUMENTATION: Storage Architecture & Limitations:
  In this assessment implementation, applications and sessions are stored in JSON files on disk.
  - Concurrency: Thread locks (threading.RLock) guarantee safety across concurrent threads in a single process.
  - Durability: Writes are atomic via temporary file rename (os.replace).
  - Limitations: In multi-worker or multi-container deployments (e.g. Gunicorn with multiple worker processes
    or Kubernetes pods across multiple nodes), file locking does not span separate OS instances without
    distributed locks (e.g. Redis) or a shared database (e.g. PostgreSQL, SQLite WAL mode).
    For scaled production deployments, replace this service with PostgreSQL / SQLAlchemy models.
"""

import os
import json
import logging
import tempfile
import threading
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self._lock = threading.RLock()
        self._jobs_cache: Optional[List[Dict[str, Any]]] = None
        self._ensure_storage_ready()

    def _ensure_storage_ready(self):
        """Ensures storage directory and initial files exist."""
        with self._lock:
            os.makedirs(settings.data_dir, exist_ok=True)

            # Ensure applications.json exists
            if not os.path.exists(settings.applications_file):
                self._atomic_write_json(settings.applications_file, [])

            # Ensure sessions.json exists
            if not os.path.exists(settings.sessions_file):
                self._atomic_write_json(settings.sessions_file, {})

            # Ensure jobs.json exists (even if empty initially)
            if not os.path.exists(settings.jobs_file):
                self._atomic_write_json(settings.jobs_file, {"metadata": {"total_jobs": 0}, "jobs": []})

    def _atomic_write_json(self, file_path: str, data: Any):
        """
        Writes data to a temporary file in the same directory and replaces atomically.
        Guarantees that a crash during writing never leaves a corrupt or half-written file.
        """
        dir_name = os.path.dirname(os.path.abspath(file_path))
        os.makedirs(dir_name, exist_ok=True)

        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            json.dump(data, tf, indent=2, ensure_ascii=False)
            temp_name = tf.name

        try:
            os.replace(temp_name, file_path)
        except Exception as e:
            if os.path.exists(temp_name):
                os.remove(temp_name)
            raise e

    def _safe_read_json(self, file_path: str, default_factory) -> Any:
        """Safely reads a JSON file; handles missing or malformed files with recovery."""
        if not os.path.exists(file_path):
            return default_factory()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return default_factory()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Malformed JSON in {file_path}: {e}. Backing up and resetting.")
            # Backup corrupt file
            backup_path = f"{file_path}.corrupt_{int(os.path.getmtime(file_path))}"
            try:
                os.rename(file_path, backup_path)
            except Exception:
                pass
            fallback = default_factory()
            self._atomic_write_json(file_path, fallback)
            return fallback

    # ─── Jobs Storage ─────────────────────────────────────────────────────────

    def load_jobs(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """Loads and returns all jobs from jobs.json. Caches in memory for fast lookup."""
        with self._lock:
            if self._jobs_cache is not None and not force_reload:
                return self._jobs_cache

            raw = self._safe_read_json(
                settings.jobs_file,
                lambda: {"metadata": {"total_jobs": 0}, "jobs": []}
            )
            if isinstance(raw, dict):
                jobs = raw.get("jobs", [])
            elif isinstance(raw, list):
                jobs = raw
            else:
                jobs = []

            # Normalize jobs: ensure both source_url and source_link exist
            for j in jobs:
                url = j.get("source_url") or j.get("source_link") or ""
                j["source_url"] = url
                j["source_link"] = url

            self._jobs_cache = jobs
            return self._jobs_cache

    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Finds a job by its unique job_id."""
        jobs = self.load_jobs()
        for j in jobs:
            if j.get("job_id", "").strip().lower() == job_id.strip().lower():
                return j
        return None

    def reload_jobs(self) -> int:
        """Clears memory cache and reloads dataset. Returns total jobs indexed."""
        with self._lock:
            self._jobs_cache = None
            jobs = self.load_jobs(force_reload=True)
            return len(jobs)

    # ─── Applications Storage ─────────────────────────────────────────────────

    def get_applications(self, session_id: Optional[str] = None, job_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves stored application records, optionally filtered by session or job_id."""
        with self._lock:
            apps = self._safe_read_json(settings.applications_file, list)
            if not isinstance(apps, list):
                apps = []

            if session_id:
                apps = [a for a in apps if a.get("session_id") == session_id]
            if job_id:
                apps = [a for a in apps if a.get("job_id", "").lower() == job_id.lower()]

            # Sort descending by applied_date
            apps.sort(key=lambda x: x.get("applied_date", ""), reverse=True)
            return apps

    def save_application(self, application_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thread-safely appends a new application record.
        Prevents duplicate applications within the same session.
        """
        with self._lock:
            apps = self._safe_read_json(settings.applications_file, list)
            if not isinstance(apps, list):
                apps = []

            # Check duplicate within session (or globally if session_id is None)
            job_id = application_record.get("job_id")
            session_id = application_record.get("session_id")

            for existing in apps:
                if existing.get("job_id") == job_id:
                    # If sessions match or either is None, flag duplicate
                    if not session_id or not existing.get("session_id") or existing.get("session_id") == session_id:
                        return {
                            "is_duplicate": True,
                            "existing": existing,
                        }

            apps.append(application_record)
            self._atomic_write_json(settings.applications_file, apps)
            return {
                "is_duplicate": False,
                "application": application_record,
            }

    # ─── Sessions Storage ─────────────────────────────────────────────────────

    def load_sessions(self) -> Dict[str, Any]:
        with self._lock:
            sessions = self._safe_read_json(settings.sessions_file, dict)
            return sessions if isinstance(sessions, dict) else {}

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            sessions = self.load_sessions()
            return sessions.get(session_id)

    def save_session(self, session_id: str, session_data: Dict[str, Any]):
        with self._lock:
            sessions = self.load_sessions()
            sessions[session_id] = session_data
            self._atomic_write_json(settings.sessions_file, sessions)


storage_service = StorageService()
