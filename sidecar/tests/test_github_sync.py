"""Unit tests for GitHub profile remote sync and live demo extraction."""

import pytest
from unittest.mock import patch, MagicMock
from app.github_sync import (
    extract_github_live_demo,
    extract_project_bullet_points,
    sync_github_profile_repositories
)
from app.database import Database

def test_extract_github_live_demo():
    # 1. Homepage priority
    assert extract_github_live_demo("https://my-app.vercel.app", "# README") == "https://my-app.vercel.app"

    # 2. Markdown link detection
    readme_md = "# Project\nCheck out the [Live Demo](https://awesome-tool.netlify.app) for preview."
    assert extract_github_live_demo(None, readme_md) == "https://awesome-tool.netlify.app"

    # 3. Known domain detection
    readme_raw = "# Service\nDeployed on https://my-service.fly.dev with high uptime."
    assert extract_github_live_demo(None, readme_raw) == "https://my-service.fly.dev"

def test_extract_project_bullet_points():
    readme = (
        "# KV Store\n\n"
        "## Key Features\n"
        "- Implemented Raft consensus protocol from scratch with 99.9% leader stability.\n"
        "- Engineered LSM-tree storage engine achieving 45,000 writes/sec.\n"
        "- Optimized read path with Bloom filters reducing disk I/O by 82%.\n"
    )
    bullets = extract_project_bullet_points(readme, "A fast KV store", "kv-store")
    assert len(bullets) == 3
    assert "Raft consensus" in bullets[0]
    assert "LSM-tree storage" in bullets[1]

def test_sync_github_profile_mocked(tmp_path):
    db_path = str(tmp_path / "test_gh.db")
    test_db = Database(db_path=db_path)

    mock_repos_payload = [
        {
            "name": "maxume-ai",
            "html_url": "https://github.com/Aruldeshwal/maxume-ai",
            "description": "Local-first AI resume optimizer.",
            "homepage": "https://maxume.vercel.app",
            "default_branch": "main",
            "language": "TypeScript",
            "pushed_at": "2026-08-16T12:00:00Z",
            "fork": False
        }
    ]

    mock_readme_text = "# Maxume AI\n## Highlights\n- Built hybrid Ollama + cloud API architecture.\n- Single page DOCX styling rebuilder."

    with patch("requests.get") as mock_get:
        # First call is repos list, second is raw readme
        mock_resp_repos = MagicMock()
        mock_resp_repos.status_code = 200
        mock_resp_repos.json.return_value = mock_repos_payload

        mock_resp_readme = MagicMock()
        mock_resp_readme.status_code = 200
        mock_resp_readme.text = mock_readme_text

        mock_get.side_effect = [mock_resp_repos, mock_resp_readme]

        results = sync_github_profile_repositories("Aruldeshwal", database=test_db)
        assert len(results) == 1
        assert results[0]["directory_name"] == "maxume-ai"
        assert results[0]["live_demo_url"] == "https://maxume.vercel.app"

        projects_in_db = test_db.list_projects()
        assert len(projects_in_db) == 1
        assert projects_in_db[0]["directory_name"] == "maxume-ai"
        assert projects_in_db[0]["live_demo_url"] == "https://maxume.vercel.app"
