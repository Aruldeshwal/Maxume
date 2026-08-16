"""Incremental Git Watcher & Project Synchronizer for Maxume SSOT."""

import os
import re
import subprocess
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from app.database import Database, db as default_db

# Markdown URL regex for [Label](https://...) and standalone https?://
MD_LINK_REGEX = re.compile(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)')
RAW_URL_REGEX = re.compile(r'(https?://[^\s\)]+)')

def is_git_repository(repo_path: str) -> bool:
    """Check if the provided directory is inside a Git working tree."""
    if not os.path.exists(repo_path):
        return False
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        return res.returncode == 0 and res.stdout.strip() == "true"
    except Exception:
        return False

def get_directory_commit_hash(repo_path: str, subfolder_rel_path: str = ".") -> Optional[str]:
    """Retrieve the latest commit hash for a given subfolder within a Git repository."""
    try:
        res = subprocess.run(
            ["git", "log", "-1", '--format=%H', "--", subfolder_rel_path],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0:
            commit_hash = res.stdout.strip()
            return commit_hash if commit_hash else None
        return None
    except Exception:
        return None

def extract_live_demo_url(markdown_text: str) -> Optional[str]:
    """Extract live demo or deployment URL from markdown content."""
    # First look for links explicitly labeled 'demo', 'live', 'website', 'app', 'deploy'
    md_matches = MD_LINK_REGEX.findall(markdown_text)
    for label, url in md_matches:
        label_lower = label.lower()
        if any(keyword in label_lower for keyword in ["demo", "live", "app", "site", "web", "deploy"]):
            return url
    
    # Fallback to any markdown hyperlink found
    if md_matches:
        return md_matches[0][1]
    
    # Fallback to raw URL
    raw_matches = RAW_URL_REGEX.findall(markdown_text)
    if raw_matches:
        return raw_matches[0]
    
    return None

def collect_project_markdown(project_dir: str) -> str:
    """Aggregate all markdown files within a project subdirectory."""
    contents = []
    for root, _, files in os.walk(project_dir):
        for f in files:
            if f.endswith(".md") and not f.endswith("_summary.md"):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
                        contents.append(f"### File: {f}\n" + fp.read())
                except Exception:
                    continue
    return "\n\n".join(contents)

class GitWatcher:
    def __init__(self, database: Database = default_db):
        self.db = database

    def scan_project_folder(
        self,
        projects_root: str,
        summarizer_callback: Optional[Callable[[str, str], str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan /projects master directory, perform incremental Git commit comparison,
        and update SQLite SSOT accordingly.
        """
        results = []
        if not os.path.exists(projects_root):
            return results

        is_git = is_git_repository(projects_root)
        
        # Scan immediate subdirectories
        entries = sorted(os.listdir(projects_root))
        for entry in entries:
            full_path = os.path.join(projects_root, entry)
            if not os.path.isdir(full_path) or entry.startswith("."):
                continue

            rel_path = entry
            # Check if this subfolder is its own separate Git repo
            if is_git_repository(full_path):
                current_commit = get_directory_commit_hash(full_path, ".")
            elif is_git:
                current_commit = get_directory_commit_hash(projects_root, rel_path)
            else:
                current_commit = None
            
            # Check DB record
            normalized_path = os.path.abspath(full_path).replace("\\", "/")
            existing = self.db.get_project_by_path(normalized_path)
            
            needs_sync = False
            if existing is None:
                needs_sync = True
            elif current_commit is not None and existing.get("last_commit_hash") != current_commit:
                needs_sync = True
            elif current_commit is None and not existing.get("summary_markdown"):
                needs_sync = True

            demo_url = existing.get("live_demo_url") if existing else None
            summary = existing.get("summary_markdown") if existing else None

            if needs_sync:
                raw_markdown = collect_project_markdown(full_path)
                extracted_url = extract_live_demo_url(raw_markdown)
                if extracted_url:
                    demo_url = extracted_url

                if summarizer_callback and raw_markdown:
                    summary = summarizer_callback(entry, raw_markdown)
                elif raw_markdown:
                    summary = f"# {entry}\n\nAuto-indexed project logs.\n\n{raw_markdown[:500]}..."
                else:
                    summary = f"# {entry}\n\nNo markdown documentation found."

                # Upsert to SQLite SSOT
                self.db.upsert_project(
                    directory_path=normalized_path,
                    directory_name=entry,
                    last_commit_hash=current_commit,
                    summary_markdown=summary,
                    live_demo_url=demo_url
                )

                # Write [dir_name]_summary.md to project folder
                summary_file_path = os.path.join(full_path, f"{entry}_summary.md")
                try:
                    with open(summary_file_path, "w", encoding="utf-8") as sf:
                        sf.write(summary or "")
                except Exception:
                    pass

                results.append({
                    "directory_name": entry,
                    "directory_path": normalized_path,
                    "commit_hash": current_commit,
                    "status": "synchronized",
                    "live_demo_url": demo_url
                })
            else:
                results.append({
                    "directory_name": entry,
                    "directory_path": normalized_path,
                    "commit_hash": current_commit,
                    "status": "up_to_date",
                    "live_demo_url": demo_url
                })

        return results
