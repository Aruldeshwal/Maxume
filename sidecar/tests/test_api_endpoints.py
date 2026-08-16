"""Unit tests for FastAPI sidecar endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "maxume-sidecar"

def test_projects_crud_endpoint(client):
    # List projects
    res = client.get("/api/projects")
    assert res.status_code == 200
    assert "projects" in res.json()

    # Upsert project
    upsert_res = client.post(
        "/api/projects",
        json={
            "directory_path": "/projects/test_proj",
            "directory_name": "test_proj",
            "last_commit_hash": "commit_111",
            "summary_markdown": "# Test Project",
            "live_demo_url": "https://test.com"
        }
    )
    assert upsert_res.status_code == 200
    assert upsert_res.json()["status"] == "ok"

def test_applications_crud_endpoint(client):
    create_res = client.post(
        "/api/applications",
        json={
            "company_name": "Tesla",
            "role_title": "Software Engineer",
            "jd_raw_text": "Python and distributed systems required."
        }
    )
    assert create_res.status_code == 200
    app_id = create_res.json()["application_id"]
    assert app_id > 0

    get_res = client.get(f"/api/applications/{app_id}")
    assert get_res.status_code == 200
    app_data = get_res.json()
    assert app_data["application"]["company_name"] == "Tesla"
    assert app_data["networking_contacts"] == []
    assert app_data["company_research_signals"] == []
