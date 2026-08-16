"""GitHub Profile Remote Fetcher & Auto-Summarizer for Maxume SSOT."""

import re
import requests
from typing import Optional, List, Dict, Any, Tuple
from app.database import Database, db as default_db
from app.git_watcher import MD_LINK_REGEX, RAW_URL_REGEX, extract_live_demo_url

LIVE_HOST_KEYWORDS = [
    "vercel.app", "netlify.app", "herokuapp.com", "fly.dev", "railway.app",
    "render.com", "github.io", "pages.dev", "firebaseapp.com", "surge.sh",
    "aws", "azure", "replit.app", "streamlit.app"
]

def extract_github_live_demo(homepage: Optional[str], readme_text: str) -> Optional[str]:
    """
    Extracts the highest-confidence live deployment URL:
    1. Repository homepage field on GitHub
    2. Explicit markdown links (e.g. [Live Demo](...), [Website](...))
    3. Known deployment host domains (Vercel, Netlify, Render, Cloudflare, etc.)
    """
    if homepage and homepage.strip().startswith("http"):
        return homepage.strip()

    if not readme_text:
        return None

    # Check markdown explicit links
    md_matches = MD_LINK_REGEX.findall(readme_text)
    for label, url in md_matches:
        label_lower = label.lower()
        if any(kw in label_lower for kw in ["demo", "live", "app", "site", "web", "deploy", "preview", "prod"]):
            if "github.com" not in url.lower() or "/issues" not in url.lower():
                return url

    # Check for known hosting domains in raw URLs
    raw_urls = RAW_URL_REGEX.findall(readme_text)
    for u in raw_urls:
        u_lower = u.lower()
        if any(host in u_lower for host in LIVE_HOST_KEYWORDS):
            return u.rstrip(".)]>\"'")

    # Fallback to general markdown extractor
    fallback_url = extract_live_demo_url(readme_text)
    if fallback_url and "github.com" not in fallback_url.lower():
        return fallback_url

    return None

def extract_project_bullet_points(readme_text: str, description: Optional[str], repo_name: str) -> List[str]:
    """
    Extracts structured, high-impact resume bullet points from README markdown.
    """
    bullets = []
    
    if not readme_text:
        if description:
            bullets.append(f"Architected and deployed {repo_name}: {description}")
        else:
            bullets.append(f"Engineered full-stack architecture and backend services for {repo_name}.")
        return bullets

    # 1. Search for bullet points under Features / Highlights / Key Capabilities
    lines = readme_text.splitlines()
    in_key_section = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check section headers
        if stripped.startswith("#"):
            lower_header = stripped.lower()
            if any(h in lower_header for h in ["feature", "highlight", "architecture", "overview", "what it does", "key capabilities", "tech stack"]):
                in_key_section = True
            else:
                in_key_section = False
            continue

        if in_key_section:
            if stripped.startswith(("-", "*", "•", "1.", "2.", "3.", "4.")):
                clean_bullet = re.sub(r'^[-*•\d.)\s]+', '', stripped).strip()
                # Strip markdown bolding / formatting
                clean_bullet = clean_bullet.replace("**", "").replace("__", "")
                if len(clean_bullet) > 20 and not clean_bullet.startswith("http"):
                    bullets.append(clean_bullet)
                    if len(bullets) >= 4:
                        break

    # 2. If no bullet points found under headers, extract top 3-4 bullet lines from anywhere in README
    if not bullets:
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("-", "*", "•")):
                clean_bullet = re.sub(r'^[-*•\s]+', '', stripped).replace("**", "").strip()
                if len(clean_bullet) > 25 and not clean_bullet.startswith("http"):
                    bullets.append(clean_bullet)
                    if len(bullets) >= 4:
                        break

    # 3. Fallback to description + overview sentence
    if not bullets:
        if description:
            bullets.append(f"Engineered and deployed {repo_name}: {description}")
        
        # Grab first 2 descriptive sentences from README
        paragraphs = [p.strip() for p in readme_text.split("\n\n") if p.strip() and not p.strip().startswith("#")]
        if paragraphs:
            first_p = paragraphs[0].replace("\n", " ").replace("**", "")
            sentences = re.split(r'(?<=[.!?])\s+', first_p)
            for s in sentences[:3]:
                if len(s) > 25 and not s.startswith("[") and not s.startswith("http"):
                    bullets.append(s.strip())

    if not bullets:
        bullets.append(f"Engineered and maintained {repo_name} repository.")

    return bullets[:4]

def sync_github_profile_repositories(
    username: str,
    token: Optional[str] = None,
    database: Database = default_db
) -> List[Dict[str, Any]]:
    """
    Queries public GitHub API for a user profile, fetches repositories and READMEs,
    extracts live demo URLs and engineering bullet points, and persists to local SQLite SSOT.
    """
    clean_user = username.strip().lstrip("@")
    if not clean_user:
        return []

    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "Maxume-App"}
    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"

    # Fetch user repos
    api_url = f"https://api.github.com/users/{clean_user}/repos?per_page=100&sort=pushed"
    res = requests.get(api_url, headers=headers, timeout=10.0)
    
    if res.status_code != 200:
        if res.status_code == 404:
            raise ValueError(f"GitHub user '{clean_user}' not found.")
        elif res.status_code == 403:
            raise RuntimeError("GitHub API rate limit exceeded. Provide a personal GitHub token or try again later.")
        else:
            raise RuntimeError(f"GitHub API returned HTTP {res.status_code}: {res.text}")

    repos_data = res.json()
    results = []

    for repo in repos_data:
        # Skip forks if desired
        is_fork = repo.get("fork", False)
        if is_fork:
            continue

        repo_name = repo.get("name", "")
        repo_html_url = repo.get("html_url", "")
        description = repo.get("description", "")
        homepage = repo.get("homepage", "")
        default_branch = repo.get("default_branch", "main")
        language = repo.get("language") or "General Software"
        pushed_at = repo.get("pushed_at", "")

        # Try to fetch raw README
        readme_text = ""
        for branch_candidate in [default_branch, "master", "main"]:
            raw_readme_url = f"https://raw.githubusercontent.com/{clean_user}/{repo_name}/{branch_candidate}/README.md"
            try:
                r_res = requests.get(raw_readme_url, timeout=5.0)
                if r_res.status_code == 200:
                    readme_text = r_res.text
                    break
            except Exception:
                continue

        # Extract live demo URL
        live_demo_url = extract_github_live_demo(homepage, readme_text) or (homepage if homepage and homepage.startswith("http") else None)

        # Extract bullet points
        bullet_points = extract_project_bullet_points(readme_text, description, repo_name)
        
        # Build clean markdown summary
        bullets_formatted = "\n".join(f"- {b}" for b in bullet_points)
        summary_markdown = (
            f"# {repo_name}\n\n"
            f"**GitHub**: {repo_html_url}\n"
            f"**Language / Tech**: {language}\n"
            f"**Live Demo**: {live_demo_url or 'None'}\n\n"
            f"## Engineering Highlights\n{bullets_formatted}\n"
        )

        virtual_path = f"github.com/{clean_user}/{repo_name}"

        # Upsert into SQLite SSOT
        database.upsert_project(
            directory_path=virtual_path,
            directory_name=repo_name,
            last_commit_hash=pushed_at,
            summary_markdown=summary_markdown,
            live_demo_url=live_demo_url
        )

        results.append({
            "directory_name": repo_name,
            "directory_path": virtual_path,
            "commit_hash": pushed_at[:10] if pushed_at else "Remote",
            "live_demo_url": live_demo_url,
            "language": language,
            "bullet_points": bullet_points,
            "status": "synchronized"
        })

    return results
