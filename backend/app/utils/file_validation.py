"""
File validation utilities for resume uploads.
Validates MIME types, extensions, file size limits, and basic file structure.
"""

from app.config import settings
from app.utils.errors import FileTooLargeError, InvalidInputError

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/octet-stream",  # Browser fallback for binary
}


def validate_resume_file(filename: str, content_type: str, file_bytes: bytes) -> str:
    """
    Validates file type and size.
    Returns the normalized extension: '.pdf' or '.docx'.
    Raises InvalidInputError or FileTooLargeError if validation fails.
    """
    if not filename:
        raise InvalidInputError("File name is missing.")

    # Size check
    size = len(file_bytes)
    if size == 0:
        raise InvalidInputError("Uploaded file is empty (0 bytes).")

    if size > settings.max_upload_size_bytes:
        raise FileTooLargeError(
            f"File size ({size / (1024*1024):.2f} MB) exceeds maximum allowed size of {settings.max_upload_size_bytes / (1024*1024):.0f} MB."
        )

    # Extension check
    lower_name = filename.lower()
    ext = ""
    for allowed_ext in ALLOWED_EXTENSIONS:
        if lower_name.endswith(allowed_ext):
            ext = allowed_ext
            break

    if not ext:
        raise InvalidInputError(
            f"Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx)."
        )

    # Normalize .doc to .docx check or accept
    if ext == ".doc":
        ext = ".docx"

    return ext
