"""Google Custom Search Engine (CSE) LinkedIn Employee Lookup Module (apicontracts.md §4)."""

import os
import re
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from app.scheduler import scheduler

load_dotenv()

def parse_employee_from_item(item: Dict[str, Any], company_name: str) -> Dict[str, Any]:
    """Parse title, snippet, and link from Google Custom Search JSON API response item."""
    raw_title = item.get("title", "")
    snippet = item.get("snippet", "")
    link = item.get("link", "")
    
    # 1. Clean employee name: format often "Jane Doe - SDE - Company | LinkedIn" or "Jane Doe | LinkedIn"
    name_match = re.split(r'[-–|]', raw_title)
    employee_name = name_match[0].strip() if name_match else raw_title

    # Remove trailing qualifications or parenthesis in name if any
    employee_name = re.sub(r'\s*\(.*?\)', '', employee_name).strip()

    # 2. Extract employee tagline / role headline from title or snippet
    tagline = ""
    if len(name_match) > 1:
        # middle part often has "Senior Software Engineer - Amazon"
        middle = " - ".join(part.strip() for part in name_match[1:] if "linkedin" not in part.lower())
        tagline = middle
    
    if not tagline:
        # Extract from snippet
        clean_snip = re.sub(r'^(?:View\s+[\w\s]+\'s\s+profile\s+on\s+LinkedIn[.,\s]*|[\w\s]+is\s+a\s+)', '', snippet, flags=re.IGNORECASE).strip()
        tagline = clean_snip[:150]

    return {
        "employee_name": employee_name,
        "employee_tagline": tagline or f"Software Professional at {company_name}",
        "profile_url": link,
        "referral_status": "Not Contacted"
    }

async def lookup_company_employees(
    company_name: str,
    role_family: str = "Software Engineer OR SDE OR HR OR Recruiter",
    api_key: Optional[str] = None,
    cx_id: Optional[str] = None,
    num_results: int = 4,
    mock_items: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Queries Google CSE for public indexed LinkedIn profiles without authenticated scraping.
    Routes through TokenAwareScheduler (google_cse provider).
    """
    if not company_name or not company_name.strip():
        return []

    clean_company = company_name.strip()

    if mock_items is not None:
        return [parse_employee_from_item(item, clean_company) for item in mock_items[:num_results]]

    key = api_key or os.environ.get("GOOGLE_CSE_KEY")
    cx = cx_id or os.environ.get("GOOGLE_CSE_CX")
    if not key or not cx:
        return []

    async def fetch_cse():
        query = f'site:linkedin.com/in/ "{clean_company}" AND ({role_family})'
        url = "https://customsearch.googleapis.com/customsearch/v1"
        params = {
            "key": key,
            "cx": cx,
            "q": query,
            "num": min(10, num_results)
        }
        res = requests.get(url, params=params, timeout=6.0)
        if res.status_code == 200:
            data = res.json()
            items = data.get("items", [])
            return [parse_employee_from_item(item, clean_company) for item in items[:num_results]]
        elif res.status_code == 429:
            raise RuntimeError(f"Google CSE 429: {res.text}")
        return []

    try:
        return await scheduler.execute_task("google_cse", fetch_cse)
    except Exception:
        return []
