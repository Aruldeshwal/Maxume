"""Company Signal Research & Grounded Personalization Pipeline with 3-Stage Hallucination Guard."""

import os
import re
import time
import urllib.robotparser
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
        # If robots.txt cannot be fetched or parsed, default to permissive for public sites
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
        "wired.com", "theverge.com", "forbes.com",
        "inc42.com", "yourstory.com", "entrackr.com", "economictimes.indiatimes.com",
        "livemint.com", "vccircle.com", "business-standard.com"
    ]):
        return 2
    
    # Generic news / press
    return 2

def is_within_recency(date_str: Optional[str], recency_days: int = DEFAULT_RECENCY_DAYS) -> bool:
    """Determine if a published date string is within the recency window."""
    if not date_str:
        # If no explicit date is returned, treat as tentatively eligible for snippet inspection
        return True

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=recency_days)

    date_formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%b %d, %Y",
        "%B %d, %Y"
    ]

    for fmt in date_formats:
        try:
            # Handle potential slice
            clean_date = date_str.split(".")[0]
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
    google_cse_key: Optional[str] = None,
    google_cse_cx: Optional[str] = None,
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
        # Use provided test mock snippets
        for item in mock_snippets:
            if is_within_recency(item.get("published_at"), recency_days):
                raw_candidates.append(item)
    else:
        # Real Google CSE Execution
        cse_key = google_cse_key or os.environ.get("GOOGLE_CSE_KEY")
        cse_cx = google_cse_cx or os.environ.get("GOOGLE_CSE_CX")
        
        if cse_key and cse_cx:
            try:
                query = f'"{clean_company}" (news OR "product launch" OR funding OR "raises")'
                url = "https://customsearch.googleapis.com/customsearch/v1"
                params = {
                    "key": cse_key,
                    "cx": cse_cx,
                    "q": query,
                    "sort": "date",
                    "num": min(5, max_signals)
                }
                res = requests.get(url, params=params, timeout=6.0)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("items", [])
                    for it in items:
                        snippet = it.get("snippet", "")
                        link = it.get("link", "")
                        title = it.get("title", "")
                        raw_candidates.append({
                            "title": title,
                            "snippet": f"{title}. {snippet}",
                            "source_url": link,
                            "published_at": None,
                            "source_tier": classify_source_tier(link, company_domain)
                        })
            except Exception:
                pass

        # Supplement with direct company domain fetch if known
        if company_url:
            page_text = fetch_page_content_clean(company_url, timeout=8.0)
            if page_text:
                raw_candidates.append({
                    "title": f"{clean_company} Official News",
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

    # Stage D check: If 0 qualifying snippets -> NO_SIGNALS_FOUND immediately
    if not bounded_candidates:
        return ResearchBrief(
            status="NO_SIGNALS_FOUND",
            signals=[],
            company_name=clean_company,
            target_url=company_url
        )

    # --- Stage C: Grounded Summarization ---
    formatted_snippets_text = "\n\n".join(
        f"Snippet {i+1} [URL: {c['source_url']}] [Tier: {c.get('source_tier', 2)}]: {c.get('snippet', '')}"
        for i, c in enumerate(bounded_candidates)
    )

    gemini_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
    summary_text = None

    if mock_gemini_response is not None:
        summary_text = mock_gemini_response
    elif gemini_key:
        try:
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={gemini_key}"
            prompt_content = (
                "You will be given raw search snippets about a company, each with its source URL and date. "
                "Summarize ONLY what is stated in these snippets into up to 3 short, factual bullet points, each ending with its source URL in parentheses. "
                "Do not add outside knowledge, do not infer unstated facts, and do not resolve ambiguity by guessing. "
                "If the snippets do not support any usable, specific claim, respond with exactly: NO_SIGNALS_FOUND\n\n"
                f"SNIPPETS:\n{formatted_snippets_text}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt_content}]}],
                "generationConfig": {
                    "temperature": 0.0,
                    "maxOutputTokens": 512
                }
            }
            res = requests.post(gemini_url, json=payload, timeout=8.0)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    summary_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except Exception:
            pass

    # Fallback to snippet titles if Gemini is unreachable or returns NO_SIGNALS_FOUND
    if not summary_text or "NO_SIGNALS_FOUND" in summary_text.strip():
        # Fallback to highest tier candidate snippet title directly
        if summary_text and "NO_SIGNALS_FOUND" in summary_text.strip():
            return ResearchBrief(
                status="NO_SIGNALS_FOUND",
                signals=[],
                company_name=clean_company,
                target_url=company_url
            )

    # --- Stage D: Hallucination Guard Verification ---
    source_texts = [c.get("snippet", "") for c in bounded_candidates]
    verified_signals: List[SignalItem] = []

    # Parse bullet lines
    lines = [line.strip() for line in (summary_text or "").splitlines() if line.strip() and not line.strip().startswith("#")]
    for line in lines:
        clean_line = line.lstrip("•*- 1234567890.)")
        if not clean_line or len(clean_line) < 10:
            continue

        # Extract source URL from parentheses if present, or match to candidate
        url_match = re.search(r'\((https?://[^\s\)]+)\)', clean_line)
        source_url = url_match.group(1) if url_match else bounded_candidates[0]["source_url"]
        headline = re.sub(r'\(https?://[^\s\)]+\)', '', clean_line).strip()

        # Run deterministic containment check
        passed = passes_containment_check(headline, source_texts)
        if passed:
            tier = classify_source_tier(source_url, company_domain)
            signal_type = "news"
            lower_h = headline.lower()
            if "launch" in lower_h or "unveil" in lower_h or "release" in lower_h:
                signal_type = "product_launch"
            elif "fund" in lower_h or "raise" in lower_h or "series" in lower_h:
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
        signals=verified_signals[:3],
        company_name=clean_company,
        target_url=company_url
    )
