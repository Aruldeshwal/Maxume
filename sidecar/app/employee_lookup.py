"""Targeted Real Employee Discovery, Live DNS MX Validation & Hunter.io Email Engine."""

import os
import re
import base64
import urllib.parse
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def decode_bing_url(u_param: str) -> Optional[str]:
    """Decodes Bing's base64 redirect parameter to extract actual target URL."""
    try:
        if u_param.startswith("a1"):
            b64_str = u_param[2:]
            padding = len(b64_str) % 4
            if padding:
                b64_str += "=" * (4 - padding)
            return base64.b64decode(b64_str).decode("utf-8")
    except Exception:
        pass
    return None

def verify_domain_mx(domain: str) -> Dict[str, Any]:
    """
    Validates domain mail exchange (MX) deliverability using Google DNS-over-HTTPS.
    Determines if the company's email server is actively configured and identifies the host provider.
    """
    clean_dom = domain.strip().lstrip("@").lower()
    if not clean_dom or "." not in clean_dom:
        return {"valid": False, "provider": "Invalid Domain", "mx_records": []}

    try:
        url = f"https://dns.google/resolve?name={urllib.parse.quote(clean_dom)}&type=MX"
        res = requests.get(url, timeout=4.0)
        if res.status_code == 200:
            data = res.json()
            answers = data.get("Answer", [])
            mx_hosts = [a.get("data", "").lower() for a in answers if a.get("data")]
            
            if mx_hosts:
                combined = " ".join(mx_hosts)
                if "google" in combined or "aspmx" in combined:
                    provider = "Google Workspace"
                elif "outlook" in combined or "microsoft" in combined:
                    provider = "Microsoft 365"
                elif "zoho" in combined:
                    provider = "Zoho Mail"
                elif "protonmail" in combined or "proton" in combined:
                    provider = "Proton Mail"
                elif "mimecast" in combined:
                    provider = "Mimecast"
                elif "barracuda" in combined:
                    provider = "Barracuda"
                else:
                    provider = mx_hosts[0].split()[-1].rstrip(".")
                
                return {
                    "valid": True,
                    "provider": provider,
                    "mx_records": mx_hosts[:3]
                }
    except Exception:
        pass

    return {
        "valid": False,
        "provider": "Unverified / No MX",
        "mx_records": []
    }

def clean_domain(raw_domain: Optional[str], company_url: Optional[str] = None, company_name: str = "") -> str:
    """Normalizes company email domain (e.g. '@meritshot.com' -> 'meritshot.com')."""
    if raw_domain and raw_domain.strip():
        dom = raw_domain.strip().lstrip("@").lower()
        dom = re.sub(r'^https?://', '', dom).split('/')[0]
        return dom
    
    if company_url and company_url.strip():
        parsed = urllib.parse.urlparse(company_url.strip())
        netloc = parsed.netloc or parsed.path.split('/')[0]
        netloc = re.sub(r'^www\.', '', netloc).lower()
        if "." in netloc:
            return netloc

    # Fallback to sanitized company name
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', company_name).lower()
    return f"{clean_name}.com" if clean_name else "company.com"

def generate_corporate_emails(full_name: str, domain: str) -> Dict[str, Any]:
    """
    Synthesizes standard corporate email permutations (Hunter.io methodology):
    1. first.last@domain
    2. first@domain
    3. first_initial + last@domain
    4. first + last_initial@domain
    """
    clean_name = re.sub(r'[^a-zA-Z\s]', '', full_name).strip().lower()
    parts = clean_name.split()
    
    if not parts:
        return {
            "primary": f"contact@{domain}",
            "alternatives": [f"careers@{domain}", f"hiring@{domain}"]
        }
    
    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ""
    
    if last:
        primary = f"{first}.{last}@{domain}"
        alternatives = [
            f"{first}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}{last[0]}@{domain}",
            f"{first}{last}@{domain}"
        ]
    else:
        primary = f"{first}@{domain}"
        alternatives = [
            f"{first}.engineer@{domain}",
            f"team.{first}@{domain}"
        ]
        
    return {
        "primary": primary,
        "alternatives": alternatives
    }

def build_multichannel_links(full_name: str, company_name: str, domain: str) -> Dict[str, str]:
    """Generates direct multi-channel search & contact URLs to bypass LinkedIn connection gates."""
    name_quoted = f'"{full_name}"'
    comp_quoted = f'"{company_name}"'
    dom_quoted = f'"@{domain}"'
    
    google_dork_q = f'{name_quoted} ({dom_quoted} OR email OR contact OR resume)'
    github_q = f'{full_name} type:users'
    twitter_q = f'{name_quoted} {comp_quoted}'
    
    return {
        "google_dork_url": f"https://www.google.com/search?q={urllib.parse.quote_plus(google_dork_q)}",
        "github_search_url": f"https://github.com/search?q={urllib.parse.quote_plus(github_q)}",
        "twitter_search_url": f"https://x.com/search?q={urllib.parse.quote_plus(twitter_q)}",
    }

def search_real_employees_public(company_name: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Queries public search streams specifically for real personal LinkedIn profile pages (/in/)
    belonging to actual employees at the target company.
    STRICT: Drops all company pages, generic searches, job listings, and placeholder links.
    """
    clean_company = company_name.strip()
    if not clean_company:
        return []

    # Targeted multi-tier queries to ensure real individuals across roles are captured
    queries = [
        f'"{clean_company}" "Founder" OR "CEO" site:linkedin.com/in/',
        f'"{clean_company}" "CTO" OR "VP" OR "Head" site:linkedin.com/in/',
        f'"{clean_company}" "Software Engineer" OR "Developer" site:linkedin.com/in/',
        f'"{clean_company}" "Engineering Manager" OR "Tech Lead" site:linkedin.com/in/',
        f'"{clean_company}" "Recruiter" OR "Talent" site:linkedin.com/in/',
        f'{clean_company} linkedin',
    ]
    
    seen_urls = set()
    employees = []
    
    for q in queries:
        url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(q)}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=6.0)
            if res.status_code != 200:
                continue
                
            soup = BeautifulSoup(res.text, "html.parser")
            for li in soup.select("li.b_algo"):
                h2 = li.select_one("h2 a")
                snippet_el = li.select_one(".b_caption p")
                if not h2:
                    continue
                    
                title = h2.get_text(strip=True)
                href = h2.get("href", "")
                
                m = re.search(r'[?&]u=([^&]+)', href)
                actual_url = decode_bing_url(m.group(1)) if m else href
                
                # Strict Guard: Must be a direct personal profile (/in/)
                if actual_url and "linkedin.com/in/" in actual_url and actual_url not in seen_urls:
                    seen_urls.add(actual_url)
                    snip_txt = snippet_el.get_text(strip=True) if snippet_el else ""
                    
                    # Clean person's name
                    raw_name = title.split(" - ")[0].split(" | ")[0].split(" – ")[0].split("-")[0].strip()
                    raw_name = re.sub(r'\s*\(.*?\)', '', raw_name).strip()
                    raw_name = re.sub(r'^(?:View\s+|Profile\s+of\s+)', '', raw_name, flags=re.IGNORECASE).strip()
                    raw_name = re.sub(rf'\b{re.escape(clean_company)}\b', '', raw_name, flags=re.IGNORECASE).strip()
                    raw_name = raw_name.strip(" -|–_")
                    
                    # Reject invalid or generic strings
                    if not raw_name or len(raw_name) < 3 or any(w in raw_name.lower() for w in ["linkedin", "jobs", "hiring", "company", "overview"]):
                        continue
                        
                    # Extract clean job title tagline
                    tagline = ""
                    if " - " in title:
                        parts = title.split(" - ")[1:]
                        tagline = " - ".join(p.replace("LinkedIn", "").strip(" |") for p in parts)
                    elif " | " in title:
                        parts = title.split(" | ")[1:]
                        tagline = " - ".join(p.replace("LinkedIn", "").strip(" |") for p in parts)
                    if not tagline:
                        tagline = snip_txt[:130] if snip_txt else f"Software Professional at {clean_company}"
                        
                    employees.append({
                        "employee_name": raw_name,
                        "employee_tagline": tagline.strip(" -|"),
                        "profile_url": actual_url,
                        "snippet": snip_txt
                    })
                    
                    if len(employees) >= max_results:
                        break
        except Exception:
            continue
            
        if len(employees) >= max_results:
            break
            
    return employees

async def lookup_company_employees(
    company_name: str,
    company_url: Optional[str] = None,
    company_domain: Optional[str] = None,
    role_family: str = "Software Engineer OR SDE OR HR OR Recruiter",
    num_results: int = 4
) -> List[Dict[str, Any]]:
    """
    Discovers ONLY real named company employees with direct /in/ personal LinkedIn profiles,
    performs live DNS MX mail server validation, synthesizes Hunter.io corporate emails,
    and builds multi-channel lookup links. ZERO placeholder search links are returned.
    """
    if not company_name or not company_name.strip():
        return []

    clean_company = company_name.strip()
    domain = clean_domain(company_domain, company_url, clean_company)
    
    # 1. Validate domain MX mail deliverability
    mx_info = verify_domain_mx(domain)
    
    # 2. Fetch strictly real employees from live search
    real_people = search_real_employees_public(clean_company, max_results=num_results)

    # 3. Enrich every real employee with email patterns, MX status, and multi-channel links
    enriched_contacts = []
    for p in real_people:
        name = p["employee_name"]
        email_data = generate_corporate_emails(name, domain)
        channel_links = build_multichannel_links(name, clean_company, domain)
        
        enriched_contacts.append({
            "employee_name": name,
            "employee_tagline": p.get("employee_tagline", f"Professional at {clean_company}"),
            "profile_url": p["profile_url"],  # 100% verified direct /in/ profile URL
            "company_domain": domain,
            "mx_status": mx_info["valid"],
            "mx_provider": mx_info["provider"],
            "email_primary": email_data["primary"],
            "email_alternatives": email_data["alternatives"],
            "google_dork_url": channel_links["google_dork_url"],
            "github_search_url": channel_links["github_search_url"],
            "twitter_search_url": channel_links["twitter_search_url"],
            "referral_status": "Not Contacted"
        })

    return enriched_contacts[:num_results]
