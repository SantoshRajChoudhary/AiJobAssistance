"""
Resume Parser Agent Bridge.
Bridges legacy calls to the new PyMuPDF/python-docx resume parser tool.
Removes any hardcoded API keys.
"""

from app.agents.tools.resume_parser import parse_resume_document
from app.utils.file_validation import validate_resume_file


async def parse_resume(file_bytes: bytes, filename: str) -> dict:
    ext = validate_resume_file(filename=filename, content_type="", file_bytes=file_bytes)
    profile = await parse_resume_document(file_bytes, ext)
    return profile.model_dump()
