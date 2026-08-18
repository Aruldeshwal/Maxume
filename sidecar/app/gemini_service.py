"""Gemini Developer API Service for Multimodal OCR and Project Reranking (apicontracts.md §2, ADR 2)."""

import os
import json
import re
import logging
import requests
from typing import List, Dict, Any, Optional, Union, Tuple
from dotenv import load_dotenv
from app.scheduler import scheduler
from app.image_optimizer import compress_jd_screenshot

load_dotenv()

logger = logging.getLogger("maxume.gemini")

# Production flash models in verified priority order
CANDIDATE_GEMINI_MODELS = [
    os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview"),
    "gemini-3.1-flash-lite-preview",
    "gemini-flash-latest"
]

def score_project_relevance(proj: Dict[str, Any], jd_text: str) -> int:
    """
    Computes a weighted relevance score of a project against a Job Description.
    Evaluates tech stack keywords, project name, summary markdown, and bullets.
    """
    jd_lower = jd_text.lower()
    score = 0

    # 1. Tech stack tokens (highest weight: 14 pts for exact word match, 7 pts for substring)
    tech_stack = (proj.get("tech_stack") or "").lower()
    for tech in [t.strip() for t in tech_stack.split(",") if t.strip()]:
        escaped = re.escape(tech)
        if re.search(r'\b' + escaped + r'\b', jd_lower):
            score += 14
        elif tech in jd_lower:
            score += 7

    # 2. Project Directory / Name keywords (e.g. sentiment-analysis for NLP/ML)
    name_words = re.findall(r'[a-zA-Z]+', proj.get("directory_name", "").lower())
    for w in name_words:
        if len(w) > 3 and w in jd_lower:
            score += 10

    # 3. Domain & Architecture Keyword matching in Summary & Bullets
    summary = (proj.get("summary_markdown") or "").lower()
    domain_keywords = [
        "python", "react", "next.js", "typescript", "javascript", "fastapi", "node",
        "express", "mongodb", "postgresql", "prisma", "sql", "sqlite", "machine learning",
        "nlp", "sentiment", "scikit", "socket.io", "real-time", "tauri", "rust", "c++",
        "docker", "cloud", "aws", "azure", "rest", "graphql", "tailwind", "zustand", "clerk"
    ]
    for kw in domain_keywords:
        if kw in jd_lower and kw in summary:
            score += 4

    return score

class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def _get_api_urls(self) -> List[str]:
        key = self.api_key or os.environ.get("GEMINI_API_KEY", "")
        return [
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            for model in CANDIDATE_GEMINI_MODELS
        ]

    async def ocr_screenshot_jd(
        self,
        image_paths: Union[str, List[str]],
        mock_response: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extracts clean text, company name, role title, and tech requirements from one or multiple JD screenshots.
        Compresses images with Pillow first per ADR 1.
        """
        if mock_response is not None:
            return mock_response

        # Normalize to list
        if isinstance(image_paths, str):
            paths_list = [image_paths]
        else:
            paths_list = image_paths

        if not paths_list:
            return {"company_name": "", "role_title": "", "raw_text": "", "key_skills": []}

        # Compress all screenshots locally
        image_parts = []
        for p in paths_list:
            if os.path.exists(p):
                try:
                    _, b64_img, _ = compress_jd_screenshot(p)
                    image_parts.append({
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": b64_img
                        }
                    })
                except Exception:
                    continue

        if not image_parts:
            return {"company_name": "", "role_title": "", "raw_text": "", "key_skills": []}

        async def call_ocr():
            prompt = (
                "You are given one or more sequential screenshots of a job description. "
                "Carefully transcribe and extract all textual information across all provided images in chronological order. "
                "Output a valid JSON object with the following fields: 'company_name', 'role_title', 'raw_text' (complete unified job description), and 'key_skills' (array of strings). "
                "Output ONLY the JSON object, nothing else."
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            *image_parts
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 3000
                }
            }

            for url in self._get_api_urls():
                try:
                    res = requests.post(url, json=payload, timeout=15.0)
                    if res.status_code == 200:
                        data = res.json()
                        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        clean_json_str = re.sub(r'^```json\s*|\s*```$', '', text.strip(), flags=re.MULTILINE)
                        clean_json_str = re.sub(r'<think>.*?</think>', '', clean_json_str, flags=re.DOTALL).strip()
                        try:
                            return json.loads(clean_json_str)
                        except Exception:
                            return {
                                "company_name": "Target Company",
                                "role_title": "Software Engineer",
                                "raw_text": text,
                                "key_skills": []
                            }
                    elif res.status_code == 429:
                        raise RuntimeError(f"Gemini 429: {res.text}")
                    elif res.status_code == 404:
                        continue
                except RuntimeError as r_err:
                    if "429" in str(r_err):
                        raise r_err
                except Exception:
                    continue

            return {"company_name": "Target Company", "role_title": "Software Engineer", "raw_text": "", "key_skills": []}

        return await scheduler.execute_task("gemini", call_ocr)

    async def rerank_projects_for_jd(
        self,
        jd_text: str,
        candidate_projects: List[Dict[str, Any]],
        top_k: int = 4,
        mock_response: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Takes candidate projects, evaluates semantic keyword relevance against the Job Description,
        uses Gemini to select the best 3-4 matches, and selects concise, standout bullet points.
        """
        if mock_response is not None:
            return mock_response[:top_k]

        if not candidate_projects:
            return []

        # 1. Score ALL candidate projects semantically against the target JD
        scored_projects = sorted(
            candidate_projects,
            key=lambda p: score_project_relevance(p, jd_text),
            reverse=True
        )

        prefiltered = scored_projects[:8]

        def extract_clean_bullets_from_text(summary_txt: str) -> List[str]:
            valid = []
            for line in (summary_txt or "").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                lower = stripped.lower()
                if any(lower.startswith(prefix) for prefix in ["github:", "**github", "language:", "**language", "live demo:", "**live demo", "url:", "tech stack:", "**tech stack", "timeline:", "**timeline"]):
                    continue
                clean = re.sub(r'^[-*•\d.)\s]+', '', stripped).replace("**", "").replace("__", "").strip()
                if len(clean) > 20 and not clean.startswith("http"):
                    valid.append(clean)
            return valid

        def extract_metadata_from_summary(summary_txt: str) -> Tuple[str, str]:
            tech = ""
            timeline = ""
            for line in (summary_txt or "").splitlines():
                lower = line.lower()
                if "**tech stack**:" in lower or "tech stack:" in lower:
                    tech = re.sub(r'[*_]+tech stack[*_]+:\s*', '', line, flags=re.IGNORECASE).strip()
                elif "**timeline**:" in lower or "timeline:" in lower or "**date**:" in lower:
                    timeline = re.sub(r'[*_]+(?:timeline|date)[*_]+:\s*', '', line, flags=re.IGNORECASE).strip()
            return tech, timeline

        def get_local_fallback() -> List[Dict[str, Any]]:
            """Returns the highest scored candidate projects with clean metadata."""
            fallback_list = []
            for i, p in enumerate(scored_projects[:top_k]):
                summary_txt = p.get("summary_markdown", "")
                extracted_bullets = extract_clean_bullets_from_text(summary_txt)
                meta_tech, meta_timeline = extract_metadata_from_summary(summary_txt)
                if not extracted_bullets:
                    extracted_bullets = [
                        f"Architected core engineering architecture and services for {p.get('directory_name', 'project')}.",
                        "Engineered modular data pipelines optimizing response latency.",
                        "Designed responsive UI components achieving fast user iteration cycles."
                    ]

                fallback_list.append({
                    "title": p.get("directory_name") or p.get("title", f"Project {i+1}"),
                    "tech_stack": p.get("tech_stack") or meta_tech or "General Engineering",
                    "live_demo_url": p.get("live_demo_url"),
                    "date": p.get("timeline") or p.get("date") or meta_timeline or "2024 – Present",
                    "bullets": extracted_bullets[:3]
                })
            return fallback_list

        async def call_rerank():
            projects_summary_str = ""
            for i, p in enumerate(prefiltered):
                clean_bullets = extract_clean_bullets_from_text(p.get('summary_markdown', ''))
                meta_tech, meta_timeline = extract_metadata_from_summary(p.get('summary_markdown', ''))
                bullets_joined = "\n".join(f"- {b}" for b in clean_bullets[:3])
                projects_summary_str += (
                    f"Project {i+1}:\n"
                    f"Name: {p.get('directory_name') or p.get('title')}\n"
                    f"Tech Stack: {p.get('tech_stack') or meta_tech or 'N/A'}\n"
                    f"Timeline: {p.get('timeline') or p.get('date') or meta_timeline or '2024 – Present'}\n"
                    f"URL: {p.get('live_demo_url', '')}\n"
                    f"Highlights:\n{bullets_joined}\n\n"
                )

            prompt = (
                "You are an expert technical recruiter and resume strategist. "
                "Analyze the candidate's projects and select the top 2-3 most relevant projects for the given Job Description. "
                "For each selected project, return: 'title', 'tech_stack', 'live_demo_url', 'date', and 3 concise, standout engineering 'bullets'. "
                "Do NOT include URLs, GitHub links, or labels in the bullet points. "
                "Output ONLY a valid JSON array of objects with keys: 'title', 'tech_stack', 'live_demo_url', 'date', 'bullets'.\n\n"
                f"JOB DESCRIPTION:\n{jd_text[:1500]}\n\n"
                f"CANDIDATE PROJECTS:\n{projects_summary_str}"
            )

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 2048
                }
            }

            for url in self._get_api_urls():
                try:
                    res = requests.post(url, json=payload, timeout=12.0)
                    if res.status_code == 200:
                        data = res.json()
                        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        clean_json_str = re.sub(r'^```json\s*|\s*```$', '', text.strip(), flags=re.MULTILINE)
                        clean_json_str = re.sub(r'<think>.*?</think>', '', clean_json_str, flags=re.DOTALL).strip()
                        try:
                            ranked = json.loads(clean_json_str)
                            # Match each ranked project back to candidate projects by name
                            matched_results = []
                            for r in ranked:
                                r_title = (r.get("title") or "").strip().lower()
                                matched_proj = next(
                                    (p for p in prefiltered if p.get("directory_name", "").lower() in r_title or r_title in p.get("directory_name", "").lower()),
                                    None
                                )
                                if matched_proj:
                                    meta_tech, meta_time = extract_metadata_from_summary(matched_proj.get("summary_markdown", ""))
                                    tech = r.get("tech_stack") or matched_proj.get("tech_stack") or meta_tech or "General Engineering"
                                    timeline = r.get("date") or matched_proj.get("timeline") or matched_proj.get("date") or meta_time or "2024 – Present"
                                    live_url = r.get("live_demo_url") or matched_proj.get("live_demo_url")
                                else:
                                    tech = r.get("tech_stack") or "General Engineering"
                                    timeline = r.get("date") or "2024 – Present"
                                    live_url = r.get("live_demo_url")

                                bullets_cleaned = [
                                    re.sub(r'^[-*•\d.)\s]+', '', b).replace("**", "").strip()
                                    for b in r.get("bullets", [])
                                    if len(b.strip()) > 15 and not any(b.lower().startswith(x) for x in ["github:", "language:", "live demo:", "url:", "tech stack:"])
                                ][:3]

                                matched_results.append({
                                    "title": r.get("title"),
                                    "tech_stack": tech,
                                    "live_demo_url": live_url,
                                    "date": timeline,
                                    "bullets": bullets_cleaned
                                })

                            if matched_results:
                                return matched_results[:top_k]
                        except Exception:
                            return get_local_fallback()
                    elif res.status_code == 429:
                        raise RuntimeError(f"Gemini 429: {res.text}")
                    elif res.status_code == 404:
                        continue
                except RuntimeError as r_err:
                    if "429" in str(r_err):
                        raise r_err
                except Exception:
                    continue

            return get_local_fallback()

        try:
            return await scheduler.execute_task("gemini", call_rerank)
        except Exception:
            return get_local_fallback()

gemini_service = GeminiService()
