"""
Orchestrator Agent Bridge.
Bridges legacy calls to the new Orchestrator agent.
Removes hardcoded Groq API keys.
"""

from typing import Dict, Any, Optional, List
from app.agents.orchestrator import orchestrator


async def orchestrate(
    message: str,
    resume: Optional[Dict[str, Any]] = None,
    applied_jobs: Optional[List[Dict[str, Any]]] = None,
    recommended_jobs: Optional[List[Dict[str, Any]]] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    response = await orchestrator.orchestrate(
        message=message,
        session_id=session_id,
        client_resume=resume,
        client_applied=applied_jobs,
        client_recommended=recommended_jobs,
    )
    return response.model_dump()
