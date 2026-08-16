"""Unit tests for Authentic Candidate Skills Synthesis Engine."""

import pytest
from app.skills_engine import extract_authentic_candidate_skills

def test_extract_authentic_candidate_skills_no_hallucinations():
    projects = [
        {
            "directory_name": "EzNotes",
            "summary_markdown": "# EzNotes\nBuilt Next.js 14 app with React, TypeScript, and Render.",
            "tech_stack": "TypeScript, React, Next.js",
            "language": "TypeScript",
            "is_hidden": 0
        },
        {
            "directory_name": "SlotSwap",
            "summary_markdown": "# SlotSwap\nMongoose sessions and MongoDB peer-to-peer exchange with Node.js and Express.",
            "tech_stack": "Node.js, Express, MongoDB",
            "language": "TypeScript",
            "is_hidden": 0
        },
        {
            "directory_name": "sentiment-analysis-app",
            "summary_markdown": "# Sentiment App\nPython and Streamlit app using Scikit-Learn for NLP.",
            "tech_stack": "Python, Streamlit",
            "language": "Python",
            "is_hidden": 0
        }
    ]

    skills = extract_authentic_candidate_skills(
        projects=projects,
        jd_text="Looking for a Full Stack engineer with React, Next.js, and MongoDB."
    )

    all_skills_flat = [s for sublist in skills.values() for s in sublist]
    all_skills_str = " ".join(all_skills_flat).lower()

    # Assert genuine candidate skills exist
    assert "typescript" in all_skills_str
    assert "python" in all_skills_str
    assert "react.js" in all_skills_str
    assert "next.js" in all_skills_str
    assert "mongodb" in all_skills_str

    # Assert unrepresented fake technologies (like Go, Rust, Ruby) DO NOT exist
    assert "go" not in all_skills_flat
    assert "rust" not in all_skills_str
    assert "ruby" not in all_skills_str
    assert "kubernetes" not in all_skills_str
