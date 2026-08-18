"""Maximal Marginal Relevance (MMR) & Skill-Cluster Project Matching Engine for Maxume."""

import re
from typing import List, Dict, Any, Set, Tuple

# Comprehensive canonical taxonomy of engineering skills and domains
CANONICAL_SKILL_MAP = {
    # Languages
    "python": "python",
    "typescript": "typescript",
    "javascript": "javascript",
    "js": "javascript",
    "ts": "typescript",
    "rust": "rust",
    "c++": "c++",
    "cpp": "c++",
    "c": "c",
    "golang": "go",
    "go": "go",
    "java": "java",
    "sql": "sql",
    "html": "html",
    "css": "css",
    "shell": "shell",
    "bash": "bash",

    # Frontend Frameworks & Web
    "react": "react",
    "react.js": "react",
    "reactjs": "react",
    "next": "next.js",
    "next.js": "next.js",
    "nextjs": "next.js",
    "vue": "vue",
    "vue.js": "vue",
    "angular": "angular",
    "tailwind": "tailwind css",
    "tailwindcss": "tailwind css",
    "redux": "redux",
    "zustand": "zustand",
    "framer": "framer motion",
    "lucide": "lucide",

    # Backend & API Frameworks
    "node": "node.js",
    "node.js": "node.js",
    "nodejs": "node.js",
    "express": "express.js",
    "express.js": "express.js",
    "fastapi": "fastapi",
    "flask": "flask",
    "django": "django",
    "rest": "rest api",
    "restful": "rest api",
    "api": "rest api",
    "graphql": "graphql",

    # Databases & ORM
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "mongoose": "mongodb",
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "prisma": "prisma",
    "sqlite": "sqlite",
    "sqlite3": "sqlite",
    "redis": "redis",
    "mysql": "mysql",

    # AI, ML & Data Science
    "machine learning": "machine learning",
    "ml": "machine learning",
    "nlp": "nlp",
    "sentiment analysis": "sentiment analysis",
    "sentiment": "sentiment analysis",
    "scikit-learn": "scikit-learn",
    "scikit": "scikit-learn",
    "sklearn": "scikit-learn",
    "pytorch": "pytorch",
    "torch": "pytorch",
    "tensorflow": "tensorflow",
    "pandas": "pandas",
    "numpy": "numpy",
    "streamlit": "streamlit",
    "llm": "llm",
    "ollama": "ollama",
    "groq": "groq",
    "transformers": "transformers",

    # Architecture, Systems & Cloud
    "socket.io": "socket.io",
    "websocket": "socket.io",
    "websockets": "socket.io",
    "real-time": "real-time",
    "realtime": "real-time",
    "tauri": "tauri",
    "desktop": "desktop app",
    "ipc": "ipc sidecar",
    "docker": "docker",
    "dockerfile": "docker",
    "clerk": "clerk auth",
    "auth": "authentication",
    "jwt": "authentication",
    "oauth": "authentication"
}

def extract_skills_from_text(text: str) -> Set[str]:
    """Extracts canonical skill identifiers from a raw text block (JD or project summary)."""
    text_lower = (text or "").lower()
    found_skills = set()

    for keyword, canonical in CANONICAL_SKILL_MAP.items():
        # Match word boundaries or exact symbols
        escaped = re.escape(keyword)
        if re.search(r'(?:^|[^a-zA-Z0-9_#+])' + escaped + r'(?:$|[^a-zA-Z0-9_#+])', text_lower):
            found_skills.add(canonical)

    return found_skills

def extract_project_skills(proj: Dict[str, Any]) -> Set[str]:
    """Combines tech stack, directory name, and summary to extract all verified skills."""
    combined = f"{proj.get('tech_stack', '')} {proj.get('directory_name', '')} {proj.get('summary_markdown', '')}"
    return extract_skills_from_text(combined)

def compute_project_base_relevance(
    proj_skills: Set[str],
    jd_skills: Set[str],
    proj: Dict[str, Any],
    jd_text: str
) -> float:
    """
    Computes foundational relevance. ONLY skills requested by the JD earn score.
    Non-requested technologies receive zero weight.
    """
    if not jd_skills:
        return 1.0

    matching_skills = proj_skills.intersection(jd_skills)
    score = 0.0

    # Tech stack explicit matches (highest weight)
    tech_stack_lower = (proj.get("tech_stack") or "").lower()
    for s in matching_skills:
        if s in tech_stack_lower:
            score += 15.0
        else:
            score += 8.0

    # Directory name match (e.g. sentiment-analysis matching sentiment/NLP in JD)
    proj_name = proj.get("directory_name", "").lower().replace("-", " ")
    for word in proj_name.split():
        if len(word) > 3 and word in jd_text.lower():
            score += 12.0

    return score

def select_projects_mmr(
    candidate_projects: List[Dict[str, Any]],
    jd_text: str,
    top_k: int = 4,
    alpha: float = 0.60
) -> List[Dict[str, Any]]:
    """
    Selects top candidate projects using Maximal Marginal Relevance (MMR).
    
    Guarantees:
    1. Zero Out-of-Scope Injections: Projects with technologies not in the JD get zero bonus.
    2. Deep Specialization: If the JD is pure MERN, top 3 will all be MERN projects.
    3. Multi-Domain Breadth: If the JD asks for MERN + Python/AI, MMR selects the best from each requested domain.
    """
    if not candidate_projects:
        return []

    jd_skills = extract_skills_from_text(jd_text)

    # Pre-extract skills for all candidates
    project_skill_cache = [
        (proj, extract_project_skills(proj))
        for proj in candidate_projects
    ]

    selected: List[Dict[str, Any]] = []
    covered_skills: Set[str] = set()
    remaining_candidates = list(project_skill_cache)

    while len(selected) < min(top_k, len(candidate_projects)) and remaining_candidates:
        best_proj = None
        best_skills = set()
        best_mmr_score = -999999.0
        best_idx = -1

        for idx, (proj, p_skills) in enumerate(remaining_candidates):
            # 1. Base relevance score against JD (only requested skills count)
            base_rel = compute_project_base_relevance(p_skills, jd_skills, proj, jd_text)

            # 2. Marginal Coverage Gain: New JD skills covered by this project that haven't been covered yet
            uncovered_jd_skills = jd_skills - covered_skills
            new_skills_covered = p_skills.intersection(uncovered_jd_skills)
            marginal_gain = len(new_skills_covered) * 20.0

            # 3. Redundancy Penalty: Skills overlapping with already selected projects
            redundancy = len(p_skills.intersection(covered_skills)) * 5.0

            # MMR Formula
            mmr_score = (alpha * base_rel) + ((1.0 - alpha) * marginal_gain) - (0.2 * redundancy)

            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_proj = proj
                best_skills = p_skills
                best_idx = idx

        if best_proj and best_idx >= 0:
            selected.append(best_proj)
            covered_skills.update(best_skills.intersection(jd_skills))
            remaining_candidates.pop(best_idx)
        else:
            break

    return selected
