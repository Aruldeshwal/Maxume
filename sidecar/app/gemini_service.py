"""Gemini Developer API Service for Multimodal OCR and Project Reranking (apicontracts.md §2, ADR 2)."""

import os
import json
import re
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from app.scheduler import scheduler
from app.image_optimizer import compress_jd_screenshot

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash-lite"

class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def _get_api_url(self) -> str:
        key = self.api_key or os.environ.get("GEMINI_API_KEY", "")
        return f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"

    async def ocr_screenshot_jd(self, image_path: str, mock_response: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extracts clean text, company name, role title, and tech requirements from JD screenshot.
        Compresses image with Pillow first per ADR 1.
        """
        if mock_response is not None:
            return mock_response

        # Compress screenshot locally
        _, b64_img, _ = compress_jd_screenshot(image_path)

        async def call_ocr():
            url = self._get_api_url()
            prompt = (
                "Identify and extract the clean text from this job description screenshot. "
                "Output a valid JSON object with the following fields: 'company_name', 'role_title', 'raw_text', and 'key_skills' (array of strings). "
                "Output ONLY the JSON object, nothing else."
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inlineData": {
                                    "mimeType": "image/jpeg",
                                    "data": b64_img
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 2048
                }
            }
            res = requests.post(url, json=payload, timeout=12.0)
            if res.status_code == 200:
                data = res.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                # Clean code blocks
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
            else:
                raise RuntimeError(f"Gemini OCR error: {res.status_code} - {res.text}")

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
        and selects 3-4 concise, impactful bullet points per project.
        """
        if mock_response is not None:
            return mock_response[:top_k]

        if not candidate_projects:
            return []

        # Local pre-filter to top 8 if more exist
        prefiltered = candidate_projects[:8]

        async def call_rerank():
            url = self._get_api_url()
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

            res = requests.post(url, json=payload, timeout=12.0)
            if res.status_code == 200:
                data = res.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                clean_json_str = re.sub(r'^```json\s*|\s*```$', '', text.strip(), flags=re.MULTILINE)
                try:
                    ranked = json.loads(clean_json_str)
                    return ranked[:top_k]
                except Exception:
                    # Fallback to prefiltered list
                    return [
                        {
                            "title": p.get("directory_name") or p.get("title", f"Project {i+1}"),
                            "tech_stack": p.get("tech_stack", "General Engineering"),
                            "live_demo_url": p.get("live_demo_url"),
                            "bullets": ["Engineered high performance component.", "Optimized storage and API latency."]
                        }
                        for i, p in enumerate(prefiltered[:top_k])
                    ]
            elif res.status_code == 429:
                raise RuntimeError(f"Gemini 429: {res.text}")
            else:
                raise RuntimeError(f"Gemini rerank error: {res.status_code} - {res.text}")

        return await scheduler.execute_task("gemini", call_rerank)

gemini_service = GeminiService()
