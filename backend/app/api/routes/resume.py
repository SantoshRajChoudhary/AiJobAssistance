"""
Resume upload and parsing routes.
Supports both /api/resume/upload (assessment spec) and /api/parse-resume (React UI compatibility).
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, status
from fastapi.responses import JSONResponse

from app.utils.file_validation import validate_resume_file
from app.agents.tools.resume_parser import parse_resume_document
from app.agents.tools.job_matcher import match_and_rank_jobs
from app.services.session_service import session_service
from app.models.schemas import ResumeUploadResponse

router = APIRouter(tags=["Resume"])


async def handle_resume_upload(file: UploadFile, session_id: Optional[str] = None):
    """Core logic for validating, extracting, and matching uploaded resumes."""
    contents = await file.read()
    ext = validate_resume_file(
        filename=file.filename or "",
        content_type=file.content_type or "",
        file_bytes=contents,
    )

    # Extract text and structure resume profile
    profile = await parse_resume_document(contents, ext)

    # Associate with session
    session_id, _ = session_service.get_or_create_session(session_id)
    session_service.set_resume_profile(session_id, profile.model_dump())

    # Generate initial personalized job recommendations
    recommended_jobs = match_and_rank_jobs(
        resume=profile.model_dump(),
        filters={"remote": True},
        limit=10,
    )

    response_payload = ResumeUploadResponse(
        profile=profile,
        session_id=session_id,
        recommended_jobs=recommended_jobs,
        message="Resume parsed successfully.",
    )
    return response_payload


@router.post(
    "/api/resume/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and parse a PDF or DOCX resume (Assessment Spec)",
)
async def upload_resume(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    return await handle_resume_upload(file, session_id)


@router.post(
    "/api/parse-resume",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and parse resume (React Frontend Compatible Alias)",
)
async def parse_resume_alias(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    return await handle_resume_upload(file, session_id)
