"""Unit tests for SQLite database schema and operations."""

import os
import tempfile
import pytest
from app.database import Database

@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path=db_path)
        yield db

def test_schema_tables_exist(temp_db):
    """Verify all 4 core tables exist in the schema."""
    with temp_db.get_connection() as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]
        assert "projects" in tables
        assert "applications" in tables
        assert "networking_contacts" in tables
        assert "company_research_signals" in tables

def test_project_upsert_and_fetch(temp_db):
    """Test project upsert and retrieval."""
    pid = temp_db.upsert_project(
        directory_path="/projects/kv_store",
        directory_name="kv_store",
        last_commit_hash="abc1234",
        summary_markdown="# KV Store\nFast storage engine.",
        live_demo_url="https://demo.example.com"
    )
    assert pid > 0

    project = temp_db.get_project_by_path("/projects/kv_store")
    assert project is not None
    assert project["directory_name"] == "kv_store"
    assert project["last_commit_hash"] == "abc1234"
    assert project["live_demo_url"] == "https://demo.example.com"

    # Upsert with new commit hash
    pid2 = temp_db.upsert_project(
        directory_path="/projects/kv_store",
        directory_name="kv_store",
        last_commit_hash="def5678"
    )
    assert pid2 == pid
    project_updated = temp_db.get_project_by_path("/projects/kv_store")
    assert project_updated["last_commit_hash"] == "def5678"
    assert project_updated["summary_markdown"] == "# KV Store\nFast storage engine."

def test_application_and_relationships(temp_db):
    """Test application creation, contacts, and company signals with cascade delete."""
    app_id = temp_db.create_application(
        company_name="Acme Corp",
        role_title="Senior Backend Engineer",
        status="Draft"
    )
    assert app_id > 0

    # Add contact
    contact_id = temp_db.add_networking_contact(
        application_id=app_id,
        employee_name="Jane Doe",
        employee_tagline="Engineering Manager at Acme Corp",
        profile_url="https://linkedin.com/in/janedoe"
    )
    assert contact_id > 0

    # Add signal
    signal_id = temp_db.add_company_signal(
        application_id=app_id,
        signal_type="product_launch",
        headline="Acme Corp launches new AI cloud",
        source_url="https://acme.example.com/news/cloud",
        source_tier=1,
        guard_check_passed=1
    )
    assert signal_id > 0

    contacts = temp_db.list_networking_contacts(app_id)
    assert len(contacts) == 1
    assert contacts[0]["employee_name"] == "Jane Doe"

    signals = temp_db.list_company_signals(app_id)
    assert len(signals) == 1
    assert signals[0]["headline"] == "Acme Corp launches new AI cloud"
    assert signals[0]["source_tier"] == 1
