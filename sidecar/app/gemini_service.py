"""Gemini Developer API Service for Multimodal OCR and Project Reranking (apicontracts.md §2, ADR 2)."""

import os
import json
import re
import logging
import requests
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
from app.scheduler import scheduler
from app.image_optimizer import compress_jd_screenshot

load_dotenv()

logger = logging.getLogger("maxume.gemini")

# Production flash models in priority order
CANDIDATE_GEMINI_MODELS = [
    os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

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
                        # Try next candidate model
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
        Takes top candidate projects, uses Gemini to select the best 3-4 matches,
        and selects 3-4 concise, impactful bullet points per project with robust local fallback.
        """
        if mock_response is not None:
            return mock_response[:top_k]

        if not candidate_projects:
            return []

        prefiltered = candidate_projects[:8]

        def get_local_fallback() -> List[Dict[str, Any]]:
            fallback_list = []
            for i, p in enumerate(prefiltered[:top_k]):
                summary_txt = p.get("summary_markdown", "")
                extracted_bullets = [
                    line.lstrip("-*• ").strip()
                    for line in summary_txt.splitlines()
                    if line.strip().startswith(("-", "*", "•")) and len(line.strip()) > 15
                ]
                if not extracted_bullets:
                    extracted_bullets = ["Engineered high performance component.", "Optimized storage and API latency."]

                fallback_list.append({
                    "title": p.get("directory_name") or p.get("title", f"Project {i+1}"),
                    "tech_stack": p.get("tech_stack", "General Engineering"),
                    "live_demo_url": p.get("live_demo_url"),
                    "bullets": extracted_bullets[:4]
                })
            return fallback_list

        async def call_rerank():
            projects_summary_str = ""
            for i, p in enumerate(prefiltered):
                projects_summary_str += (
                    f"Project {i+1}:\n"
                    f"Name: {p.get('directory_name') or p.get('title')}\n"
                    f"Tech Stack: {p.get('tech_stack', 'N/A')}\n"
                    f"URL: {p.get('live_demo_url', '')}\n"
                    f"Logs/Summary: {p.get('summary_markdown', '')[:400]}\n\n"
                )

            prompt = (
                "You are an expert technical recruiter and resume strategist. "
                "Analyze the candidate's projects and select the top 3-4 most relevant projects for the given Job Description. "
                "For each selected project, provide: 'title', 'tech_stack', 'live_demo_url', and 3-4 quantitative, impactful 'bullets'. "
                "Output ONLY a valid JSON array of objects with keys: 'title', 'tech_stack', 'live_demo_url', 'bullets'.\n\n"
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
                        try:
                            ranked = json.loads(clean_json_str)
                            return ranked[:top_k]
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

            # Graceful local fallback if cloud API is unreachable
            return get_local_fallback()

        try:
            return await scheduler.execute_task("gemini", call_rerank)
        except Exception:
            return get_local_fallback()

gemini_service = GeminiService()
