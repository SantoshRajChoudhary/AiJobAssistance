"""
Health check route.
Provides service health status and dataset availability without leaking secrets.
"""

from fastapi import APIRouter
from app.services.storage_service import storage_service
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/api/health", response_model=HealthResponse)
def get_health():
    jobs = storage_service.load_jobs()
    indexed_count = len(jobs)
    return HealthResponse(
        status="ok",
        jobs_indexed=indexed_count,
        dataset_available=(indexed_count > 0),
        version="1.0.0",
        storage_type="JSON File Storage (Persistent Atomic)",
    )
