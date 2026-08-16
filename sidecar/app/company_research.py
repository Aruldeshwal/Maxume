"""Company Signal Research & Grounded Personalization Pipeline with 3-Stage Hallucination Guard."""

import os
import re
import time
import urllib.robotparser
import urllib.parse
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

DEFAULT_RECENCY_DAYS = int(os.environ.get("PERSONALIZATION_RECENCY_DAYS", "90"))
DEFAULT_MAX_SIGNALS = int(os.environ.get("PERSONALIZATION_MAX_SIGNALS", "5"))
USER_AGENT = "Maxume/1.0 (personal job-application assistant; local use)"

TIER_1_PATTERNS = ["news", "press", "blog", "about", "company", "careers", "updates"]
TIER_3_PATTERNS = ["github.com"]

# --- Pydantic Data Contracts (apicontracts.md §5) ---

class SignalItem(BaseModel):
    signal_type: str = "news"  # 'news', 'product_launch', 'funding', 'engineering_blog', 'other'
    headline: str
    source_url: str
    source_tier: int  # 1=company domain, 2=press, 3=github
    published_at: Optional[str] = None
    guard_check_passed: bool = True

class ResearchBrief(BaseModel):
    status: str  # "FOUND" or "NO_SIGNALS_FOUND"
    signals: List[SignalItem] = []
    company_name: str = ""
    target_url: Optional[str] = None

# --- Stage A & B: Ethical Scraping & Source Fetching ---

def is_url_allowed_by_robots(url: str, user_agent: str = USER_AGENT, timeout: float = 3.0) -> bool:
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

def fetch_page_content_clean(url: str, timeout: float = 8.0) -> Optional[str]:
    """
    Fetch and clean text from an external company page.
    Strictly follows scraping ethics (security.md §4): 8s timeout, descriptive User-Agent.
    """
    if not is_url_allowed_by_robots(url):
        return None

    try:
        headers = {"User-Agent": USER_AGENT}
        res = requests.get(url, headers=headers, timeout=timeout)
        if res.status_code != 200:
            return None

        # Check for paywall keywords
        lower_text = res.text.lower()
        if "subscribe to read" in lower_text or "paywall" in lower_text or "sign in to continue" in lower_text:
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text[:4000] if text else None
    except Exception:
        return None

def classify_source_tier(url: str, company_domain: Optional[str] = None) -> int:
    """Classify source priority: 1=Company Domain, 2=Major Press, 3=GitHub."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if company_domain and (company_domain.lower() in domain or domain in company_domain.lower()):
        return 1
    if any(p in domain for p in TIER_3_PATTERNS):
        return 3
    if any(p in domain for p in [
        "techcrunch.com", "bloomberg.com", "reuters.com", "venturebeat.com",
        "wired.com", "theverge.com", "forbes.com", "cnbc.com",
        "inc42.com", "yourstory.com", "entrackr.com", "economictimes.indiatimes.com",
        "livemint.com", "vccircle.com", "business-standard.com"
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
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%b %d, %Y",
        "%B %d, %Y"
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
    recency_days: int = DEFAULT_RECENCY_DAYS,
    max_signals: int = DEFAULT_MAX_SIGNALS,
    gemini_api_key: Optional[str] = None,
    mock_snippets: Optional[List[Dict[str, Any]]] = None,
    mock_gemini_response: Optional[str] = None
) -> ResearchBrief:
    """
    Full 5-Stage Company Signal Research Pipeline (companyresearch.md §2).
    Returns ResearchBrief with status 'FOUND' or 'NO_SIGNALS_FOUND'.
    Never raises for 'nothing found'.
    """
    if not company_name or not company_name.strip():
        return ResearchBrief(status="NO_SIGNALS_FOUND", signals=[], company_name="")

    clean_company = company_name.strip()
    company_domain = urlparse(company_url).netloc if company_url else None

    # --- Stage A & B: Candidate Snippet Collection ---
    raw_candidates: List[Dict[str, Any]] = []

    if mock_snippets is not None:
        for item in mock_snippets:
            if is_within_recency(item.get("published_at"), recency_days):
                raw_candidates.append(item)
    else:
        # 1. Real-Time Google News RSS Search (Zero-Config, Real-Time Dated Articles)
        try:
            rss_q = urllib.parse.quote(f"{clean_company} launch OR funding OR news OR AI")
            rss_url = f"https://news.google.com/rss/search?q={rss_q}&hl=en-US&gl=US&ceid=US:en"
            rss_res = requests.get(rss_url, headers={"User-Agent": USER_AGENT}, timeout=6.0)
            if rss_res.status_code == 200:
                root = ET.fromstring(rss_res.content)
                for item in root.findall(".//item")[:max_signals * 2]:
                    t = item.find("title").text if item.find("title") is not None else ""
                    l = item.find("link").text if item.find("link") is not None else ""
                    d = item.find("pubDate").text if item.find("pubDate") is not None else None
                    if t and l:
                        raw_candidates.append({
                            "title": t,
                            "snippet": t,
                            "source_url": l,
                            "published_at": d,
                            "source_tier": classify_source_tier(l, company_domain)
                        })
        except Exception:
            pass

        # 3. Supplement with direct company domain fetch if known
        if company_url:
            page_text = fetch_page_content_clean(company_url, timeout=8.0)
            if page_text:
                raw_candidates.append({
                    "title": f"{clean_company} Official Announcement",
                    "snippet": page_text[:800],
                    "source_url": company_url,
                    "published_at": None,
                    "source_tier": 1
                })

    # Filter by recency and sort by source tier (1 > 2 > 3)
    qualifying_candidates = [
        c for c in raw_candidates 
        if is_within_recency(c.get("published_at"), recency_days) and c.get("source_tier", 2) in (1, 2, 3)
    ]
    qualifying_candidates.sort(key=lambda x: x.get("source_tier", 2))
    bounded_candidates = qualifying_candidates[:max_signals]

    if not bounded_candidates:
        return ResearchBrief(
            status="NO_SIGNALS_FOUND",
            signals=[],
            company_name=clean_company,
            target_url=company_url
        )

    # --- Stage C: Grounded Summarization with Multi-LLM & Fallback ---
    formatted_snippets_text = "\n\n".join(
        f"Snippet {i+1} [URL: {c['source_url']}] [Tier: {c.get('source_tier', 2)}]: {c.get('snippet', '')}"
        for i, c in enumerate(bounded_candidates)
    )

    summary_text = None

    if mock_gemini_response is not None:
        summary_text = mock_gemini_response
    else:
        # Try Groq first if available for high-speed grounded summarization
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_key:
            try:
                g_url = "https://api.groq.com/openai/v1/chat/completions"
                g_headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                g_payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Summarize ONLY what is stated in the snippets into up to 3 short, factual bullet points, each ending with its source URL in parentheses. "
                                "Do not invent facts. If nothing usable, say NO_SIGNALS_FOUND."
                            )
                        },
                        {"role": "user", "content": f"SNIPPETS:\n{formatted_snippets_text}"}
                    ],
                    "temperature": 0.0,
                    "max_tokens": 512
                }
                g_res = requests.post(g_url, headers=g_headers, json=g_payload, timeout=6.0)
                if g_res.status_code == 200:
                    summary_text = g_res.json()["choices"][0]["message"]["content"].strip()
            except Exception:
                pass

        # Fallback to candidate snippet headlines if LLM call was unavailable
        if not summary_text or "NO_SIGNALS_FOUND" in summary_text.strip():
            # Build summary directly from verified candidate headlines
            summary_text = "\n".join(
                f"- {c['title']} ({c['source_url']})" for c in bounded_candidates
            )

    # --- Stage D: Hallucination Guard Verification ---
    source_texts = [c.get("snippet", "") for c in bounded_candidates]
    verified_signals: List[SignalItem] = []

    lines = [line.strip() for line in (summary_text or "").splitlines() if line.strip() and not line.strip().startswith("#")]
    for line in lines:
        clean_line = line.lstrip("•*- 1234567890.)")
        if not clean_line or len(clean_line) < 10:
            continue

        url_match = re.search(r'\((https?://[^\s\)]+)\)', clean_line)
        source_url = url_match.group(1) if url_match else bounded_candidates[0]["source_url"]
        headline = re.sub(r'\(https?://[^\s\)]+\)', '', clean_line).strip()

        # Run deterministic containment check
        passed = passes_containment_check(headline, source_texts)
        if passed:
            tier = classify_source_tier(source_url, company_domain)
            signal_type = "news"
            lower_h = headline.lower()
            if "launch" in lower_h or "unveil" in lower_h or "release" in lower_h or "introduce" in lower_h:
                signal_type = "product_launch"
            elif "fund" in lower_h or "raise" in lower_h or "series" in lower_h or "invest" in lower_h:
                signal_type = "funding"
            elif "blog" in source_url.lower() or "eng" in source_url.lower():
                signal_type = "engineering_blog"

            verified_signals.append(SignalItem(
                signal_type=signal_type,
                headline=headline,
                source_url=source_url,
                source_tier=tier,
                guard_check_passed=True
            ))

    if not verified_signals:
        return ResearchBrief(
            status="NO_SIGNALS_FOUND",
            signals=[],
            company_name=clean_company,
            target_url=company_url
        )

    return ResearchBrief(
        status="FOUND",
        signals=verified_signals[:max_signals],
        company_name=clean_company,
        target_url=company_url
    )
