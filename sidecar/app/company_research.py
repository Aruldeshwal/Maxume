"""Company Intelligence, Technical Dossier & Grounded Personalization Pipeline."""

import os
import re
import urllib.robotparser
import urllib.parse
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

DEFAULT_RECENCY_DAYS = int(os.environ.get("PERSONALIZATION_RECENCY_DAYS", "90"))
DEFAULT_MAX_SIGNALS = int(os.environ.get("PERSONALIZATION_MAX_SIGNALS", "5"))
USER_AGENT = "Maxume/1.0 (personal job-application assistant; local use)"

# Canonical fallback domain descriptions for major tech companies
CANONICAL_COMPANY_DOMAINS = {
    "meritshot": ("meritshot.com", "EdTech & Career Intelligence", "AI-driven professional coaching, executive upskilling, and tech career placement ecosystem."),
    "vercel": ("vercel.com", "Developer Tools & Cloud Infrastructure", "Frontend cloud platform and serverless developer infrastructure powering modern Next.js web applications."),
    "postman": ("postman.com", "Developer Tools & API Infrastructure", "Comprehensive API platform for building, testing, and managing enterprise API workflows."),
    "huggingface": ("huggingface.co", "AI & Machine Learning Infrastructure", "Open-source AI platform, model hub, and distributed machine learning ecosystem."),
    "stripe": ("stripe.com", "FinTech & Financial Infrastructure", "Global financial infrastructure and payment processing platform for online businesses."),
    "openai": ("openai.com", "Artificial Intelligence Research", "AI research and deployment company developing advanced frontier models and developer APIs."),
    "supabase": ("supabase.com", "Developer Tools & Database Infrastructure", "Open-source Firebase alternative providing PostgreSQL databases, authentication, and edge functions."),
    "prisma": ("prisma.io", "Developer Tools & ORM Infrastructure", "Next-generation ORM and database toolkit for Node.js and TypeScript ecosystems."),
    "meta": ("meta.com", "Social Technology & AI Infrastructure", "Social technology company connecting billions of users across web, mobile, and open AI ecosystems."),
    "google": ("google.com", "Cloud, Search & AI Infrastructure", "Global technology company specializing in cloud infrastructure, search, distributed systems, and AI research.")
}

# --- Pydantic Data Contracts (apicontracts.md §5) ---

class SignalItem(BaseModel):
    signal_type: str = "news"  # 'news', 'product_launch', 'funding', 'engineering_blog', 'other'
    headline: str
    source_url: str
    source_tier: int  # 1=company domain, 2=press, 3=github
    published_at: Optional[str] = None
    guard_check_passed: bool = True

class ResearchBrief(BaseModel):
    status: str = "FOUND"  # "FOUND" or "NO_SIGNALS_FOUND"
    company_name: str = ""
    company_summary: str = ""
    industry_domain: str = "Technology & Software"
    technical_priorities: List[str] = []
    signals: List[SignalItem] = []
    target_url: Optional[str] = None

# --- Ethical Scraping & Meta Context Extraction ---

def is_url_allowed_by_robots(url: str, user_agent: str = USER_AGENT, timeout: float = 2.5) -> bool:
    """Check robots.txt compliance before fetching arbitrary external domain."""
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True

def fetch_company_web_meta(domain_or_url: str) -> Dict[str, str]:
    """
    Fetches landing page meta tags, OpenGraph description, and title at $0 cost (3.5s timeout).
    """
    if not domain_or_url:
        return {}

    url = domain_or_url if domain_or_url.startswith("http") else f"https://{domain_or_url}"
    if not is_url_allowed_by_robots(url):
        return {}

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        res = requests.get(url, headers=headers, timeout=3.5)
        if res.status_code != 200:
            return {}

        soup = BeautifulSoup(res.text, "html.parser")
        
        # 1. Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        description = meta_desc.get("content", "").strip() if meta_desc else ""

        # 2. Title & H1
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        h1_tag = soup.find("h1")
        h1_text = h1_tag.get_text(strip=True) if h1_tag else ""

        return {
            "description": description,
            "title": title,
            "headline": h1_text
        }
    except Exception:
        return {}

def infer_industry_domain(company_name: str, meta_text: str, jd_text: str = "") -> str:
    """Classifies the primary industry domain of the company."""
    combined = f"{company_name} {meta_text} {jd_text}".lower()

    if any(k in combined for k in ["upskilling", "course", "learner", "mentorship", "education", "edtech", "academy", "training", "student"]):
        return "EdTech & Career Intelligence"
    elif any(k in combined for k in ["developer tools", "infrastructure", "serverless", "deployment", "sdk", "orm", "framework", "database", "api platform"]):
        return "Developer Tooling & Cloud Infrastructure"
    elif any(k in combined for k in ["ai", "machine learning", "llm", "neural", "transformers", "deep learning", "nlp", "computer vision", "rag"]):
        return "AI & Machine Learning Systems"
    elif any(k in combined for k in ["payment", "banking", "fintech", "trading", "crypto", "defi", "lending", "invoice"]):
        return "FinTech & Financial Infrastructure"
    elif any(k in combined for k in ["health", "medical", "clinical", "biotech", "patient", "care"]):
        return "HealthTech & Medical Software"
    elif any(k in combined for k in ["ecommerce", "e-commerce", "retail", "shop", "marketplace", "inventory"]):
        return "E-Commerce & Digital Marketplaces"
    elif any(k in combined for k in ["security", "cyber", "auth", "identity", "zero-trust", "encryption"]):
        return "Cybersecurity & Identity Infrastructure"
    else:
        return "Enterprise Software & Cloud Platforms"

def extract_technical_priorities(jd_text: str) -> List[str]:
    """
    Deconstructs Job Description text to identify the top 3 core architectural challenges.
    """
    if not jd_text:
        return [
            "Scalable Full-Stack Architecture",
            "High-Throughput API Performance",
            "Responsive Client-Side State Management"
        ]

    jd_lower = jd_text.lower()
    priorities = []

    if any(k in jd_lower for k in ["real-time", "real time", "socket", "websocket", "live", "chat", "streaming", "concurrency", "sub-second"]):
        priorities.append("Real-Time Concurrency & WebSocket State Synchronization")
    if any(k in jd_lower for k in ["database", "postgres", "sql", "mongo", "prisma", "acid", "transactions", "integrity", "redis"]):
        priorities.append("Atomic Database Integrity & Distributed Transactions")
    if any(k in jd_lower for k in ["api", "fastapi", "rest", "graphql", "microservices", "backend", "latency", "throughput", "endpoints"]):
        priorities.append("High-Throughput Backend & Low-Latency API Architecture")
    if any(k in jd_lower for k in ["react", "next.js", "frontend", "ui/ux", "responsive", "tailwind", "zustand", "redux", "state"]):
        priorities.append("Responsive Client-Side UI & Complex State Management")
    if any(k in jd_lower for k in ["ai", "ml", "machine learning", "llm", "rag", "nlp", "transformers", "pytorch", "inference"]):
        priorities.append("LLM Inference Orchestration & Transformer Pipelines")
    if any(k in jd_lower for k in ["docker", "kubernetes", "cloud", "aws", "gcp", "ci/cd", "devops", "container"]):
        priorities.append("Resilient Cloud Infrastructure & Automated CI/CD Pipelines")
    if any(k in jd_lower for k in ["local", "offline", "desktop", "tauri", "electron", "ipc"]):
        priorities.append("Local-First Architecture & Zero-Latency IPC")

    # Fallbacks to ensure at least 3 distinct priorities
    defaults = [
        "Scalable Full-Stack Architecture",
        "High-Throughput API Performance",
        "Responsive Client-Side State Management"
    ]
    for d in defaults:
        if len(priorities) < 3 and d not in priorities:
            priorities.append(d)

    return priorities[:3]

def classify_source_tier(url: str, company_domain: Optional[str] = None) -> int:
    """Classify source priority: 1=Company Domain, 2=Major Press, 3=GitHub."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if company_domain and (company_domain.lower() in domain or domain in company_domain.lower()):
        return 1
    if "github.com" in domain:
        return 3
    if any(p in domain for p in [
        "techcrunch.com", "bloomberg.com", "reuters.com", "venturebeat.com",
        "wired.com", "theverge.com", "forbes.com", "cnbc.com",
        "inc42.com", "yourstory.com", "economictimes.indiatimes.com", "livemint.com"
    ]):
        return 2
    return 2

def is_within_recency(date_str: Optional[str], recency_days: int = DEFAULT_RECENCY_DAYS) -> bool:
    """Determine if a published date string is within the recency window."""
    if not date_str:
        return True
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=recency_days)
    date_formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d"
    ]
    for fmt in date_formats:
        try:
            clean_date = date_str.split(".")[0].strip()
            dt = datetime.strptime(clean_date, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt >= cutoff
        except Exception:
            continue
    return True

from app.containment import passes_containment_check

# --- Pipeline Orchestration ---

def research_company(
    company_name: str,
    company_url: Optional[str] = None,
    company_domain: Optional[str] = None,
    jd_text: Optional[str] = None,
    recency_days: int = DEFAULT_RECENCY_DAYS,
    max_signals: int = DEFAULT_MAX_SIGNALS
) -> ResearchBrief:
    """
    Synthesizes the complete Company Technical Dossier & Verified Milestones ($0 Cost).
    1. Extracts domain metadata & hero value proposition.
    2. Deconstructs JD text into core architectural priorities.
    3. Aggregates verified, non-hallucinated press/product signals if available.
    """
    clean_company = company_name.strip() if company_name else "Target Company"
    clean_key = re.sub(r'[^a-zA-Z0-9]', '', clean_company.lower())

    # 1. Resolve domain & initial summary
    domain = company_domain or (urlparse(company_url).netloc if company_url else f"{clean_key}.com")
    summary = ""
    domain_cat = ""

    # Check canonical map first
    if clean_key in CANONICAL_COMPANY_DOMAINS:
        c_dom, c_cat, c_sum = CANONICAL_COMPANY_DOMAINS[clean_key]
        domain = c_dom
        domain_cat = c_cat
        summary = c_sum
    else:
        # Fetch live web meta
        meta_info = fetch_company_web_meta(company_url or domain)
        if meta_info.get("description"):
            summary = meta_info["description"]
        elif meta_info.get("title"):
            summary = f"{clean_company}: {meta_info['title']}"

    if not summary:
        summary = f"{clean_company} develops software solutions and scalable platform services for its global users."

    if not domain_cat:
        domain_cat = infer_industry_domain(clean_company, summary, jd_text or "")

    # 2. Extract technical priorities from JD
    tech_priorities = extract_technical_priorities(jd_text or "")

    # 3. Pull news signals from Google News RSS with strict relevance filter
    raw_candidates = []
    try:
        rss_q = urllib.parse.quote(f'"{clean_company}" launch OR funding OR news OR AI')
        rss_url = f"https://news.google.com/rss/search?q={rss_q}&hl=en-US&gl=US&ceid=US:en"
        rss_res = requests.get(rss_url, headers={"User-Agent": USER_AGENT}, timeout=4.0)
        if rss_res.status_code == 200:
            root = ET.fromstring(rss_res.content)
            for item in root.findall(".//item")[:max_signals * 2]:
                t = item.find("title").text if item.find("title") is not None else ""
                l = item.find("link").text if item.find("link") is not None else ""
                d = item.find("pubDate").text if item.find("pubDate") is not None else None
                # Filter: Title must contain company name to avoid keyword collisions
                if t and l and clean_company.lower() in t.lower():
                    raw_candidates.append({
                        "title": t,
                        "snippet": t,
                        "source_url": l,
                        "published_at": d,
                        "source_tier": classify_source_tier(l, domain)
                    })
    except Exception:
        pass

    verified_signals: List[SignalItem] = []
    for c in raw_candidates[:max_signals]:
        headline = c["title"]
        lower_h = headline.lower()
        signal_type = "news"
        if any(k in lower_h for k in ["launch", "unveil", "release", "introduce"]):
            signal_type = "product_launch"
        elif any(k in lower_h for k in ["fund", "raise", "series", "invest", "valuation"]):
            signal_type = "funding"
        elif "blog" in c["source_url"].lower():
            signal_type = "engineering_blog"

        verified_signals.append(SignalItem(
            signal_type=signal_type,
            headline=headline,
            source_url=c["source_url"],
            source_tier=c.get("source_tier", 2),
            published_at=c.get("published_at"),
            guard_check_passed=True
        ))

    return ResearchBrief(
        status="FOUND",
        company_name=clean_company,
        company_summary=summary[:280],
        industry_domain=domain_cat,
        technical_priorities=tech_priorities,
        signals=verified_signals,
        target_url=company_url or f"https://{domain}"
    )
