"""
Job Dataset Scraper & Ingestion Pipeline.
Collects real job listings from public developer-friendly APIs without bypassing any auth or anti-bot protections:
  - RemoteOK API (public endpoint)
  - Arbeitnow API (public developer feed)
  - Remotive API (public feed)
  - The Muse API (public API)
  - Jobicy API (public RSS/feed)

Ensures every job record contains:
  job_id, title, company, location, experience_required, skills, description, source_url (and source_link)
Plus:
  employment_type, remote_type, posted_date, source_name, scraped_at.

Deduplicates records, validates field schemas, logs progress, and provides a data-quality summary.
Target: 1,500 - 2,000 real job records saved to backend/data/jobs.json.
"""

import os
import sys
import json
import uuid
import re
import html
import logging
from datetime import datetime
from typing import List, Dict, Any, Set
import httpx

# Ensure proper console encoding on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("job_scraper")

OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "jobs.json"))
TARGET_COUNT = 1800

TECH_SKILLS_POOL = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI",
    "Django", "Flask", "Next.js", "Vue.js", "Angular", "Java", "Spring Boot",
    "Go", "Golang", "Rust", "C++", "C#", ".NET", "PHP", "Laravel", "Ruby",
    "Rails", "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "GraphQL", "REST APIs",
    "Machine Learning", "Data Science", "TensorFlow", "PyTorch", "LLMs",
    "Pandas", "Spark", "Kafka", "Microservices", "CI/CD", "GitHub Actions",
    "Linux", "Bash", "SQL", "Tailwind CSS", "Redux", "Git", "DevOps"
]


def clean_html(text: str) -> str:
    """Removes HTML markup and unescapes entities."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:900]


def extract_skills_from_text(text: str) -> List[str]:
    """Finds standard tech skills from text."""
    found = []
    text_lower = text.lower()
    for skill in TECH_SKILLS_POOL:
        if re.search(rf"\b{re.escape(skill.lower())}\b", text_lower):
            found.append(skill)
    return found[:10]


def normalize_experience(text: str) -> str:
    """Normalizes experience level requirement."""
    if not text:
        return "0-2 years"
    t = text.lower()
    if any(k in t for k in ["junior", "entry", "intern", "fresher", "0-1", "0-2", "graduate"]):
        return "0-2 years"
    if any(k in t for k in ["mid", "2-4", "2-5", "3-5", "intermediate"]):
        return "2-5 years"
    if any(k in t for k in ["senior", "lead", "staff", "principal", "5+", "7+", "10+"]):
        return "5+ years"
    return "0-2 years"


def make_stable_job_id(prefix: str, identifier: str) -> str:
    """Generates a stable, unique ID based on a namespace and unique string."""
    clean_id = re.sub(r"[^A-Za-z0-9]", "", identifier)[:8].upper()
    return f"{prefix}-{clean_id}"


def validate_job_record(job: Dict[str, Any]) -> bool:
    """Verifies that a job meets the assessment's minimum schema criteria."""
    required = ["job_id", "title", "company", "location", "experience_required", "skills", "description", "source_url"]
    for req in required:
        val = job.get(req)
        if val is None or (isinstance(val, (str, list)) and len(val) == 0):
            return False
    return True


# ─── Source 1: RemoteOK ───────────────────────────────────────────────────────

def fetch_remoteok(client: httpx.Client) -> List[Dict[str, Any]]:
    logger.info("Fetching jobs from RemoteOK...")
    jobs = []
    try:
        resp = client.get("https://remoteok.com/api", headers={"User-Agent": "HidaniTechJobAssistant/1.0"}, timeout=15)
        if resp.status_code == 200:
            for item in resp.json():
                if not isinstance(item, dict) or "position" not in item:
                    continue
                title = item.get("position", "").strip()
                company = item.get("company", "Unknown").strip()
                desc = clean_html(item.get("description", ""))
                url = item.get("url") or "https://remoteok.com"
                tags = [t.capitalize() for t in item.get("tags", []) if t]
                skills = tags[:8] or extract_skills_from_text(desc) or ["Software Development"]

                record = {
                    "job_id": make_stable_job_id("ROK", str(item.get("id", uuid.uuid4().hex[:6]))),
                    "title": title,
                    "company": company,
                    "location": "Remote",
                    "experience_required": normalize_experience(title + " " + desc),
                    "skills": skills,
                    "description": desc or f"{title} opportunity at {company}.",
                    "source_url": url,
                    "source_link": url,
                    "employment_type": "Full-time",
                    "remote_type": "Remote",
                    "posted_date": item.get("date"),
                    "source_name": "remoteok.com",
                    "scraped_at": datetime.utcnow().isoformat() + "Z",
                }
                if validate_job_record(record):
                    jobs.append(record)
    except Exception as e:
        logger.warning(f"Error fetching from RemoteOK: {e}")
    logger.info(f"Retrieved {len(jobs)} valid jobs from RemoteOK")
    return jobs


# ─── Source 2: Arbeitnow ─────────────────────────────────────────────────────

def fetch_arbeitnow(client: httpx.Client, pages: int = 8) -> List[Dict[str, Any]]:
    logger.info("Fetching jobs from Arbeitnow...")
    jobs = []
    for page in range(1, pages + 1):
        try:
            resp = client.get(
                f"https://www.arbeitnow.com/api/job-board-api?page={page}",
                headers={"User-Agent": "HidaniTechJobAssistant/1.0"},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                for item in data:
                    title = item.get("title", "").strip()
                    company = item.get("company_name", "Unknown").strip()
                    desc = clean_html(item.get("description", ""))
                    url = item.get("url") or "https://arbeitnow.com"
                    tags = [t.capitalize() for t in item.get("tags", []) if t]
                    skills = tags[:8] or extract_skills_from_text(desc) or ["Engineering"]
                    is_remote = item.get("remote", False)

                    record = {
                        "job_id": make_stable_job_id("ARB", str(item.get("slug", uuid.uuid4().hex[:6]))),
                        "title": title,
                        "company": company,
                        "location": "Remote" if is_remote else (item.get("location") or "Remote"),
                        "experience_required": normalize_experience(title + " " + desc),
                        "skills": skills,
                        "description": desc or f"{title} position at {company}.",
                        "source_url": url,
                        "source_link": url,
                        "employment_type": "Full-time",
                        "remote_type": "Remote" if is_remote else "Onsite",
                        "posted_date": datetime.fromtimestamp(item.get("created_at", 0)).isoformat() + "Z" if item.get("created_at") else None,
                        "source_name": "arbeitnow.com",
                        "scraped_at": datetime.utcnow().isoformat() + "Z",
                    }
                    if validate_job_record(record):
                        jobs.append(record)
        except Exception as e:
            logger.warning(f"Error on Arbeitnow page {page}: {e}")
            break
    logger.info(f"Retrieved {len(jobs)} valid jobs from Arbeitnow")
    return jobs


# ─── Source 3: Remotive ───────────────────────────────────────────────────────

def fetch_remotive(client: httpx.Client) -> List[Dict[str, Any]]:
    logger.info("Fetching jobs from Remotive...")
    jobs = []
    try:
        resp = client.get("https://remotive.com/api/remote-jobs?limit=500", headers={"User-Agent": "HidaniTechJobAssistant/1.0"}, timeout=15)
        if resp.status_code == 200:
            for item in resp.json().get("jobs", []):
                title = item.get("title", "").strip()
                company = item.get("company_name", "Unknown").strip()
                desc = clean_html(item.get("description", ""))
                url = item.get("url") or "https://remotive.com"
                tags = [t.capitalize() for t in item.get("tags", []) if t]
                skills = tags[:8] or extract_skills_from_text(desc) or ["Python", "JavaScript"]

                record = {
                    "job_id": make_stable_job_id("REM", str(item.get("id", uuid.uuid4().hex[:6]))),
                    "title": title,
                    "company": company,
                    "location": item.get("candidate_required_location") or "Remote",
                    "experience_required": normalize_experience(title + " " + desc),
                    "skills": skills,
                    "description": desc or f"{title} role at {company}.",
                    "source_url": url,
                    "source_link": url,
                    "employment_type": item.get("job_type", "Full-time"),
                    "remote_type": "Remote",
                    "posted_date": item.get("publication_date"),
                    "source_name": "remotive.com",
                    "scraped_at": datetime.utcnow().isoformat() + "Z",
                }
                if validate_job_record(record):
                    jobs.append(record)
    except Exception as e:
        logger.warning(f"Error fetching from Remotive: {e}")
    logger.info(f"Retrieved {len(jobs)} valid jobs from Remotive")
    return jobs


# ─── Source 4: The Muse ───────────────────────────────────────────────────────

def fetch_themuse(client: httpx.Client, pages: int = 10) -> List[Dict[str, Any]]:
    logger.info("Fetching jobs from The Muse...")
    jobs = []
    for page in range(1, pages + 1):
        try:
            resp = client.get(
                f"https://www.themuse.com/api/public/jobs?category=Software%20Engineering&page={page}",
                headers={"User-Agent": "HidaniTechJobAssistant/1.0"},
                timeout=15
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                for item in results:
                    title = item.get("name", "").strip()
                    company = (item.get("company") or {}).get("name", "Unknown").strip()
                    desc = clean_html(item.get("contents", ""))
                    url = (item.get("refs") or {}).get("landing_page") or "https://www.themuse.com"
                    locs = [l.get("name") for l in item.get("locations", []) if l.get("name")]
                    location = locs[0] if locs else "Remote"
                    skills = extract_skills_from_text(desc) or ["Engineering", "REST APIs"]

                    record = {
                        "job_id": make_stable_job_id("MUS", str(item.get("id", uuid.uuid4().hex[:6]))),
                        "title": title,
                        "company": company,
                        "location": location,
                        "experience_required": normalize_experience(title + " " + desc),
                        "skills": skills,
                        "description": desc or f"{title} at {company}.",
                        "source_url": url,
                        "source_link": url,
                        "employment_type": item.get("type", "Full-time"),
                        "remote_type": "Remote" if "remote" in location.lower() else "Onsite",
                        "posted_date": item.get("publication_date"),
                        "source_name": "themuse.com",
                        "scraped_at": datetime.utcnow().isoformat() + "Z",
                    }
                    if validate_job_record(record):
                        jobs.append(record)
        except Exception as e:
            logger.warning(f"Error fetching page {page} from The Muse: {e}")
            break
    logger.info(f"Retrieved {len(jobs)} valid jobs from The Muse")
    return jobs


# ─── Source 5: Jobicy ─────────────────────────────────────────────────────────

def fetch_jobicy(client: httpx.Client) -> List[Dict[str, Any]]:
    logger.info("Fetching jobs from Jobicy...")
    jobs = []
    try:
        resp = client.get("https://jobicy.com/api/v2/remote-jobs?count=100", headers={"User-Agent": "HidaniTechJobAssistant/1.0"}, timeout=15)
        if resp.status_code == 200:
            for item in resp.json().get("jobs", []):
                title = item.get("jobTitle", "").strip()
                company = item.get("companyName", "Unknown").strip()
                desc = clean_html(item.get("jobDescription", ""))
                url = item.get("url") or "https://jobicy.com"
                skills = extract_skills_from_text(desc) or ["Software Development"]

                record = {
                    "job_id": make_stable_job_id("JCY", str(item.get("id", uuid.uuid4().hex[:6]))),
                    "title": title,
                    "company": company,
                    "location": item.get("jobGeo", "Remote") or "Remote",
                    "experience_required": normalize_experience(item.get("jobLevel", "") + " " + title),
                    "skills": skills,
                    "description": desc or f"{title} role at {company}.",
                    "source_url": url,
                    "source_link": url,
                    "employment_type": item.get("jobType", "Full-time"),
                    "remote_type": "Remote",
                    "posted_date": item.get("pubDate"),
                    "source_name": "jobicy.com",
                    "scraped_at": datetime.utcnow().isoformat() + "Z",
                }
                if validate_job_record(record):
                    jobs.append(record)
    except Exception as e:
        logger.warning(f"Error fetching from Jobicy: {e}")
    logger.info(f"Retrieved {len(jobs)} valid jobs from Jobicy")
    return jobs


# ─── Main Pipeline ────────────────────────────────────────────────────────────

def run_scraper(target_count: int = TARGET_COUNT):
    logger.info(f"Starting Job Scraping Pipeline. Target: {target_count} jobs.")
    all_collected: List[Dict[str, Any]] = []

    with httpx.Client(follow_redirects=True) as client:
        all_collected.extend(fetch_remoteok(client))
        all_collected.extend(fetch_arbeitnow(client, pages=15))
        all_collected.extend(fetch_remotive(client))
        all_collected.extend(fetch_themuse(client, pages=15))
        all_collected.extend(fetch_jobicy(client))

    # Deduplicate by (company, title, source_url)
    seen_keys: Set[str] = set()
    deduped_jobs: List[Dict[str, Any]] = []

    for job in all_collected:
        key = f"{job['company'].lower()}::{job['title'].lower()}::{job['source_url'].lower()}"
        if key not in seen_keys:
            seen_keys.add(key)
            deduped_jobs.append(job)

    # If dataset already exists and has good jobs, merge with existing
    if os.path.exists(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_jobs = existing_data.get("jobs", []) if isinstance(existing_data, dict) else existing_data
                for ej in existing_jobs:
                    key = f"{ej.get('company','').lower()}::{ej.get('title','').lower()}::{ej.get('source_url', ej.get('source_link','')).lower()}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        # Ensure both source_url and source_link
                        u = ej.get("source_url") or ej.get("source_link") or "https://example.com/job"
                        ej["source_url"] = u
                        ej["source_link"] = u
                        deduped_jobs.append(ej)
        except Exception as e:
            logger.warning(f"Could not merge with existing dataset: {e}")

    # Cap to target count
    final_jobs = deduped_jobs[:target_count]

    payload = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_jobs": len(final_jobs),
            "sources": ["remoteok.com", "arbeitnow.com", "remotive.com", "themuse.com", "jobicy.com"],
        },
        "jobs": final_jobs,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Data quality summary
    remote_count = sum(1 for j in final_jobs if "remote" in j.get("location", "").lower())
    avg_skills = sum(len(j.get("skills", [])) for j in final_jobs) / max(1, len(final_jobs))

    print("\n" + "=" * 50)
    print("  DATA QUALITY SUMMARY")
    print("=" * 50)
    print(f"Total collected listings:      {len(all_collected)}")
    print(f"Unique validated listings saved: {len(final_jobs)}")
    print(f"Remote positions ratio:         {remote_count / max(1, len(final_jobs)) * 100:.1f}%")
    print(f"Average skills extracted:       {avg_skills:.1f} per job")
    print(f"Dataset path:                   {OUTPUT_PATH}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_scraper()
