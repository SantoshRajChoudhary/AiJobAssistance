"""
Orchestrator Agent.
Central conversational intelligence for the AI Job Assistant.

Responsibilities:
  - Classifies natural-language user intent into specialized actions:
      * APPLY               → application_manager
      * APPLICATION_STATUS  → application_status
      * FILTER_JOBS         → job_matcher with specific filters
      * RECOMMEND_JOBS      → job_matcher with candidate resume
      * GENERAL_CHAT        → conversational guidance
  - Resolves job identifiers (sequential index from chat or stable job_id).
  - Handles ambiguous requests by asking clarifying questions.
  - Maintains conversation history and session-scoped profile context.
  - Security constraints: Never executes code, never trusts unvalidated job IDs.
"""

import re
import logging
from typing import Dict, Any, Optional, List

from app.models.schemas import ChatResponse, JobItem, ApplicationRecord
from app.services.session_service import session_service
from app.services.storage_service import storage_service
from app.services.llm_service import llm_service
from app.agents.tools.job_matcher import match_and_rank_jobs
from app.agents.tools.application_manager import record_application
from app.agents.tools.application_status import get_applications_for_session, format_application_history_text
from app.utils.errors import JobNotFoundError, DuplicateApplicationError

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self):
        pass

    def classify_intent(self, message: str) -> str:
        """Rule-guided deterministic intent classification with LLM-grade accuracy."""
        lower = message.lower().strip()

        # 1. Apply intent
        if re.search(r"\bapply\b", lower):
            return "APPLY"

        # 2. Application status / history intent
        if re.search(r"(show|list|view|check|see|my|track).*(applied|applications|status|history)", lower):
            return "APPLICATION_STATUS"
        if "what did i apply" in lower or "where did i apply" in lower or "my jobs" in lower:
            return "APPLICATION_STATUS"

        # 3. Filtering jobs by criteria (remote, skills, location, experience)
        if re.search(r"\b(remote|hybrid|onsite|location|in\s+[a-z]+)\b", lower) and any(w in lower for w in ["job", "role", "position", "work", "show", "find"]):
            return "FILTER_JOBS"
        if re.search(r"\b(react|python|node|java|typescript|frontend|backend|fullstack|devops|data|sde)\b", lower):
            return "FILTER_JOBS"
        if re.search(r"\b(junior|entry|fresher|intern|senior|lead)\b", lower):
            return "FILTER_JOBS"

        # 4. Job recommendation intent
        if any(kw in lower for kw in ["recommend", "match", "suggest", "find jobs", "best jobs", "suitable", "roles for me"]):
            return "RECOMMEND_JOBS"

        return "GENERAL_CHAT"

    def extract_filters(self, message: str) -> Dict[str, Any]:
        """Extracts structured search parameters from natural language queries."""
        lower = message.lower()
        filters = {}

        # Remote check
        if "remote" in lower:
            filters["remote"] = True

        # Location extraction
        loc_match = re.search(r"\bin\s+([A-Za-z\s]+?)(?:\s+jobs|\s+roles|\s+positions|\s*$|\.|\,)", message)
        if loc_match:
            cand = loc_match.group(1).strip()
            if cand.lower() not in {"the", "my", "this", "our"}:
                filters["location"] = cand

        # Known skills
        skills_pool = [
            "python", "react", "javascript", "typescript", "node", "fastapi",
            "django", "vue", "angular", "java", "spring", "golang", "go",
            "docker", "kubernetes", "aws", "sql", "graphql", "machine learning"
        ]
        for skill in skills_pool:
            if re.search(rf"\b{re.escape(skill)}\b", lower):
                filters["skill"] = skill.capitalize()
                break

        # Title roles
        titles_pool = ["frontend", "backend", "full stack", "fullstack", "devops", "data scientist", "intern", "sde", "engineer"]
        for title in titles_pool:
            if title in lower:
                filters["title"] = title
                break

        return filters

    def resolve_target_job(
        self,
        message: str,
        session_id: str,
        active_recommended: List[Dict[str, Any]],
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Attempts to find which job the user is referring to.
        Returns (job_id, clarification_prompt).
        """
        # 1. By direct job ID pattern (e.g. 'JOB-1042', 'ROK-E016AC', 'ARB-123')
        id_match = re.search(r"\b([A-Z]{3}-[A-Z0-9]+|JOB-[A-Z0-9]+)\b", message, re.IGNORECASE)
        if id_match:
            job_id = id_match.group(1).upper()
            if storage_service.get_job_by_id(job_id):
                return job_id, None
            return None, f"I could not find a job with ID `{job_id}` in our dataset. Please verify the job ID."

        # 2. By list index (e.g. 'job 1', 'role #2', 'apply to first one')
        num_match = re.search(r"(?:job|role|position|#|number)?\s*(\d+)", message, re.IGNORECASE)
        if num_match:
            idx = int(num_match.group(1)) - 1
            if 0 <= idx < len(active_recommended):
                chosen_job = active_recommended[idx]
                return chosen_job.get("job_id"), None
            return None, f"You requested job #{idx+1}, but only {len(active_recommended)} recommendations are currently displayed. Which job would you like to apply to?"

        # 3. By ordinal words: 'first', 'second', 'third'
        ordinals = {"first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4}
        for word, idx in ordinals.items():
            if word in message.lower():
                if 0 <= idx < len(active_recommended):
                    return active_recommended[idx].get("job_id"), None

        # 4. By company name mention in recommended jobs
        lower_msg = message.lower()
        for rec in active_recommended:
            comp = rec.get("company", "").lower()
            if comp and comp in lower_msg:
                return rec.get("job_id"), None

        # Ambiguous request
        if not active_recommended:
            return None, "Which job would you like to apply to? Please provide the Job ID (e.g. `ROK-123`) or upload a resume to view recommendations."
        
        job_options = ", ".join([f"#{i+1} ({j.get('title')} at {j.get('company')})" for i, j in enumerate(active_recommended[:3])])
        return None, f"Which job would you like to apply to? You can say *'apply to job 1'* or specify a job from the list: {job_options}."

    async def orchestrate(
        self,
        message: str,
        session_id: Optional[str] = None,
        client_resume: Optional[Dict[str, Any]] = None,
        client_applied: Optional[List[Dict[str, Any]]] = None,
        client_recommended: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatResponse:
        """
        Main execution workflow: classifies intent, executes tool, returns structured ChatResponse.
        """
        session_id, session_data = session_service.get_or_create_session(session_id)

        # Merge profile: prioritize client-passed profile or stored session profile
        resume_profile = client_resume or session_data.get("resume_profile")
        if client_resume and not session_data.get("resume_profile"):
            session_service.set_resume_profile(session_id, client_resume)

        # Log user query in bounded memory
        session_service.append_message(session_id, "user", message)

        intent = self.classify_intent(message)
        logger.info(f"Session {session_id} classified intent: {intent} for message: '{message}'")

        # ─── ACTION 1: APPLY TO JOB ───────────────────────────────────────────
        if intent == "APPLY":
            active_recs = client_recommended or []
            job_id, clarification = self.resolve_target_job(message, session_id, active_recs)

            if clarification:
                session_service.append_message(session_id, "assistant", clarification)
                return ChatResponse(
                    type="clarification",
                    message=clarification,
                    session_id=session_id,
                )

            try:
                apply_res = record_application(job_id=job_id, session_id=session_id)
                app_record = apply_res.application
                success_text = (
                    f"Application recorded for **{app_record.title}** at **{app_record.company}** (`{app_record.job_id}`).\n"
                    f"Status: **{app_record.status.capitalize()}** (Tracked locally)."
                )
                session_service.append_message(session_id, "assistant", success_text)
                return ChatResponse(
                    type="application_success",
                    message=success_text,
                    session_id=session_id,
                    data={"application": app_record.model_dump()},
                    applied_job=app_record,
                )
            except DuplicateApplicationError as e:
                dup_text = f"Duplicate Application: {e.message}"
                session_service.append_message(session_id, "assistant", dup_text)
                return ChatResponse(
                    type="text",
                    message=dup_text,
                    session_id=session_id,
                )
            except JobNotFoundError as e:
                not_found_text = f"Error: {e.message}"
                session_service.append_message(session_id, "assistant", not_found_text)
                return ChatResponse(
                    type="text",
                    message=not_found_text,
                    session_id=session_id,
                )

        # ─── ACTION 2: APPLICATION STATUS ────────────────────────────────────
        elif intent == "APPLICATION_STATUS":
            apps = get_applications_for_session(session_id=session_id)
            history_text = format_application_history_text(apps)
            session_service.append_message(session_id, "assistant", history_text)
            return ChatResponse(
                type="application_status",
                message=history_text,
                session_id=session_id,
                data={"applications": [a.model_dump() for a in apps], "total": len(apps)},
            )

        # ─── ACTION 3: FILTER JOBS ───────────────────────────────────────────
        elif intent == "FILTER_JOBS":
            filters = self.extract_filters(message)
            jobs = match_and_rank_jobs(resume=resume_profile, filters=filters, limit=8)

            filter_descriptions = []
            if filters.get("remote"):
                filter_descriptions.append("remote")
            if filters.get("skill"):
                filter_descriptions.append(f"skills in {filters['skill']}")
            if filters.get("location"):
                filter_descriptions.append(f"located in {filters['location']}")
            if filters.get("title"):
                filter_descriptions.append(f"role '{filters['title']}'")

            filter_str = ", ".join(filter_descriptions) if filter_descriptions else "your criteria"
            summary_text = f"Found {len(jobs)} jobs matching {filter_str}:"
            session_service.append_message(session_id, "assistant", summary_text)

            return ChatResponse(
                type="job_recommendations",
                message=summary_text,
                session_id=session_id,
                data={"jobs": [j.model_dump() for j in jobs], "total": len(jobs), "filters": filters},
                recommended_jobs=jobs,
            )

        # ─── ACTION 4: RECOMMEND JOBS ────────────────────────────────────────
        elif intent == "RECOMMEND_JOBS":
            jobs = match_and_rank_jobs(resume=resume_profile, filters={"remote": True}, limit=8)
            if resume_profile and resume_profile.get("skills"):
                reply_text = f"Based on your profile as a {resume_profile.get('designation', 'Engineer')}, here are the best matching positions:"
            else:
                reply_text = "Here are our top recommended tech listings. To receive personalized match scores, please upload your resume!"

            session_service.append_message(session_id, "assistant", reply_text)
            return ChatResponse(
                type="job_recommendations",
                message=reply_text,
                session_id=session_id,
                data={"jobs": [j.model_dump() for j in jobs], "total": len(jobs)},
                recommended_jobs=jobs,
            )

        # ─── ACTION 5: GENERAL CHAT ──────────────────────────────────────────
        else:
            context = "You are the Hidani Tech AI Job Assistant. You help users parse resumes, find matching jobs, and apply."
            reply = await llm_service.generate_chat_reply(message, context)
            session_service.append_message(session_id, "assistant", reply)
            return ChatResponse(
                type="text",
                message=reply,
                session_id=session_id,
                data={},
            )


orchestrator = Orchestrator()
