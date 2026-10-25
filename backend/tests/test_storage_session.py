"""
Tests for Storage Service and Session Service.
Covers:
  - Atomic write behavior
  - Malformed JSON recovery
  - Session isolation and bounded history
  - Survival of session state
"""

import os
import tempfile
import pytest
from app.services.storage_service import StorageService
from app.services.session_service import SessionService


def test_atomic_write_creates_valid_file(tmp_path):
    storage = StorageService()
    test_file = os.path.join(tmp_path, "atomic_test.json")

    data = {"test": "value", "items": [1, 2, 3]}
    storage._atomic_write_json(test_file, data)

    assert os.path.exists(test_file)
    read_back = storage._safe_read_json(test_file, dict)
    assert read_back == data


def test_malformed_json_recovery(tmp_path):
    storage = StorageService()
    corrupt_file = os.path.join(tmp_path, "corrupt.json")

    # Write corrupt data
    with open(corrupt_file, "w", encoding="utf-8") as f:
        f.write("{ invalid json content ][")

    # Safe read should not crash, but recover with default factory
    recovered = storage._safe_read_json(corrupt_file, list)
    assert isinstance(recovered, list)
    assert len(recovered) == 0


def test_session_bounded_history():
    sessions = SessionService()
    sess_id = sessions.create_session()

    # Append 30 messages (limit is 20)
    for i in range(30):
        sessions.append_message(sess_id, "user", f"Message {i}")

    history = sessions.get_history(sess_id)
    assert len(history) <= 20
    assert history[-1]["content"] == "Message 29"


def test_session_resume_profile_persistence():
    sessions = SessionService()
    sess_id = sessions.create_session()

    profile_data = {
        "name": "Alice Developer",
        "email": "alice@example.com",
        "skills": ["Python", "FastAPI"],
    }
    sessions.set_resume_profile(sess_id, profile_data)

    retrieved = sessions.get_resume_profile(sess_id)
    assert retrieved is not None
    assert retrieved["name"] == "Alice Developer"
    assert "FastAPI" in retrieved["skills"]
