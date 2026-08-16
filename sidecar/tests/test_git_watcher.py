"""Unit tests for Incremental Git Watcher and SSOT synchronizer."""

import os
import shutil
import tempfile
import subprocess
import pytest
from app.database import Database
from app.git_watcher import (
    GitWatcher,
    extract_live_demo_url,
    is_git_repository,
    get_directory_commit_hash,
)

@pytest.fixture
def temp_env():
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test_maxume.db")
    db = Database(db_path=db_path)
    
    projects_dir = os.path.join(tmpdir, "projects")
    os.makedirs(projects_dir, exist_ok=True)
    
    # Initialize disposable git repo
    subprocess.run(["git", "init"], cwd=projects_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@maxume.local"], cwd=projects_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Maxume Test"], cwd=projects_dir, check=True, capture_output=True)
    
    yield {
        "tmpdir": tmpdir,
        "db": db,
        "projects_dir": projects_dir,
    }
    
    shutil.rmtree(tmpdir, ignore_errors=True)

def test_extract_live_demo_url():
    """Test URL extraction from markdown text."""
    # Labeled link
    md1 = "Here is our project. Check the [Live Demo](https://myapp.vercel.app) for details."
    assert extract_live_demo_url(md1) == "https://myapp.vercel.app"

    # Multiple links, prefer deployment keyword
    md2 = "[GitHub](https://github.com/example/repo) and [App Site](https://coolapp.io)"
    assert extract_live_demo_url(md2) == "https://coolapp.io"

    # Raw URL
    md3 = "Hosted live on https://api.myservice.com/v1"
    assert extract_live_demo_url(md3) == "https://api.myservice.com/v1"

    # No link
    md4 = "Just plain text with no links."
    assert extract_live_demo_url(md4) is None

def test_git_watcher_incremental_sync(temp_env):
    """Test incremental detection of unchanged vs modified project subfolders."""
    projects_dir = temp_env["projects_dir"]
    db = temp_env["db"]
    watcher = GitWatcher(database=db)

    # 1. Create project A with markdown logs
    proj_a = os.path.join(projects_dir, "web-scraper")
    os.makedirs(proj_a, exist_ok=True)
    with open(os.path.join(proj_a, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Web Scraper\nHigh performance crawler. [Live Demo](https://scraper.io)")

    subprocess.run(["git", "add", "."], cwd=projects_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit for scraper"], cwd=projects_dir, check=True, capture_output=True)

    # 2. First scan -> Should synchronize and extract URL
    results = watcher.scan_project_folder(projects_dir)
    assert len(results) == 1
    assert results[0]["directory_name"] == "web-scraper"
    assert results[0]["status"] == "synchronized"
    assert results[0]["live_demo_url"] == "https://scraper.io"

    # Check SQLite record
    normalized_path = os.path.abspath(proj_a).replace("\\", "/")
    proj_record = db.get_project_by_path(normalized_path)
    assert proj_record is not None
    assert proj_record["live_demo_url"] == "https://scraper.io"
    first_commit = proj_record["last_commit_hash"]
    assert first_commit is not None

    # Check generated summary file
    assert os.path.exists(os.path.join(proj_a, "web-scraper_summary.md"))

    # 3. Second scan without any modifications -> Should report up_to_date
    results_2 = watcher.scan_project_folder(projects_dir)
    assert len(results_2) == 1
    assert results_2[0]["status"] == "up_to_date"
    assert results_2[0]["commit_hash"] == first_commit

    # 4. Modify project A and create project B
    with open(os.path.join(proj_a, "README.md"), "a", encoding="utf-8") as f:
        f.write("\nUpdated with distributed workers.")

    proj_b = os.path.join(projects_dir, "kv-engine")
    os.makedirs(proj_b, exist_ok=True)
    with open(os.path.join(proj_b, "LOGS.md"), "w", encoding="utf-8") as f:
        f.write("# KV Engine\nGo key-value store [Demo Web](https://kv.dev)")

    subprocess.run(["git", "add", "."], cwd=projects_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Update scraper and add kv engine"], cwd=projects_dir, check=True, capture_output=True)

    # 5. Third scan -> web-scraper should be synchronized with new hash, kv-engine synchronized
    results_3 = watcher.scan_project_folder(projects_dir)
    assert len(results_3) == 2
    
    scraper_res = next(r for r in results_3 if r["directory_name"] == "web-scraper")
    kv_res = next(r for r in results_3 if r["directory_name"] == "kv-engine")
    
    assert scraper_res["status"] == "synchronized"
    assert scraper_res["commit_hash"] != first_commit
    assert kv_res["status"] == "synchronized"
    assert kv_res["live_demo_url"] == "https://kv.dev"

    # 6. Fourth scan -> All up to date
    results_4 = watcher.scan_project_folder(projects_dir)
    assert all(r["status"] == "up_to_date" for r in results_4)
