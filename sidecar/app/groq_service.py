"""Groq High-Speed LPU Creative Generation Service with Strict Grounding Constraints (apicontracts.md §3)."""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from app.scheduler import scheduler
from app.company_research import ResearchBrief

load_dotenv()

CANDIDATE_GROQ_MODELS = [
    os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768"
]

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

    async def _execute_groq_completion(self, user_content: str, max_tokens: int = 1024) -> str:
        key = self.api_key or os.environ.get("GROQ_API_KEY", "")
        if not key:
            raise RuntimeError("GROQ_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

        for model_name in CANDIDATE_GROQ_MODELS:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_GROUNDING_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.7,
                "max_tokens": max_tokens,
                "stream": False
            }
            try:
                res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=12.0)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"].strip()
                elif res.status_code == 429:
                    raise RuntimeError(f"Groq 429: {res.text}")
                elif res.status_code == 400 and ("decommissioned" in res.text or "invalid_request_error" in res.text):
                    # Try next candidate model
                    continue
                else:
                    continue
            except RuntimeError as r_err:
                if "429" in str(r_err):
                    raise r_err
            except Exception:
                continue

        raise RuntimeError("All Groq candidate models failed or unavailable.")

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
            try:
                return await self._execute_groq_completion(user_content, max_tokens=1024)
            except Exception:
                # Fallback to high-quality template
                return (
                    f"Dear Hiring Team at {company_name},\n\n"
                    f"I am writing to express my strong enthusiasm for the {role_title} position. "
                    f"With a proven track record in engineering scalable architectures and low-latency systems, "
                    f"I am eager to contribute to your engineering organization.\n\n"
                    f"Key technical achievements include:\n"
                    f"{bullets_str}\n\n"
                    f"I look forward to discussing how my experience aligns with your team's goals.\n\n"
                    f"Sincerely,\nCandidate"
                )

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
            try:
                return await self._execute_groq_completion(user_content, max_tokens=512)
            except Exception:
                return (
                    f"Hi {employee_name}, I came across your work as {employee_tagline} at {company_name} and was really impressed. "
                    f"I am applying for the {role_title} opening. With hands-on experience in high-scale systems, "
                    f"I'd love to connect briefly or ask for your referral if you're open to it. Thank you for your time!"
                )

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
            try:
                return await self._execute_groq_completion(user_content, max_tokens=1024)
            except Exception:
                return (
                    f"Subject: Application: {role_title} - Engineering Candidate\n\n"
                    f"Hi Team,\n\n"
                    f"I am excited to apply for the {role_title} opening at {company_name}. "
                    f"My background centers on architecting resilient backend systems and deploying production-ready services:\n\n"
                    f"{bullets_str}\n\n"
                    f"I have attached my resume and would welcome the opportunity to discuss how I can add immediate value to {company_name}.\n\n"
                    f"Best regards,\nCandidate"
                )

        return await scheduler.execute_task("groq", call_groq)

groq_service = GroqService()
