"""Groq High-Speed LPU Creative Generation Service with Humanized Tone & Anti-AI Blacklist."""

import os
import re
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from app.scheduler import scheduler
from app.company_research import ResearchBrief

load_dotenv()

CANDIDATE_GROQ_MODELS = [
    os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
    "openai/gpt-oss-20b",
    "groq/compound",
    "qwen/qwen3.6-27b"
]

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_HUMAN_ENGINEER_PROMPT = (
    "You are an articulate, pragmatic software engineer writing directly to another engineer or hiring manager. "
    "CRITICAL DIRECTIVE: You must output ONLY the final copy-pastable text. "
    "NEVER output your internal thinking, reasoning process, chain of thought, outline, draft notes, or meta-commentary. "
    "Start immediately with the greeting (e.g. 'Hi team at...') or subject line. "
    "You communicate casually yet technically, with zero corporate jargon, zero marketing fluff, and zero robotic filler. "
    "You speak openly about real engineering friction, race conditions, architecture decisions, and concrete solutions. "
    "You never invent fake metrics or hallucinate technologies."
)

ANTI_AI_FORBIDDEN_BUZZWORDS = [
    "delve", "testament", "tapestry", "beacon", "foster", "synergy", "spearheaded",
    "seamless", "pivotal", "testament to", "in today's fast-paced landscape",
    "thrilled to apply", "dynamic ecosystem", "cognitive friction", "pedagogical flow",
    "non-negotiable", "passionate about", "moreover", "furthermore", "in addition",
    "allow me to introduce", "pleased to submit", "fervent", "ardent", "harnessing the power"
]

def clean_thinking_and_preamble(raw_text: str) -> str:
    """Bulletproof extractor that eliminates any reasoning/thinking tokens or preamble."""
    text = raw_text.strip()
    
    # 1. Strip standard <think>...</think> tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    
    # 2. If <think> was unclosed (token truncation), remove everything from <think>
    if "<think>" in text:
        text = re.sub(r'<think>.*', '', text, flags=re.DOTALL).strip()

    # 3. Strip markdown thought headers
    thought_patterns = [
        r"(?i)^(?:Here(?:'s| is) (?:a )?(?:thinking process|plan|breakdown|draft):.*?\n\n)",
        r"(?i)^(?:Thinking Process:.*?\n\n)",
        r"(?i)^(?:###\s*(?:Thinking|Analysis|Plan|Breakdown|Notes).*?\n\n)",
        r"(?i)^(?:1\.\s*Analyze User Input.*?\n\n)"
    ]
    for pat in thought_patterns:
        text = re.sub(pat, '', text, flags=re.DOTALL).strip()

    # 4. If text contains markers like "Here is the cover letter:", slice to the actual content
    letter_start_markers = [
        r"(?i)\n(?:Here is the (?:cover letter|email|pitch|letter):)\s*\n+",
        r"(?i)\n(?:Cover Letter:)\s*\n+",
        r"(?i)\n(?:Subject: [^\n]+)\n+",
        r"(?i)\n(?:Dear [^\n]+,)\n+",
        r"(?i)\n(?:Hi [^\n]+,)\n+",
        r"(?i)\n(?:Hello [^\n]+,)\n+"
    ]
    for marker in letter_start_markers:
        match = re.search(marker, text)
        if match and match.start() > 0:
            prefix = text[:match.start()]
            if any(k in prefix.lower() for k in ["think", "analyze", "deconstruct", "draft", "step 1", "constraints"]):
                text = text[match.start():].strip()
                text = re.sub(r'(?i)^(?:Here is the (?:cover letter|email|pitch|letter):)\s*', '', text).strip()
                text = re.sub(r'(?i)^(?:Cover Letter:)\s*', '', text).strip()
                break

    # 5. If it starts with common greeting or Subject, ensure no lingering preamble
    if not (text.startswith("Hi ") or text.startswith("Dear ") or text.startswith("Subject: ") or text.startswith("Hello ")):
        greeting_match = re.search(r'(?m)^(Hi |Dear |Subject: |Hello |To )', text)
        if greeting_match and greeting_match.start() > 0:
            candidate_clean = text[greeting_match.start():].strip()
            if len(candidate_clean) > 80:
                text = candidate_clean

    return text

class GroqService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")

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

    def _format_candidate_projects(self, projects: List[Dict[str, Any]]) -> str:
        if not projects:
            return "No specific projects provided."
        
        project_blocks = []
        for p in projects[:3]:
            name = p.get("name") or p.get("title") or "Engineering Project"
            stack = p.get("tech_stack") or ", ".join(p.get("tags", [])) or "Full Stack"
            gh_url = p.get("github_url") or p.get("repo_url") or ""
            demo_url = p.get("live_demo_url") or ""
            
            bullets = p.get("bullets", [])
            bullet_text = " ".join(bullets[:2]) if bullets else "Engineered core modules with robust concurrency and state management."

            block = (
                f"- Project: {name} ({stack})\n"
                f"  GitHub: {gh_url or 'N/A'}\n"
                f"  Live Demo: {demo_url or 'N/A'}\n"
                f"  Engineering Focus: {bullet_text}"
            )
            project_blocks.append(block)

        return "\n".join(project_blocks)

    async def _execute_groq_completion(self, user_content: str, max_tokens: int = 1500) -> str:
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
                        {"role": "system", "content": SYSTEM_HUMAN_ENGINEER_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    "temperature": 0.3,
                    "max_tokens": max_tokens,
                    "stream": False
                }
                try:
                    res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=14.0)
                    if res.status_code == 200:
                        data = res.json()
                        raw_text = data["choices"][0]["message"]["content"].strip()
                        cleaned_text = clean_thinking_and_preamble(raw_text)
                        if cleaned_text:
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

    async def generate_cover_letter(
        self,
        company_name: str,
        role_title: str,
        resume_bullets: List[str] = [],
        projects: Optional[List[Dict[str, Any]]] = None,
        research_brief: Optional[ResearchBrief] = None,
        pitch_style: str = "deep_dive",
        mock_response: Optional[str] = None
    ) -> str:
        """
        Generates humanized Cover Letter with exact engineering mechanics and live links.
        Supports 3 pitch styles: 'deep_dive', 'scannable', 'executive'.
        """
        if mock_response is not None:
            return mock_response

        brief_str = self._format_research_brief(research_brief)
        project_context = self._format_candidate_projects(projects or [])
        if not projects and resume_bullets:
            project_context = "\n".join(f"• {b}" for b in resume_bullets)

        domain_str = research_brief.industry_domain if research_brief else "Technology"
        priority_str = research_brief.technical_priorities[0] if research_brief and research_brief.technical_priorities else "scalable full-stack architecture"

        style_instruction = ""
        if pitch_style == "scannable":
            style_instruction = (
                "FORMAT: 3-Part Structured Matrix for Fast Technical Scanning:\n"
                "1. Platform Alignment (2 sentences on why candidate maps to company's stack/goals)\n"
                "2. Verified Proofs of Work (Bold project names with direct GitHub/Live URLs and 2 technical bullet points each detailing what was built and how concurrency/state was handled)\n"
                "3. Immediate Day 1 Contribution (2 sentences on exact problems candidate can solve on day one)."
            )
        elif pitch_style == "executive":
            style_instruction = (
                "FORMAT: 4-Sentence Ultra-Dense Executive Pitch for Founders & VPs:\n"
                "- Sentence 1: Direct technical match for role & company challenge.\n"
                "- Sentence 2: Core proof of work with concrete mechanics from Project 1 + active live demo/GitHub link.\n"
                "- Sentence 3: Second architecture proof of work (IPC, DB transactions, or concurrency).\n"
                "- Sentence 4: Low-friction 10-minute sync invite."
            )
        else: # deep_dive
            style_instruction = (
                "FORMAT: 3-Paragraph Conversational Engineering Deep-Dive for Tech Leads & Engineering Managers:\n"
                "- Paragraph 1: Humanized opening on company's product in {domain_str} and why their engineering challenges (e.g. {priority_str}) are interesting.\n"
                "- Paragraph 2: Story of building Project 1 — what broke, why concurrency/state sync was hard, how you solved it, and naturally embed the GitHub or live demo URL.\n"
                "- Paragraph 3: Second project architecture (sidecar IPC, atomic DB transactions, or optimistic UI), followed by a 1-sentence engineering proposal for {company_name}'s platform and a direct, confident close."
            )

        forbidden_str = ", ".join(ANTI_AI_FORBIDDEN_BUZZWORDS)

        user_content = (
            f"Write an authentic, humanized Cover Letter applying for {role_title} at {company_name}.\n\n"
            f"COMPANY INTELLIGENCE:\n{brief_str}\n\n"
            f"CANDIDATE PROJECTS (WITH EXACT MECHANICS & VERIFIED LINKS):\n{project_context}\n\n"
            f"{style_instruction}\n\n"
            f"CRITICAL HUMANIZATION & ANTI-AI CONSTRAINTS:\n"
            f"1. STRICTLY FORBIDDEN WORDS: Never use any of these buzzwords: {forbidden_str}.\n"
            f"2. SPEAK LIKE A REAL ENGINEER: Talk naturally about practical software trade-offs, race conditions, atomic mutations, and system boundaries.\n"
            f"3. EMBED REAL LINKS: Mention candidate's GitHub or live demo URLs naturally in the text.\n"
            f"4. NO fake percentage metrics. Focus entirely on authentic architecture and code mechanics.\n"
            f"5. DIRECT OUTPUT ONLY: Start immediately with the greeting (e.g. 'Hi team at {company_name},') and end with the candidate sign-off. Absolutely NO thinking process, reasoning steps, outline, notes, or analysis tags.\n"
            f"6. Output the final copy-pastable letter immediately."
        )

        async def call_groq():
            try:
                return await self._execute_groq_completion(user_content, max_tokens=1800)
            except Exception:
                return (
                    f"Hi team at {company_name},\n\n"
                    f"I saw the {role_title} opening and wanted to reach out. As {company_name} scales its platform in {domain_str}, "
                    f"handling concurrent users while maintaining low-latency state updates is usually where the biggest bottlenecks occur.\n\n"
                    f"I've spent a lot of time working through these exact problems in my own projects. When building full-stack architectures, "
                    f"I focus heavily on atomic database integrity, WebSocket event isolation, and decoupled sidecar IPC to eliminate race conditions.\n\n"
                    f"I’d love to bring this practical engineering approach to {company_name}. I have attached my resume and look forward to connecting.\n\n"
                    f"Best,\nCandidate"
                )

        return await scheduler.execute_task("groq", call_groq)

    async def generate_application_email(
        self,
        company_name: str,
        role_title: str,
        resume_bullets: List[str] = [],
        projects: Optional[List[Dict[str, Any]]] = None,
        research_brief: Optional[ResearchBrief] = None,
        pitch_style: str = "deep_dive",
        mock_response: Optional[str] = None
    ) -> str:
        """
        Generates humanized direct application email (Subject + Body) with live links.
        """
        if mock_response is not None:
            return mock_response

        brief_str = self._format_research_brief(research_brief)
        project_context = self._format_candidate_projects(projects or [])
        if not projects and resume_bullets:
            project_context = "\n".join(f"• {b}" for b in resume_bullets[:2])

        domain_str = research_brief.industry_domain if research_brief else "Technology"
        forbidden_str = ", ".join(ANTI_AI_FORBIDDEN_BUZZWORDS)

        user_content = (
            f"Draft a humanized, direct application email (Subject Line + Body) applying for {role_title} at {company_name}.\n\n"
            f"COMPANY CONTEXT:\n{brief_str}\n\n"
            f"CANDIDATE PROJECTS:\n{project_context}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Subject line should be natural and specific (e.g. 'Full-stack engineer / Project Name -> {company_name}').\n"
            f"2. Body should be 4-6 natural sentences. Sound like an engineer emailing another engineer.\n"
            f"3. Reference a concrete engineering challenge in {domain_str} and explain how candidate solved it.\n"
            f"4. Naturally embed 1 GitHub or live demo link.\n"
            f"5. NO robotic buzzwords ({forbidden_str}).\n"
            f"6. DIRECT OUTPUT ONLY: Start immediately with the Subject line and end with sign-off. Absolutely NO thinking process, reasoning steps, outline, notes, or analysis tags.\n"
            f"7. End with a clean 10-15 minute chat invite."
        )

        async def call_groq():
            try:
                return await self._execute_groq_completion(user_content, max_tokens=1000)
            except Exception:
                return (
                    f"Subject: Full-Stack Engineer / {role_title} opening -> {company_name}\n\n"
                    f"Hi Team,\n\n"
                    f"I saw the {role_title} role at {company_name} and wanted to share my background directly. "
                    f"As your team expands its platform in {domain_str}, I bring hands-on experience building decoupled backend architectures and real-time state synchronization.\n\n"
                    f"In my recent projects, I focused heavily on isolating concurrent WebSocket channels and enforcing atomic transaction integrity to eliminate race conditions under load.\n\n"
                    f"I’d love to connect for 10-15 minutes if you're open to exploring a fit. My resume is attached.\n\n"
                    f"Best regards,\nCandidate"
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

groq_service = GroqService()
