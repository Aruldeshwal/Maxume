"""GitHub Profile Remote Fetcher & High-Impact AI Resume Bullet Synthesizer for Maxume SSOT."""

import os
import re
import json
import requests
from typing import Optional, List, Dict, Any
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

def synthesize_high_impact_bullets_ai(
    repo_name: str,
    description: Optional[str],
    language: str,
    readme_text: str
) -> Optional[List[str]]:
    """
    Uses local Ollama or cloud LLM to synthesize elite, Google XYZ-formula resume bullet points:
    'Accomplished [X] as measured by [Y], by doing [Z]'
    """
    prompt = (
        "You are an elite Staff Software Engineer and FAANG resume strategist. "
        "Analyze the provided GitHub repository documentation and craft exactly 3 to 4 standout, high-impact resume bullet points. "
        "\n\nSTRICT BULLET POINT RULES:\n"
        "1. Follow Google's XYZ formula: 'Accomplished [X] as measured by [Y], by doing [Z]'.\n"
        "2. Start every bullet with a strong power action verb (e.g. Architected, Engineered, Implemented, Optimized, Streamlined, Scaled).\n"
        "3. Focus on concrete architectural choices (e.g., concurrency models, distributed state, caching layers, async I/O, schema design, latency reduction, throughput, fault tolerance).\n"
        "4. DO NOT write passive fluff like 'Used React to make a website' or 'Wrote Python code'.\n"
        "5. Output ONLY a valid JSON array of 3-4 strings (bullet points), nothing else.\n\n"
        f"REPOSITORY: {repo_name}\n"
        f"DESCRIPTION: {description or 'N/A'}\n"
        f"PRIMARY TECH: {language}\n"
        f"README CONTENT:\n{readme_text[:2500]}"
    )

    # 1. Try local Ollama if available
    try:
        ollama_url = "http://127.0.0.1:11434/api/generate"
        res = requests.post(
            ollama_url,
            json={
                "model": "qwen2.5:7b-instruct",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=8.0
        )
        if res.status_code == 200:
            resp_text = res.json().get("response", "")
            clean_json = re.sub(r'^```json\s*|\s*```$', '', resp_text.strip(), flags=re.MULTILINE)
            bullets = json.loads(clean_json)
            if isinstance(bullets, list) and len(bullets) >= 2:
                return [b.lstrip("•-* ") for b in bullets[:4]]
    except Exception:
        pass

    # 2. Try Groq if GROQ_API_KEY is configured
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            groq_url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a FAANG technical resume writer. Output ONLY a JSON array of 3-4 high-impact resume bullet points."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }
            res = requests.post(groq_url, headers=headers, json=payload, timeout=8.0)
            if res.status_code == 200:
                text = res.json()["choices"][0]["message"]["content"].strip()
                clean_json = re.sub(r'^```json\s*|\s*```$', '', text, flags=re.MULTILINE)
                bullets = json.loads(clean_json)
                if isinstance(bullets, list) and len(bullets) >= 2:
                    return [b.lstrip("•-* ") for b in bullets[:4]]
        except Exception:
            pass

    # 3. Try Gemini if GEMINI_API_KEY is configured
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024}
            }
            res = requests.post(gemini_url, json=payload, timeout=8.0)
            if res.status_code == 200:
                text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                clean_json = re.sub(r'^```json\s*|\s*```$', '', text, flags=re.MULTILINE)
                bullets = json.loads(clean_json)
                if isinstance(bullets, list) and len(bullets) >= 2:
                    return [b.lstrip("•-* ") for b in bullets[:4]]
        except Exception:
            pass

    return None

def extract_project_bullet_points(
    readme_text: str,
    description: Optional[str],
    repo_name: str,
    language: str = "Software Engineering"
) -> List[str]:
    """
    Extracts structured, high-impact resume bullet points from README markdown,
    leveraging AI synthesis when available, or advanced architectural heuristics when offline.
    """
    # 1. Try AI synthesis first for standout impact
    ai_bullets = synthesize_high_impact_bullets_ai(repo_name, description, language, readme_text)
    if ai_bullets and len(ai_bullets) >= 2:
        return ai_bullets

    # 2. Advanced Heuristic Extraction (Action Verb Framing)
    bullets = []
    
    if not readme_text:
        desc = description or f"high-scale {language} application"
        bullets.append(f"Architected and deployed {repo_name}, engineering end-to-end full-stack architecture for {desc}.")
        bullets.append(f"Implemented modular data models and RESTful API endpoints optimizing request throughput.")
        bullets.append(f"Structured automated testing and containerized build pipelines ensuring continuous deployment.")
        return bullets

    # Search for bullet points under Features / Highlights / Key Capabilities
    lines = readme_text.splitlines()
    in_key_section = False
    action_verbs = ["Architected", "Engineered", "Implemented", "Optimized", "Designed", "Built", "Developed", "Deployed"]
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("#"):
            lower_header = stripped.lower()
            if any(h in lower_header for h in ["feature", "highlight", "architecture", "overview", "key capabilities", "what it does", "tech"]):
                in_key_section = True
            else:
                in_key_section = False
            continue

        if in_key_section and stripped.startswith(("-", "*", "•", "1.", "2.", "3.", "4.")):
            clean = re.sub(r'^[-*•\d.)\s]+', '', stripped).replace("**", "").replace("__", "").strip()
            if len(clean) > 20 and not clean.startswith("http"):
                # Frame with strong action verb if missing
                if not any(clean.startswith(v) for v in action_verbs):
                    clean = f"Implemented {clean[0].lower() + clean[1:] if len(clean) > 1 else clean}"
                bullets.append(clean)
                if len(bullets) >= 4:
                    break

    # If not enough bullets found from headers, extract from general text paragraphs
    if len(bullets) < 2:
        paragraphs = [p.strip() for p in readme_text.split("\n\n") if p.strip() and not p.strip().startswith("#")]
        for p in paragraphs[:3]:
            clean_p = p.replace("\n", " ").replace("**", "").strip()
            sentences = re.split(r'(?<=[.!?])\s+', clean_p)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) > 30 and not s_clean.startswith("[") and not s_clean.startswith("http"):
                    if not any(s_clean.startswith(v) for v in action_verbs):
                        s_clean = f"Engineered {s_clean[0].lower() + s_clean[1:]}"
                    bullets.append(s_clean)
                    if len(bullets) >= 4:
                        break

    # Fallback guarantees 3 solid bullet points
    if len(bullets) == 0:
        desc = description or f"production {language} system"
        bullets.append(f"Architected and deployed {repo_name} using {language}, resolving complex business workflows.")
        bullets.append(f"Designed low-latency backend services and data serialization schemas.")
        bullets.append(f"Streamlined CI/CD deployment pipelines achieving fast iteration cycles.")

    return bullets[:4]

def sync_github_profile_repositories(
    username: str,
    token: Optional[str] = None,
    database: Database = default_db
) -> List[Dict[str, Any]]:
    """
    Queries public GitHub API for a user profile, fetches repositories and READMEs,
    extracts live demo URLs and generates high-impact bullet points, and persists to local SQLite SSOT.
    """
    clean_user = username.strip().lstrip("@")
    if not clean_user:
        return []

    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "Maxume-App"}
    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"

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
        # Skip forks to focus on original projects
        if repo.get("fork", False):
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

        # Generate high-impact bullet points
        bullet_points = extract_project_bullet_points(readme_text, description, repo_name, language)
        
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
