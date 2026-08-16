"""SQLite Database driver and schema migration manager for Maxume SSOT."""

import sqlite3
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import contextmanager

DEFAULT_DB_PATH = os.environ.get("MAXUME_DB_PATH", "maxume_local.db")

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
            conn.commit()

    # --- Project SSOT Operations ---
    def get_project_by_path(self, directory_path: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM projects WHERE directory_path = ?", (directory_path,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_projects(self, include_hidden: bool = True) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if include_hidden:
                cursor = conn.execute("SELECT * FROM projects ORDER BY is_hidden ASC, directory_name ASC")
            else:
                cursor = conn.execute("SELECT * FROM projects WHERE is_hidden = 0 ORDER BY directory_name ASC")
            return [dict(row) for row in cursor.fetchall()]

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

    # --- Job Application Logs ---
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
                    compressed_image_path, output_folder_path, personalization_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING id;
                """,
                (company_name, role_title, status, jd_raw_text, compressed_image_path, output_folder_path, personalization_status),
            )
            row = cursor.fetchone()
            conn.commit()
            return row["id"]

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
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO networking_contacts (
                    application_id, employee_name, employee_tagline,
                    profile_url, referral_message_draft, referral_status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                RETURNING id;
                """,
                (application_id, employee_name, employee_tagline, profile_url, referral_message_draft, referral_status),
            )
            row = cursor.fetchone()
            conn.commit()
            return row["id"]

    def list_networking_contacts(self, application_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM networking_contacts WHERE application_id = ? ORDER BY scraped_at ASC",
                (application_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

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
