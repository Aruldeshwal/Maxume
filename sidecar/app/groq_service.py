"""Groq High-Speed LPU Creative Generation Service with Strict Grounding Constraints (apicontracts.md §3)."""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from app.scheduler import scheduler
from app.company_research import ResearchBrief

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-specdec"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_GROUNDING_PROMPT = (
    "You are an expert technical resume coach and career counselor. "
    "Generate persuasive, professional job application assets. "
    "You may only reference the company facts listed under RESEARCH_BRIEF below; "
    "if RESEARCH_BRIEF is empty or NO_SIGNALS_FOUND, write a strong letter based on the role and candidate background alone "
    "and do not invent or imply any company-specific news, launches, or milestones."
)

class GroqService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")

    def _format_research_brief(self, brief: Optional[ResearchBrief]) -> str:
        if not brief or brief.status != "FOUND" or not brief.signals:
            return "NO_SIGNALS_FOUND"
        lines = []
        for s in brief.signals:
            lines.append(f"- {s.headline} (Source: {s.source_url})")
        return "\n".join(lines)

    async def generate_cover_letter(
        self,
        company_name: str,
        role_title: str,
        resume_bullets: List[str],
        research_brief: Optional[ResearchBrief] = None,
        mock_response: Optional[str] = None
    ) -> str:
        """
        Generates grounded 300-word cover letter via Groq LPU with grounding constraint.
        """
        if mock_response is not None:
            return mock_response

        brief_str = self._format_research_brief(research_brief)
        bullets_str = "\n".join(f"• {b}" for b in resume_bullets)

        user_content = (
            f"Create a 300-word cover letter for a {role_title} role at {company_name}.\n"
            f"My resume highlights:\n{bullets_str}\n\n"
            f"RESEARCH_BRIEF:\n{brief_str}"
        )

        async def call_groq():
            key = self.api_key or os.environ.get("GROQ_API_KEY", "")
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_GROUNDING_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
                "stream": False
            }
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10.0)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
            elif res.status_code == 429:
                raise RuntimeError(f"Groq 429: {res.text}")
            else:
                raise RuntimeError(f"Groq error: {res.status_code} - {res.text}")

        return await scheduler.execute_task("groq", call_groq)

    async def generate_referral_pitch(
        self,
        employee_name: str,
        employee_tagline: str,
        company_name: str,
        role_title: str,
        resume_bullets: List[str],
        research_brief: Optional[ResearchBrief] = None,
        mock_response: Optional[str] = None
    ) -> str:
        """
        Generates a concise 75-word LinkedIn referral message to a current employee.
        """
        if mock_response is not None:
            return mock_response

        brief_str = self._format_research_brief(research_brief)
        bullets_str = "\n".join(f"• {b}" for b in resume_bullets[:2])

        user_content = (
            f"Write a concise, professional 75-word LinkedIn referral message to {employee_name} ({employee_tagline}) at {company_name}. "
            f"I am applying for {role_title}.\n"
            f"My key background highlights:\n{bullets_str}\n\n"
            f"RESEARCH_BRIEF:\n{brief_str}"
        )

        async def call_groq():
            key = self.api_key or os.environ.get("GROQ_API_KEY", "")
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_GROUNDING_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.7,
                "max_tokens": 512,
                "stream": False
            }
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10.0)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
            elif res.status_code == 429:
                raise RuntimeError(f"Groq 429: {res.text}")
            else:
                raise RuntimeError(f"Groq error: {res.status_code} - {res.text}")

        return await scheduler.execute_task("groq", call_groq)

    async def generate_application_email(
        self,
        company_name: str,
        role_title: str,
        resume_bullets: List[str],
        research_brief: Optional[ResearchBrief] = None,
        mock_response: Optional[str] = None
    ) -> str:
        """
        Generates an outbound application email with subject line and body.
        """
        if mock_response is not None:
            return mock_response

        brief_str = self._format_research_brief(research_brief)
        bullets_str = "\n".join(f"• {b}" for b in resume_bullets)

        user_content = (
            f"Draft a compelling, direct application email (subject line + body) applying for {role_title} at {company_name}.\n"
            f"My top achievements:\n{bullets_str}\n\n"
            f"RESEARCH_BRIEF:\n{brief_str}"
        )

        async def call_groq():
            key = self.api_key or os.environ.get("GROQ_API_KEY", "")
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_GROUNDING_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
                "stream": False
            }
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10.0)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
            elif res.status_code == 429:
                raise RuntimeError(f"Groq 429: {res.text}")
            else:
                raise RuntimeError(f"Groq error: {res.status_code} - {res.text}")

        return await scheduler.execute_task("groq", call_groq)

groq_service = GroqService()
