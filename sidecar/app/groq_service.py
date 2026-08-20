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
    os.environ.get("GROQ_MODEL", "qwen/qwen3.6-27b"),
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "groq/compound"
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

        async def _call_groq():
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
                        raw_text = data["choices"][0]["message"]["content"].strip()
                        cleaned_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
                        return cleaned_text
                    elif res.status_code == 429:
                        raise RuntimeError(f"Groq 429: {res.text}")
                    elif res.status_code in [400, 404] and ("decommissioned" in res.text or "invalid_request_error" in res.text or "not_found" in res.text):
                        continue
                    else:
                        continue
                except RuntimeError as r_err:
                    if "429" in str(r_err):
                        raise r_err
                except Exception:
                    continue

            raise RuntimeError("All Groq candidate models failed or unavailable.")

        return await scheduler.execute_task("groq", _call_groq)

    def _format_research_brief(self, brief: Optional[ResearchBrief]) -> str:
        if not brief:
            return (
                "Company Mission: Engineering scalable software products.\n"
                "Industry Domain: Enterprise Software & Cloud Platforms\n"
                "Core Technical Priorities: Scalable Full-Stack Architecture, High-Throughput Performance"
            )

        lines = [
            f"Company Mission & Product: {brief.company_summary or 'Developing scalable software solutions.'}",
            f"Industry Domain: {brief.industry_domain}",
            f"Core Technical Priorities: {', '.join(brief.technical_priorities) if brief.technical_priorities else 'Full-Stack Architecture, High-Throughput Performance'}"
        ]
        if brief.signals:
            lines.append("Verified Recent Milestones:")
            for s in brief.signals[:2]:
                lines.append(f"- {s.headline} ({s.source_url})")
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
        Generates grounded 280-word cover letter using the Architectural Bridge Framework.
        Directly connects candidate's verified codebase projects to company challenges.
        """
        if mock_response is not None:
            return mock_response

        brief_str = self._format_research_brief(research_brief)
        bullets_str = "\n".join(f"• {b}" for b in resume_bullets)

        domain_str = research_brief.industry_domain if research_brief else "Technology"
        priority_str = research_brief.technical_priorities[0] if research_brief and research_brief.technical_priorities else "scalable architecture"

        user_content = (
            f"You are an elite career strategist and software engineering director. "
            f"Write a prestigious, 280-word technical Cover Letter applying for {role_title} at {company_name}.\n\n"
            f"COMPANY INTELLIGENCE & ARCHITECTURAL CONTEXT:\n{brief_str}\n\n"
            f"CANDIDATE CODEBASE PROOFS OF WORK (VERIFIED PROJECTS):\n{bullets_str}\n\n"
            f"CRITICAL ARCHITECTURAL BRIDGE INSTRUCTIONS:\n"
            f"1. DO NOT use generic filler phrases like 'I am writing with great enthusiasm' or 'Please accept my application'.\n"
            f"2. Paragraph 1 (The Hook): Empathize with {company_name}'s specific product mission in {domain_str} and their need for robust engineering around {priority_str}.\n"
            f"3. Paragraph 2 & 3 (The Architectural Parallel): Draw direct 1-to-1 parallels between the candidate's verified projects (e.g. Maxume, Metro-Connect, EzNotes) and {company_name}'s technical bottlenecks. Explain HOW the candidate handled concurrency, decoupled client-sidecar IPC, or atomic state synchronization.\n"
            f"4. Paragraph 4 (The Day 1 Close): High-confidence statement on how the candidate will help ship reliable features from Day 1.\n"
            f"5. NO fake percentage metrics. Focus strictly on system design, data integrity, and engineering mechanics.\n"
            f"6. Do not include thinking tags. Output the final letter immediately."
        )

        async def call_groq():
            try:
                return await self._execute_groq_completion(user_content, max_tokens=1200)
            except Exception:
                return (
                    f"Dear Hiring Team at {company_name},\n\n"
                    f"As {company_name} continues scaling its product architecture in {domain_str}, delivering robust, low-latency software becomes essential to maintaining user velocity.\n\n"
                    f"My engineering background directly aligns with your core technical priorities. When developing full-stack architectures, I focus heavily on concurrency safety, atomic state updates, and decoupled system design:\n\n"
                    f"{bullets_str}\n\n"
                    f"I am eager to bring this exact focus on concurrency, robust system architecture, and clean full-stack design to {company_name}'s engineering organization.\n\n"
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
        Generates a 120-word high-impact direct application email using the Day 1 Value Pitch framework.
        """
        if mock_response is not None:
            return mock_response

        brief_str = self._format_research_brief(research_brief)
        bullets_str = "\n".join(f"• {b}" for b in resume_bullets[:2])
        domain_str = research_brief.industry_domain if research_brief else "Technology"

        user_content = (
            f"Draft a high-impact, 120-word direct outbound application email (Subject Line + Body) applying for {role_title} at {company_name}.\n"
            f"COMPANY CONTEXT:\n{brief_str}\n\n"
            f"CANDIDATE HIGHLIGHTS:\n{bullets_str}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Subject line should be punchy and technical (e.g. 'Application: {role_title} - Full-Stack & Concurrency Architecture').\n"
            f"2. Hook: Acknowledge {company_name}'s mission in {domain_str}.\n"
            f"3. Value Add: Reference candidate's verified projects.\n"
            f"4. Call to Action: Clean 15-minute conversation request.\n"
            f"5. Do not include thinking tags. Output final email immediately."
        )

        async def call_groq():
            try:
                return await self._execute_groq_completion(user_content, max_tokens=600)
            except Exception:
                return (
                    f"Subject: Application: {role_title} - Engineering Candidate\n\n"
                    f"Hi Team,\n\n"
                    f"I am reaching out regarding the {role_title} opening at {company_name}. "
                    f"As your team expands its platform in {domain_str}, I bring hands-on experience architecting resilient, low-latency systems:\n\n"
                    f"{bullets_str}\n\n"
                    f"I have attached my resume and would welcome a brief conversation to explore how I can contribute to your engineering goals.\n\n"
                    f"Best regards,\nCandidate"
                )

        return await scheduler.execute_task("groq", call_groq)

groq_service = GroqService()
