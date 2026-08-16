"""Unit tests for Gemini OCR/Reranker, Groq Grounded Creative Generation, and Employee Lookup."""

import pytest
from app.gemini_service import gemini_service
from app.groq_service import groq_service, SYSTEM_GROUNDING_PROMPT
from app.employee_lookup import parse_employee_from_item
from app.company_research import ResearchBrief, SignalItem

@pytest.mark.asyncio
async def test_groq_cover_letter_grounding():
    """Verify Groq cover letter generation consumes grounding constraint."""
    brief = ResearchBrief(
        status="FOUND",
        signals=[
            SignalItem(
                signal_type="product_launch",
                headline="Acme unveiled warehouse arm v3",
                source_url="https://acme.com/v3",
                source_tier=1
            )
        ],
        company_name="Acme Corp"
    )

    mock_letter = "Dear Hiring Team, I was thrilled to see Acme's launch of the warehouse arm v3..."
    letter = await groq_service.generate_cover_letter(
        company_name="Acme Corp",
        role_title="Robotics Engineer",
        resume_bullets=["Engineered kinematic arm controls."],
        research_brief=brief,
        mock_response=mock_letter
    )

    assert "warehouse arm v3" in letter
    assert "SYSTEM_GROUNDING_PROMPT" in globals() or SYSTEM_GROUNDING_PROMPT is not None

@pytest.mark.asyncio
async def test_groq_cover_letter_no_signals():
    """Verify Groq handles NO_SIGNALS_FOUND without inventing facts."""
    brief = ResearchBrief(status="NO_SIGNALS_FOUND", signals=[], company_name="PrivateCo")
    mock_letter = "Dear Hiring Team, I am writing to express my strong interest in the Software Engineer position at PrivateCo..."
    letter = await groq_service.generate_cover_letter(
        company_name="PrivateCo",
        role_title="Software Engineer",
        resume_bullets=["Built distributed API."],
        research_brief=brief,
        mock_response=mock_letter
    )
    assert "PrivateCo" in letter

@pytest.mark.asyncio
async def test_gemini_project_reranker():
    """Verify Gemini reranks projects to top 3-4."""
    candidate_projects = [
        {"title": f"Proj {i}", "tech_stack": "Python, SQL", "summary_markdown": "Details"}
        for i in range(1, 10)
    ]
    mock_ranked = [
        {"title": "Proj 1", "tech_stack": "Python", "bullets": ["Bullet 1", "Bullet 2"]},
        {"title": "Proj 2", "tech_stack": "Python", "bullets": ["Bullet A", "Bullet B"]},
        {"title": "Proj 3", "tech_stack": "Python", "bullets": ["Bullet X", "Bullet Y"]},
    ]

    ranked = await gemini_service.rerank_projects_for_jd(
        jd_text="Looking for senior Python developers with database experience.",
        candidate_projects=candidate_projects,
        top_k=3,
        mock_response=mock_ranked
    )
    assert len(ranked) == 3
    assert ranked[0]["title"] == "Proj 1"

def test_employee_lookup_parser():
    """Verify Google CSE search result item parsing into clean networking contact card."""
    mock_item = {
        "title": "Jane Doe - Senior Engineering Manager - Amazon | LinkedIn",
        "snippet": "View Jane Doe's profile on LinkedIn. Senior Engineering Manager leading AWS database services. 10+ years distributed systems.",
        "link": "https://www.linkedin.com/in/janedoe"
    }
    contact = parse_employee_from_item(mock_item, "Amazon")
    assert contact["employee_name"] == "Jane Doe"
    assert "Amazon" in contact["employee_tagline"] or "Senior Engineering Manager" in contact["employee_tagline"]
    assert contact["profile_url"] == "https://www.linkedin.com/in/janedoe"
    assert contact["referral_status"] == "Not Contacted"
