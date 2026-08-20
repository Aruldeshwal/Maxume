"""FastAPI Application Entrypoint for Maxume Python Sidecar."""

import os
import sys
import asyncio
import logging
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("maxume")

# Ensure sidecar directory is on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sidecar_dir = os.path.dirname(current_dir)
if sidecar_dir not in sys.path:
    sys.path.insert(0, sidecar_dir)

# Multi-location .env loader for standalone desktop and dev environments
candidate_env_paths = [
    os.path.join(os.getcwd(), ".env"),
    os.path.join(os.getcwd(), "sidecar", ".env"),
    os.path.join(os.path.dirname(sys.executable), ".env"),
    os.path.join(os.path.dirname(sys.executable), "sidecar", ".env"),
    os.path.join(sidecar_dir, ".env"),
    os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Maxume", ".env"),
    r"C:\Users\aruld\OneDrive\Desktop\Maxume\sidecar\.env"
]
for ep in candidate_env_paths:
    if os.path.exists(ep):
        load_dotenv(ep)

from app.database import db
from app.git_watcher import GitWatcher
from app.docx_engine import DocxEngine, resolve_master_template
from app.ollama_manager import ollama_manager
from app.company_research import research_company, ResearchBrief
from app.employee_lookup import lookup_company_employees
from app.gemini_service import gemini_service
from app.groq_service import groq_service
from app.image_optimizer import compress_jd_screenshot
from app.github_sync import sync_github_profile_repositories
from app.skills_engine import extract_authentic_candidate_skills

app = FastAPI(
    title="Maxume Python Sidecar",
    description="Local-First Hybrid AI Assistant Backend",
    version="0.1.0"
)

# CORS config to allow Tauri frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "http://127.0.0.1:1420", "tauri://localhost", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Request Schemas ---

class ProjectUpsertRequest(BaseModel):
    directory_path: str
    directory_name: str
    last_commit_hash: Optional[str] = None
    summary_markdown: Optional[str] = None
    live_demo_url: Optional[str] = None

class ApplicationCreateRequest(BaseModel):
    company_name: str
    role_title: str
    jd_raw_text: Optional[str] = None
    compressed_image_path: Optional[str] = None
    output_folder_path: Optional[str] = None
    personalization_status: Optional[str] = "Not Attempted"

class DocxRebuildRequest(BaseModel):
    template_path: str
    output_path: str
    projects: List[Dict[str, Any]]
    skills: Union[List[str], Dict[str, List[str]]]
    hyperlink_color: Optional[str] = "990000"

class CompanyResearchRequest(BaseModel):
    company_name: str
    company_url: Optional[str] = None
    company_domain: Optional[str] = None
    recency_days: Optional[int] = 90
    max_signals: Optional[int] = 5

class OptimizeApplicationRequest(BaseModel):
    company_name: Optional[str] = ""
    role_title: Optional[str] = ""
    company_url: Optional[str] = None
    company_domain: Optional[str] = None
    jd_raw_text: Optional[str] = None
    screenshot_path: Optional[str] = None
    screenshot_base64: Optional[str] = None
    screenshots_base64: Optional[List[str]] = None
    screenshot_paths: Optional[List[str]] = None
    master_resume_path: Optional[str] = None
    output_dir: Optional[str] = None
    personalization_enabled: Optional[bool] = True

# --- Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint for Tauri sidecar readiness."""
    return {
        "status": "healthy",
        "service": "maxume-sidecar",
        "version": "0.1.0",
        "database": os.path.exists(db.db_path)
    }

@app.get("/api/config")
async def get_config():
    """Returns configured paths and environment defaults."""
    return {
        "projects_dir": os.environ.get("PROJECTS_DIR_PATH", "./projects"),
        "output_dir": os.environ.get("OUTPUT_DIR_PATH", "./output"),
        "master_resume_path": os.environ.get("MASTER_RESUME_PATH", "Master_Resume.docx")
    }

class OpenFolderRequest(BaseModel):
    path: str

@app.post("/api/open-folder")
async def open_folder_in_os(payload: OpenFolderRequest):
    """Opens a folder or file in Windows File Explorer."""
    import subprocess
    target_path = os.path.abspath(payload.path)
    if os.path.exists(target_path):
        try:
            if os.path.isdir(target_path):
                subprocess.Popen(["explorer", target_path])
            else:
                subprocess.Popen(["explorer", "/select,", target_path])
            return {"status": "ok", "opened_path": target_path}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail=f"Path '{target_path}' does not exist.")

@app.get("/api/quotas")
async def get_api_quotas():
    """Returns real-time daily quota usage for Gemini and Groq."""
    return db.get_quotas()

class ProjectVisibilityRequest(BaseModel):
    is_hidden: Optional[int] = None

# Projects & SSOT
@app.get("/api/projects")
async def get_projects(include_hidden: bool = Query(True)):
    """Returns list of tracked projects in SSOT database."""
    return {"projects": db.list_projects(include_hidden=include_hidden)}

@app.post("/api/projects/{project_id}/visibility")
async def toggle_project_visibility(project_id: int, payload: Optional[ProjectVisibilityRequest] = None):
    """Toggles or updates whether a project is hidden from resumes."""
    is_hidden = payload.is_hidden if payload else None
    success = db.toggle_project_visibility(project_id, is_hidden=is_hidden)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "ok", "project_id": project_id}

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int):
    """Permanently removes a project record from SQLite SSOT."""
    success = db.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "ok", "deleted_project_id": project_id}

class ProjectUpdateRequest(BaseModel):
    tech_stack: Optional[str] = None
    timeline: Optional[str] = None
    live_demo_url: Optional[str] = None
    bullets: Optional[List[str]] = None
    summary_markdown: Optional[str] = None

@app.put("/api/projects/{project_id}")
async def update_project(project_id: int, payload: ProjectUpdateRequest):
    """Updates a project's custom tech stack, timeline, live demo URL, and bullets."""
    success = db.update_project_custom_fields(
        project_id=project_id,
        tech_stack=payload.tech_stack,
        timeline=payload.timeline,
        live_demo_url=payload.live_demo_url,
        bullets=payload.bullets,
        summary_markdown=payload.summary_markdown
    )
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "ok", "project_id": project_id}

@app.post("/api/projects")
async def upsert_project(payload: ProjectUpsertRequest):
    """Upsert project details to local SQLite database."""
    project_id = db.upsert_project(
        directory_path=payload.directory_path,
        directory_name=payload.directory_name,
        last_commit_hash=payload.last_commit_hash,
        summary_markdown=payload.summary_markdown,
        live_demo_url=payload.live_demo_url
    )
    return {"status": "ok", "project_id": project_id}

class ProjectSyncRequest(BaseModel):
    projects_dir: Optional[str] = None

@app.post("/api/projects/sync")
async def sync_projects(payload: Optional[ProjectSyncRequest] = None):
    """Triggers Incremental Git Watcher sync across projects folder."""
    target_dir = None
    if payload and payload.projects_dir and payload.projects_dir.strip():
        target_dir = payload.projects_dir.strip()
    else:
        target_dir = os.environ.get("PROJECTS_DIR_PATH", "./projects")

    # Clean up quotes if user pasted path with quotes e.g. "C:\Path"
    target_dir = target_dir.strip("\"'")
    target_dir = os.path.expanduser(target_dir)

    watcher = GitWatcher(database=db)
    results = watcher.scan_project_folder(target_dir)
    return {"status": "ok", "scanned_directory": target_dir, "results": results}

class GitHubProfileSyncRequest(BaseModel):
    username: str
    token: Optional[str] = None
    force_resync: Optional[bool] = False

@app.post("/api/projects/github-sync")
@app.post("/api/github/sync")
async def sync_github_profile(payload: GitHubProfileSyncRequest):
    """Fetches public repositories from GitHub profile, extracts README docs & live URLs, and saves to SSOT."""
    try:
        results = await asyncio.to_thread(
            sync_github_profile_repositories,
            payload.username,
            payload.token,
            db,
            payload.force_resync or False
        )
        return {
            "status": "ok",
            "username": payload.username,
            "total_synced": len(results),
            "results": results,
            "projects": results
        }
    except Exception as e:
        logger.error(f"GitHub sync error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

# Applications History Logs
@app.get("/api/applications")
async def get_applications():
    """Returns all application logs."""
    return {"applications": db.list_applications()}

@app.post("/api/applications")
async def create_application(payload: ApplicationCreateRequest):
    """Creates a new job application record in the database."""
    app_id = db.create_application(
        company_name=payload.company_name,
        role_title=payload.role_title,
        status="Draft",
        jd_raw_text=payload.jd_raw_text,
        compressed_image_path=payload.compressed_image_path,
        output_folder_path=payload.output_folder_path,
        personalization_status=payload.personalization_status or "Not Attempted"
    )
    return {"status": "ok", "application_id": app_id}

@app.get("/api/applications/{app_id}")
async def get_application(app_id: int):
    """Retrieves full application profile with contacts and signals."""
    app_data = db.get_application(app_id)
    if not app_data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    contacts = db.list_networking_contacts(app_id)
    signals = db.list_company_signals(app_id)
    return {
        "application": app_data,
        "networking_contacts": contacts,
        "company_research_signals": signals
    }

class EmployeeLookupRequest(BaseModel):
    company_name: str
    company_url: Optional[str] = None
    company_domain: Optional[str] = None
    num_results: Optional[int] = 4

@app.post("/api/employees/lookup")
async def lookup_employees_endpoint(payload: EmployeeLookupRequest):
    """Direct lookup endpoint for real company employees and Hunter.io email synthesis."""
    contacts = await lookup_company_employees(
        company_name=payload.company_name,
        company_url=payload.company_url,
        company_domain=payload.company_domain,
        num_results=payload.num_results or 4
    )
    return {"status": "ok", "contacts": contacts}

# Docx Engine Rebuilding
@app.post("/api/docx/rebuild")
async def rebuild_docx(payload: DocxRebuildRequest):
    """Rebuilds resume DOCX with paragraph cloning, link embedding, and single-page guardrails."""
    try:
        out_path = DocxEngine.rebuild_resume(
            template_path=payload.template_path,
            output_path=payload.output_path,
            projects=payload.projects,
            skills=payload.skills,
            hyperlink_color=payload.hyperlink_color or "990000"
        )
        return {"status": "ok", "output_path": out_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX rebuilding failed: {str(e)}")

# Ollama Discovery & VRAM Guardrails
@app.get("/api/ollama/status")
async def get_ollama_status():
    """Returns reachability status for local Ollama server."""
    return ollama_manager.get_status()

@app.get("/api/ollama/models")
async def list_ollama_models(
    num_ctx: int = Query(2048, description="Context window size"),
    budget_gb: float = Query(5.2, description="VRAM budget in GB")
):
    """Lists local models with dynamic VRAM guardrail calculations."""
    return ollama_manager.list_models(num_ctx=num_ctx, budget_gb=budget_gb)

# Company Signal Research
@app.post("/api/research")
async def execute_company_research(payload: CompanyResearchRequest):
    """Executes 5-stage company research pipeline with 3-stage hallucination guard."""
    brief = research_company(
        company_name=payload.company_name,
        company_url=payload.company_url,
        recency_days=payload.recency_days or 90,
        max_signals=payload.max_signals or 5
    )
    return brief.model_dump()

# Full End-to-End Application Optimization Pipeline
@app.post("/api/optimize")
async def optimize_application(payload: OptimizeApplicationRequest):
    """
    Executes full hybrid optimization pipeline:
    1. Screenshot OCR / JD analysis
    2. Project selection & Gemini reranking
    3. Company signal research (grounded)
    4. Resume DOCX compilation
    5. Groq cover letter, referral, and email generation
    6. Networking employee discovery
    7. Persistence to local SQLite DB and /output folder
    """
    company_clean = (payload.company_name or "").strip()
    role_clean = (payload.role_title or "").strip()
    
    # 1. JD text extraction & Multi-Screenshot OCR
    jd_text = payload.jd_raw_text or ""
    compressed_img = None
    
    # Collect all base64 screenshots (single or list)
    b64_list = []
    if payload.screenshots_base64:
        b64_list.extend(payload.screenshots_base64)
    elif payload.screenshot_base64:
        b64_list.append(payload.screenshot_base64)

    temp_paths = []
    if b64_list:
        try:
            import base64
            import tempfile
            for b64_data in b64_list:
                raw_b64 = b64_data.split(",")[1] if "," in b64_data else b64_data
                img_bytes = base64.b64decode(raw_b64)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                    tf.write(img_bytes)
                    temp_paths.append(tf.name)
            
            if temp_paths:
                compressed_img, _, _ = compress_jd_screenshot(temp_paths[0])
                ocr_res = await gemini_service.ocr_screenshot_jd(temp_paths)
                jd_text = ocr_res.get("raw_text") or jd_text
                if not company_clean and ocr_res.get("company_name"):
                    company_clean = ocr_res["company_name"]
                if not role_clean and ocr_res.get("role_title"):
                    role_clean = ocr_res["role_title"]
        except Exception:
            pass
    elif payload.screenshot_paths:
        try:
            ocr_res = await gemini_service.ocr_screenshot_jd(payload.screenshot_paths)
            jd_text = ocr_res.get("raw_text") or jd_text
            if not company_clean and ocr_res.get("company_name"):
                company_clean = ocr_res["company_name"]
            if not role_clean and ocr_res.get("role_title"):
                role_clean = ocr_res["role_title"]
        except Exception:
            pass
    elif payload.screenshot_path and os.path.exists(payload.screenshot_path):
        try:
            compressed_img, _, _ = compress_jd_screenshot(payload.screenshot_path)
            ocr_res = await gemini_service.ocr_screenshot_jd(payload.screenshot_path)
            jd_text = ocr_res.get("raw_text") or jd_text
            if not company_clean and ocr_res.get("company_name"):
                company_clean = ocr_res["company_name"]
            if not role_clean and ocr_res.get("role_title"):
                role_clean = ocr_res["role_title"]
        except Exception:
            pass

    company_clean = company_clean or "Target Company"
    role_clean = role_clean or "Software Engineer"

    # 2. Company Technical Dossier & Grounded Research
    research_brief = None
    personalization_status = "Not Attempted"
    if payload.personalization_enabled:
        research_brief = research_company(
            company_name=company_clean,
            company_url=payload.company_url,
            company_domain=payload.company_domain,
            jd_text=jd_text,
            recency_days=90,
            max_signals=5
        )
        personalization_status = "Found" if research_brief.status == "FOUND" else "None Found"

    # 3. Pull projects and rerank (excluding hidden projects)
    all_projects = db.list_projects(include_hidden=False)
    ranked_projects = await gemini_service.rerank_projects_for_jd(
        jd_text=jd_text,
        candidate_projects=all_projects,
        top_k=4
    )

    # 4. Resume DOCX Rebuilding
    template_path = resolve_master_template(payload.master_resume_path)

    # Resolve output directory
    raw_out = payload.output_dir or os.environ.get("OUTPUT_DIR_PATH")
    if not raw_out or raw_out == "./output":
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, "OneDrive", "Desktop", "Job-Content"),
            os.path.join(home, "Desktop", "Job-Content"),
            os.path.join(os.environ.get("APPDATA", ""), "Maxume", "Job-Content"),
        ]
        out_root = next((c for c in candidates if os.path.exists(os.path.dirname(c))), os.path.abspath("./output"))
    else:
        out_root = os.path.abspath(raw_out)

    company_slug = "".join(c for c in company_clean if c.isalnum() or c in ("-", "_")).lower() or "company"
    app_output_dir = os.path.join(out_root, company_slug)
    os.makedirs(app_output_dir, exist_ok=True)

    compiled_resume_path = os.path.join(app_output_dir, f"{company_slug}_Resume.docx")
    try:
        authentic_skills = extract_authentic_candidate_skills(
            projects=all_projects,
            jd_text=jd_text
        )
        compiled_resume_path = DocxEngine.rebuild_resume(
            template_path=template_path,
            output_path=compiled_resume_path,
            projects=ranked_projects,
            skills=authentic_skills
        )
        logger.info(f"Resume successfully compiled to: {compiled_resume_path}")
    except Exception as docx_err:
        logger.error(f"DocxEngine rebuild failed: {docx_err}", exc_info=True)

    # 5. Extract bullet highlights for creative copy
    bullet_highlights = []
    for p in ranked_projects:
        for b in p.get("bullets", [])[:2]:
            bullet_highlights.append(b)

    # 6. Groq Creative Generation
    cover_letter = await groq_service.generate_cover_letter(
        company_name=company_clean,
        role_title=role_clean,
        resume_bullets=bullet_highlights,
        research_brief=research_brief
    )

    outreach_email = await groq_service.generate_application_email(
        company_name=company_clean,
        role_title=role_clean,
        resume_bullets=bullet_highlights,
        research_brief=research_brief
    )

    # Write copy files to output folder with file-lock resilience
    cover_letter_file = os.path.join(app_output_dir, f"{company_slug}_CoverLetter.txt")
    email_file = os.path.join(app_output_dir, f"{company_slug}_Email.txt")
    try:
        with open(cover_letter_file, "w", encoding="utf-8") as f:
            f.write(cover_letter)
    except (PermissionError, IOError):
        cover_letter_file = os.path.join(app_output_dir, f"{company_slug}_CoverLetter_new.txt")
        try:
            with open(cover_letter_file, "w", encoding="utf-8") as f:
                f.write(cover_letter)
        except Exception:
            pass

    try:
        with open(email_file, "w", encoding="utf-8") as f:
            f.write(outreach_email)
    except (PermissionError, IOError):
        email_file = os.path.join(app_output_dir, f"{company_slug}_Email_new.txt")
        try:
            with open(email_file, "w", encoding="utf-8") as f:
                f.write(outreach_email)
        except Exception:
            pass

    # 7. Verified Employee Networking Discovery ($0 search cost)
    from app.networking_engine import search_verified_company_employees, generate_batched_200char_pitches
    raw_contacts = await asyncio.to_thread(
        search_verified_company_employees,
        company_clean,
        role_clean
    )

    # 8. Single Batched Groq Request for <= 200 Character Outreach Notes
    contacts = await asyncio.to_thread(
        generate_batched_200char_pitches,
        raw_contacts,
        company_clean,
        role_clean,
        bullet_highlights
    )

    # 9. SQLite Database Persistence
    app_id = db.create_application(
        company_name=company_clean,
        role_title=role_clean,
        status="Draft",
        jd_raw_text=jd_text,
        compressed_image_path=compressed_img,
        output_folder_path=app_output_dir,
        personalization_status=personalization_status
    )
    if app_id and app_id > 0:
        db.clear_application_children(app_id)

    # Persist signals
    if research_brief and research_brief.signals:
        for s in research_brief.signals:
            db.add_company_signal(
                application_id=app_id,
                signal_type=s.signal_type,
                headline=s.headline,
                source_url=s.source_url,
                source_tier=s.source_tier,
                published_at=s.published_at,
                used_in_output=1,
                guard_check_passed=1 if s.guard_check_passed else 0
            )

    # Persist networking contacts with generated 200-char referral drafts
    saved_contacts = []
    for c in contacts:
        cid = db.add_networking_contact(
            application_id=app_id,
            employee_name=c["name"],
            employee_tagline=f"[{c.get('archetype', 'Team')}] {c.get('tagline', '')}",
            profile_url=c["profile_url"],
            referral_message_draft=c.get("referral_pitch"),
            referral_status="Not Contacted",
            email_primary=c.get("primary_email"),
            email_alternatives=c.get("alternative_emails"),
            google_dork_url=c.get("google_dork_url"),
            github_search_url=c.get("github_search_url"),
            twitter_search_url=c.get("twitter_search_url"),
        )
        saved_contacts.append({
            **c,
            "id": cid,
            "employee_name": c["name"],
            "employee_tagline": c.get("tagline"),
            "referral_message_draft": c.get("referral_pitch")
        })

    return {
        "status": "ok",
        "application_id": app_id,
        "output_folder": app_output_dir,
        "resume_path": compiled_resume_path,
        "cover_letter_path": cover_letter_file,
        "email_path": email_file,
        "cover_letter": cover_letter,
        "outreach_email": outreach_email,
        "personalization_status": personalization_status,
        "research_brief": research_brief.model_dump() if research_brief else None,
        "networking_contacts": saved_contacts,
        "ranked_projects": ranked_projects
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
