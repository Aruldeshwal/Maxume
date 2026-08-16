"""Unit tests for FastAPI sidecar endpoints."""

import os
import pytest
from unittest.mock import patch, AsyncMock
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
    res = client.get("/api/projects")
    assert res.status_code == 200
    assert "projects" in res.json()

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

def test_company_research_endpoint(client):
    res = client.post(
        "/api/research",
        json={
            "company_name": "Acme Robotics",
            "company_url": "https://acme.example.com",
            "recency_days": 90,
            "max_signals": 5
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in ("FOUND", "NO_SIGNALS_FOUND")
    assert "signals" in data

def test_ollama_endpoints(client):
    res_status = client.get("/api/ollama/status")
    assert res_status.status_code == 200

    res_models = client.get("/api/ollama/models?num_ctx=2048&budget_gb=5.2")
    assert res_models.status_code == 200
    assert "models" in res_models.json()

def test_optimize_endpoint_mocked(client, tmp_path):
    # Mock cloud services to avoid real network / credentials in unit test
    with patch("app.main.gemini_service.rerank_projects_for_jd", new_callable=AsyncMock) as mock_rerank, \
         patch("app.main.groq_service.generate_cover_letter", new_callable=AsyncMock) as mock_cl, \
         patch("app.main.groq_service.generate_application_email", new_callable=AsyncMock) as mock_email, \
         patch("app.main.lookup_company_employees", new_callable=AsyncMock) as mock_contacts:
        
        mock_rerank.return_value = [
            {"title": "KV DB", "tech_stack": "Go", "bullets": ["Built Raft engine."]}
        ]
        mock_cl.return_value = "Dear Hiring Team, Cover letter for Anthropic..."
        mock_email.return_value = "Subject: Senior Engineer Application\n\nHi Team..."
        mock_contacts.return_value = [
            {"employee_name": "Sarah Connor", "employee_tagline": "Recruiter at Anthropic", "profile_url": "https://linkedin.com/in/sarah"}
        ]

        res = client.post(
            "/api/optimize",
            json={
                "company_name": "Anthropic",
                "role_title": "Systems Engineer",
                "jd_raw_text": "Distributed systems, Python, Go.",
                "output_dir": str(tmp_path / "output"),
                "personalization_enabled": False
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["application_id"] > 0
        assert "Cover letter for Anthropic" in data["cover_letter"]
        assert len(data["networking_contacts"]) == 1
        assert data["networking_contacts"][0]["employee_name"] == "Sarah Connor"
