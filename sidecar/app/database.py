"""SQLite Database driver and schema migration manager for Maxume SSOT."""

import sqlite3
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import contextmanager

def _resolve_default_db_path() -> str:
    explicit = os.environ.get("MAXUME_DB_PATH")
    if explicit:
        return explicit
    if os.path.exists("maxume_local.db"):
        return os.path.abspath("maxume_local.db")
    app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
    maxume_dir = os.path.join(app_data, "Maxume")
    os.makedirs(maxume_dir, exist_ok=True)
    return os.path.join(maxume_dir, "maxume_local.db")

DEFAULT_DB_PATH = _resolve_default_db_path()

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- Project Synchronization Signatures (SSOT for Incremental Sync)
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    directory_path TEXT NOT NULL UNIQUE,
    directory_name TEXT NOT NULL,
    last_commit_hash TEXT,
    summary_markdown TEXT,
    live_demo_url TEXT,
    is_hidden INTEGER DEFAULT 0,
    last_synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Job Application Logs
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    role_title TEXT NOT NULL,
    status TEXT CHECK(status IN ('Draft', 'Applied', 'Interviewing', 'Offer', 'Rejected')) DEFAULT 'Draft',
    jd_raw_text TEXT,
    compressed_image_path TEXT,
    output_folder_path TEXT UNIQUE,
    personalization_status TEXT CHECK(personalization_status IN ('Found', 'None Found', 'Not Attempted')) DEFAULT 'Not Attempted',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Scraped LinkedIn Employee Profiles (Associated with Applications)
CREATE TABLE IF NOT EXISTS networking_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER,
    employee_name TEXT NOT NULL,
    employee_tagline TEXT,
    profile_url TEXT NOT NULL,
    referral_message_draft TEXT,
    referral_status TEXT CHECK(referral_status IN ('Not Contacted', 'Message Copied', 'Connected', 'Replied')) DEFAULT 'Not Contacted',
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- Company Research Signals (Personalization Pipeline, see companyresearch.md)
CREATE TABLE IF NOT EXISTS company_research_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER,
    signal_type TEXT CHECK(signal_type IN ('news', 'product_launch', 'funding', 'engineering_blog', 'other')),
    headline TEXT,
    source_url TEXT NOT NULL,
    source_tier INTEGER CHECK(source_tier IN (1, 2, 3)), -- 1=company domain, 2=press, 3=github
    published_at DATETIME,
    used_in_output INTEGER DEFAULT 0,       -- 1 if this signal was actually referenced in generated copy
    guard_check_passed INTEGER DEFAULT 1,   -- 0 if dropped by the hallucination guard's containment check
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
);
"""

class Database:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.init_schema()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    def init_schema(self) -> None:
        """Runs the SQLite schema migration scripts."""
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            # Automatic schema migration for existing databases
            try:
                conn.execute("ALTER TABLE projects ADD COLUMN is_hidden INTEGER DEFAULT 0;")
            except Exception:
                pass

            for col in [
                "ALTER TABLE networking_contacts ADD COLUMN email_primary TEXT;",
                "ALTER TABLE networking_contacts ADD COLUMN email_alternatives TEXT;",
                "ALTER TABLE networking_contacts ADD COLUMN google_dork_url TEXT;",
                "ALTER TABLE networking_contacts ADD COLUMN github_search_url TEXT;",
                "ALTER TABLE networking_contacts ADD COLUMN twitter_search_url TEXT;"
            ]:
                try:
                    conn.execute(col)
                except Exception:
                    pass

            conn.commit()

    def get_project_by_path(self, directory_path: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM projects WHERE directory_path = ?", (directory_path,))
            row = cursor.fetchone()
            return self._enrich_project_metadata(dict(row)) if row else None

    def _enrich_project_metadata(self, proj: Dict[str, Any]) -> Dict[str, Any]:
        """Parses bullets, tech stack, timeline, and live demo out of summary_markdown."""
        summary = proj.get("summary_markdown") or ""
        import re
        
        # 1. Extract bullets under Engineering Highlights
        bullets = []
        in_highlights = False
        for line in summary.splitlines():
            stripped = line.strip()
            if any(h in stripped for h in ["## Engineering Highlights", "## Highlights", "## Key Capabilities", "## Features"]):
                in_highlights = True
                continue
            if in_highlights:
                if stripped.startswith("#") and not stripped.startswith("###"):
                    break
                if stripped.startswith(("-", "*", "•")):
                    clean = re.sub(r'^[-*•\s]+', '', stripped).replace('**', '').strip()
                    if len(clean) > 10 and not clean.startswith("http"):
                        bullets.append(clean)

        proj["bullets"] = bullets

        # 2. Extract tech stack
        m_tech = re.search(r'\*\*Tech Stack\*\*:\s*([^\n]+)', summary)
        if m_tech:
            proj["tech_stack"] = m_tech.group(1).strip()

        # 3. Extract timeline
        m_time = re.search(r'\*\*Timeline\*\*:\s*([^\n]+)', summary)
        if m_time:
            proj["timeline"] = m_time.group(1).strip()
            proj["date"] = m_time.group(1).strip()

        # 4. Extract live demo URL
        m_demo = re.search(r'\*\*Live Demo\*\*:\s*(https?://[^\s\n]+)', summary)
        if m_demo and not proj.get("live_demo_url"):
            proj["live_demo_url"] = m_demo.group(1).strip()

        return proj

    def list_projects(self, include_hidden: bool = True) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if include_hidden:
                cursor = conn.execute("SELECT * FROM projects ORDER BY is_hidden ASC, directory_name ASC")
            else:
                cursor = conn.execute("SELECT * FROM projects WHERE is_hidden = 0 ORDER BY directory_name ASC")
            return [self._enrich_project_metadata(dict(row)) for row in cursor.fetchall()]

    def toggle_project_visibility(self, project_id: int, is_hidden: Optional[int] = None) -> bool:
        """Toggles or sets project visibility (is_hidden: 1 = hidden from resume, 0 = visible)."""
        with self.get_connection() as conn:
            if is_hidden is not None:
                cursor = conn.execute("UPDATE projects SET is_hidden = ? WHERE id = ?", (is_hidden, project_id))
            else:
                cursor = conn.execute(
                    "UPDATE projects SET is_hidden = CASE WHEN is_hidden = 1 THEN 0 ELSE 1 END WHERE id = ?",
                    (project_id,)
                )
            conn.commit()
            return cursor.rowcount > 0

    def delete_project(self, project_id: int) -> bool:
        """Deletes a project permanently from the SSOT database."""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_project_custom_fields(
        self,
        project_id: int,
        tech_stack: Optional[str] = None,
        timeline: Optional[str] = None,
        live_demo_url: Optional[str] = None,
        bullets: Optional[List[str]] = None,
        summary_markdown: Optional[str] = None
    ) -> bool:
        """Allows direct editing of a project's tech stack, timeline, live demo URL, and bullets."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            proj = dict(row)
            curr_summary = proj.get("summary_markdown") or f"# {proj.get('directory_name')}\n"
            
            # If summary_markdown was directly passed, use it
            new_summary = summary_markdown
            if not new_summary:
                # Reconstruct summary_markdown with updated fields
                dir_name = proj.get("directory_name", "Project")
                demo = live_demo_url if live_demo_url is not None else proj.get("live_demo_url")
                
                # Parse existing bullets if not provided
                if bullets is None:
                    parsed = self._enrich_project_metadata(proj)
                    bullets = parsed.get("bullets", [])
                    
                tech = tech_stack if tech_stack is not None else (self._enrich_project_metadata(proj).get("tech_stack") or "Software Engineering")
                time_val = timeline if timeline is not None else (self._enrich_project_metadata(proj).get("timeline") or "2024")
                
                bullets_formatted = "\n".join(f"- {b.strip().lstrip('- ')}" for b in bullets if b.strip())
                new_summary = (
                    f"# {dir_name}\n\n"
                    f"**Tech Stack**: {tech}\n"
                    f"**Timeline**: {time_val}\n"
                    f"**Live Demo**: {demo or 'None'}\n\n"
                    f"## Engineering Highlights\n{bullets_formatted}\n"
                )

            final_demo = live_demo_url if live_demo_url is not None else proj.get("live_demo_url")
            cursor = conn.execute(
                """
                UPDATE projects
                SET summary_markdown = ?,
                    live_demo_url = ?,
                    last_synced_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_summary, final_demo, project_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def upsert_project(
        self,
        directory_path: str,
        directory_name: str,
        last_commit_hash: Optional[str],
        summary_markdown: Optional[str] = None,
        live_demo_url: Optional[str] = None,
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO projects (directory_path, directory_name, last_commit_hash, summary_markdown, live_demo_url, last_synced_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(directory_path) DO UPDATE SET
                    directory_name = excluded.directory_name,
                    last_commit_hash = excluded.last_commit_hash,
                    summary_markdown = COALESCE(excluded.summary_markdown, projects.summary_markdown),
                    live_demo_url = COALESCE(excluded.live_demo_url, projects.live_demo_url),
                    last_synced_at = CURRENT_TIMESTAMP
                RETURNING id;
                """,
                (directory_path, directory_name, last_commit_hash, summary_markdown, live_demo_url),
            )
            row = cursor.fetchone()
            conn.commit()
            return row["id"] if row else -1

    def create_application(
        self,
        company_name: str,
        role_title: str,
        status: str = "Draft",
        jd_raw_text: Optional[str] = None,
        compressed_image_path: Optional[str] = None,
        output_folder_path: Optional[str] = None,
        personalization_status: str = "Not Attempted",
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO applications (
                    company_name, role_title, status, jd_raw_text,
                    compressed_image_path, output_folder_path, personalization_status, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(output_folder_path) DO UPDATE SET
                    company_name = excluded.company_name,
                    role_title = excluded.role_title,
                    status = excluded.status,
                    jd_raw_text = excluded.jd_raw_text,
                    compressed_image_path = excluded.compressed_image_path,
                    personalization_status = excluded.personalization_status,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
                """,
                (company_name, role_title, status, jd_raw_text, compressed_image_path, output_folder_path, personalization_status),
            )
            row = cursor.fetchone()
            conn.commit()
            return row["id"] if row else -1

    def clear_application_children(self, application_id: int) -> None:
        """Cleans previous signals and contacts when an existing application is re-optimized."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM networking_contacts WHERE application_id = ?", (application_id,))
            conn.execute("DELETE FROM company_research_signals WHERE application_id = ?", (application_id,))
            conn.commit()

    def get_application(self, app_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_applications(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM applications ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def update_application_status(self, app_id: int, status: str, personalization_status: Optional[str] = None) -> None:
        with self.get_connection() as conn:
            if personalization_status:
                conn.execute(
                    "UPDATE applications SET status = ?, personalization_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, personalization_status, app_id),
                )
            else:
                conn.execute(
                    "UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, app_id),
                )
            conn.commit()

    # --- Networking Contacts ---
    def add_networking_contact(
        self,
        application_id: int,
        employee_name: str,
        employee_tagline: Optional[str],
        profile_url: str,
        referral_message_draft: Optional[str] = None,
        referral_status: str = "Not Contacted",
        email_primary: Optional[str] = None,
        email_alternatives: Optional[Any] = None,
        google_dork_url: Optional[str] = None,
        github_search_url: Optional[str] = None,
        twitter_search_url: Optional[str] = None,
    ) -> int:
        import json
        alt_str = json.dumps(email_alternatives) if isinstance(email_alternatives, list) else (email_alternatives or "")
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO networking_contacts (
                    application_id, employee_name, employee_tagline,
                    profile_url, referral_message_draft, referral_status,
                    email_primary, email_alternatives, google_dork_url,
                    github_search_url, twitter_search_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id;
                """,
                (
                    application_id, employee_name, employee_tagline,
                    profile_url, referral_message_draft, referral_status,
                    email_primary, alt_str, google_dork_url,
                    github_search_url, twitter_search_url
                ),
            )
            row = cursor.fetchone()
            conn.commit()
            return row["id"]

    def list_networking_contacts(self, application_id: int) -> List[Dict[str, Any]]:
        import json
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM networking_contacts WHERE application_id = ? ORDER BY scraped_at ASC",
                (application_id,),
            )
            contacts = []
            for row in cursor.fetchall():
                d = dict(row)
                if d.get("email_alternatives") and isinstance(d["email_alternatives"], str) and d["email_alternatives"].startswith("["):
                    try:
                        d["email_alternatives"] = json.loads(d["email_alternatives"])
                    except Exception:
                        pass
                contacts.append(d)
            return contacts

    # --- Company Research Signals ---
    def add_company_signal(
        self,
        application_id: int,
        signal_type: str,
        headline: Optional[str],
        source_url: str,
        source_tier: int,
        published_at: Optional[str] = None,
        used_in_output: int = 0,
        guard_check_passed: int = 1,
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO company_research_signals (
                    application_id, signal_type, headline, source_url,
                    source_tier, published_at, used_in_output, guard_check_passed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id;
                """,
                (application_id, signal_type, headline, source_url, source_tier, published_at, used_in_output, guard_check_passed),
            )
            row = cursor.fetchone()
            conn.commit()
            return row["id"]

    def list_company_signals(self, application_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM company_research_signals WHERE application_id = ? ORDER BY source_tier ASC, published_at DESC",
                (application_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

# Default singleton instance
db = Database()
