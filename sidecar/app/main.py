"""FastAPI Application Entrypoint for Maxume Python Sidecar."""

import os
import sys
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure sidecar directory is on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sidecar_dir = os.path.dirname(current_dir)
if sidecar_dir not in sys.path:
    sys.path.insert(0, sidecar_dir)

load_dotenv(os.path.join(sidecar_dir, ".env"))

from app.database import db
from app.git_watcher import GitWatcher
from app.docx_engine import DocxEngine
from app.ollama_manager import ollama_manager

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

# Projects & SSOT
@app.get("/api/projects")
async def get_projects():
    """Returns list of tracked projects in SSOT database."""
    return {"projects": db.list_projects()}

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

@app.post("/api/projects/sync")
async def sync_projects(projects_dir: Optional[str] = None):
    """Triggers Incremental Git Watcher sync across projects folder."""
    target_dir = projects_dir or os.environ.get("PROJECTS_DIR_PATH", "./projects")
    watcher = GitWatcher(database=db)
    results = watcher.scan_project_folder(target_dir)
    return {"status": "ok", "scanned_directory": target_dir, "results": results}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
