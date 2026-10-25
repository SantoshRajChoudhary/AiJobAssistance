"""
Pydantic Schemas for the Hidani Tech AI Job Assistant.
Defines strict, validated data structures for:
  - Resume Profile and nested models (experience, education, projects, contact)
  - Jobs and Job Search filters
  - Applications and Application status
  - Chat Sessions and Orchestrator messages
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, model_validator


# ─── Resume Nested Models ─────────────────────────────────────────────────────

class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None


class ExperienceItem(BaseModel):
    role: str
    company: str
    duration: Optional[str] = None
    description: Optional[str] = None


class EducationItem(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None


class ProjectItem(BaseModel):
    name: str
    tech_stack: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class ResumeProfile(BaseModel):
    """
    Candidate resume profile schema as required by the assessment specification.
    Guarantees null or empty defaults when information is absent.
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    
    # Additional metadata for backwards compatibility with the React UI
    contact: Optional[ContactInfo] = None
    total_experience_years: Optional[float] = 0.0
    summary: Optional[str] = None

    @model_validator(mode="after")
    def sync_contact(self):
        """Keep top-level email/phone and nested contact in sync."""
        if self.contact is None:
            self.contact = ContactInfo(
                email=self.email,
                phone=self.phone,
            )
        else:
            if not self.email and self.contact.email:
                self.email = self.contact.email
            if not self.phone and self.contact.phone:
                self.phone = self.contact.phone
            if not self.contact.email and self.email:
                self.contact.email = self.email
            if not self.contact.phone and self.phone:
                self.contact.phone = self.phone
        return self


# ─── Job Models ───────────────────────────────────────────────────────────────

class JobItem(BaseModel):
    job_id: str
    title: str
    company: str
    location: str = "Remote"
    experience_required: str = "0-2 years"
    skills: List[str] = Field(default_factory=list)
    description: str
    source_url: str
    source_link: Optional[str] = None
    employment_type: Optional[str] = "Full-time"
    remote_type: Optional[str] = "Remote"
    posted_date: Optional[str] = None
    source_name: Optional[str] = None
    scraped_at: Optional[str] = None

    # Ranking & Explanation fields
    match_score: Optional[int] = None
    match_reason: Optional[str] = None

    @model_validator(mode="after")
    def sync_links(self):
        if not self.source_link and self.source_url:
            self.source_link = self.source_url
        elif not self.source_url and self.source_link:
            self.source_url = self.source_link
        return self


class JobListResponse(BaseModel):
    total: int
    page: int
    limit: int
    jobs: List[JobItem]


# ─── Application Models ───────────────────────────────────────────────────────

class ApplyRequest(BaseModel):
    session_id: Optional[str] = None
    job_id: str
    # Frontend may pass these metadata fields directly:
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    source_link: Optional[str] = None
    source_url: Optional[str] = None


class ApplicationRecord(BaseModel):
    application_id: str
    session_id: Optional[str] = None
    job_id: str
    title: str
    company: str
    location: str
    source_url: str
    source_link: Optional[str] = None
    applied_date: str
    status: str = "recorded"  # Documented initial status


class ApplyResponse(BaseModel):
    success: bool
    message: str
    application: ApplicationRecord
    is_duplicate: bool = False


# ─── Resume Upload Response ───────────────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    profile: ResumeProfile
    # Alias 'resume' for direct frontend consumption
    resume: Optional[ResumeProfile] = None
    session_id: str
    recommended_jobs: List[JobItem] = Field(default_factory=list)
    message: str = "Resume parsed successfully."

    @model_validator(mode="after")
    def sync_resume(self):
        if self.resume is None:
            self.resume = self.profile
        return self


# ─── Chat & Orchestrator Models ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    resume: Optional[Dict[str, Any]] = None
    applied_jobs: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    recommended_jobs: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    type: str  # 'text', 'job_recommendations', 'application_status', 'clarification'
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    session_id: str
    # Convenience fields for existing React frontend:
    reply: Optional[str] = None
    text: Optional[str] = None
    recommended_jobs: Optional[List[JobItem]] = None
    applied_job: Optional[ApplicationRecord] = None

    @model_validator(mode="after")
    def sync_frontend_fields(self):
        if self.reply is None:
            self.reply = self.message
        if self.text is None:
            self.text = self.message
        return self


# ─── Health Model ─────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    jobs_indexed: int
    dataset_available: bool
    version: str = "1.0.0"
    storage_type: str = "JSON File Storage (Persistent Atomic)"
