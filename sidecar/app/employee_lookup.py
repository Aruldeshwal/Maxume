"""Targeted LinkedIn Networking & Employee Discovery Module (apicontracts.md §4)."""

import os
import re
import urllib.parse
from typing import List, Dict, Any, Optional

def parse_employee_from_item(item: Dict[str, Any], company_name: str) -> Dict[str, Any]:
    """Parse title, snippet, and link from item."""
    raw_title = item.get("title", "")
    snippet = item.get("snippet", "")
    link = item.get("link", "")
    
    name_match = re.split(r'[-–|]', raw_title)
    employee_name = name_match[0].strip() if name_match else raw_title
    employee_name = re.sub(r'\s*\(.*?\)', '', employee_name).strip()

    tagline = ""
    if len(name_match) > 1:
        middle = " - ".join(part.strip() for part in name_match[1:] if "linkedin" not in part.lower())
        tagline = middle
    
    if not tagline:
        clean_snip = re.sub(r'^(?:View\s+[\w\s]+\'s\s+profile\s+on\s+LinkedIn[.,\s]*|[\w\s]+is\s+a\s+)', '', snippet, flags=re.IGNORECASE).strip()
        tagline = clean_snip[:150]

    return {
        "employee_name": employee_name,
        "employee_tagline": tagline or f"Software Professional at {company_name}",
        "profile_url": link,
        "referral_status": "Not Contacted"
    }

def generate_targeted_networking_personas(company_name: str) -> List[Dict[str, Any]]:
    """
    Generates high-priority targeted employee referral personas with direct LinkedIn search links
    for senior engineering and talent leads.
    """
    clean = company_name.strip()
    encoded = urllib.parse.quote(clean)

    personas = [
        {
            "employee_name": f"{clean} Senior Engineer / Tech Lead",
            "employee_tagline": f"Senior Software Engineer • Distributed Systems & Full Stack at {clean}",
            "profile_url": f"https://www.linkedin.com/search/results/people/?keywords={encoded}%20Software%20Engineer",
            "referral_status": "Not Contacted"
        },
        {
            "employee_name": f"{clean} Engineering Manager",
            "employee_tagline": f"Engineering Manager • Core Infrastructure & Applications at {clean}",
            "profile_url": f"https://www.linkedin.com/search/results/people/?keywords={encoded}%20Engineering%20Manager",
            "referral_status": "Not Contacted"
        },
        {
            "employee_name": f"{clean} Technical Recruiter",
            "employee_tagline": f"University & Technical Talent Partner at {clean}",
            "profile_url": f"https://www.linkedin.com/search/results/people/?keywords={encoded}%20Recruiter",
            "referral_status": "Not Contacted"
        }
    ]
    return personas

async def lookup_company_employees(
    company_name: str,
    role_family: str = "Software Engineer OR SDE OR HR OR Recruiter",
    num_results: int = 3,
    mock_items: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Discovers targeted employee referral contacts and direct LinkedIn search targets.
    """
    if not company_name or not company_name.strip():
        return []

    clean_company = company_name.strip()

    if mock_items is not None:
        return [parse_employee_from_item(item, clean_company) for item in mock_items[:num_results]]

    return generate_targeted_networking_personas(clean_company)[:num_results]
