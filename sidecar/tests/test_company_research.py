"""Unit tests for Company Signal Research pipeline and 3-Stage Hallucination Guard."""

import pytest
from datetime import datetime, timedelta, timezone
from app.company_research import (
    research_company,
    passes_containment_check,
    classify_source_tier,
    is_within_recency,
    ResearchBrief
)

def test_source_tiering():
    """Verify tier classification: 1=Company domain, 2=Major press, 3=GitHub."""
    assert classify_source_tier("https://acmerobotics.com/blog/v3-arm", company_domain="acmerobotics.com") == 1
    assert classify_source_tier("https://techcrunch.com/2026/acme-series-b", company_domain="acmerobotics.com") == 2
    assert classify_source_tier("https://github.com/acmerobotics/sdk", company_domain="acmerobotics.com") == 3

def test_passes_containment_check():
    """Verify deterministic post-hoc containment check (ADR 5)."""
    source_snippets = [
        "Acme Robotics today announced the launch of its new warehouse-picking arm v3 with 99.8% precision.",
        "The Series B round was led by Sequoia Capital, raising $45M for international expansion."
    ]

    # Grounded summary with entities and numbers present in source
    valid_bullet_1 = "Acme Robotics unveiled its warehouse-picking arm v3 featuring 99.8% precision."
    assert passes_containment_check(valid_bullet_1, source_snippets) is True

    valid_bullet_2 = "Raised $45M in Series B funding led by Sequoia Capital."
    assert passes_containment_check(valid_bullet_2, source_snippets) is True

    # Hallucinated fact (fictitious entity and wrong numbers)
    hallucinated_bullet_1 = "Acme Robotics partnered with Amazon to deploy 500,000 autonomous forklifts."
    assert passes_containment_check(hallucinated_bullet_1, source_snippets) is False

    hallucinated_bullet_2 = "Acme raised $120M in Series C round from Andreessen Horowitz."
    assert passes_containment_check(hallucinated_bullet_2, source_snippets) is False

def test_research_company_found_signals():
    """Verify research_company returns FOUND with correctly tiered signals when grounded."""
    recent_date = (datetime.now(timezone.utc) - timedelta(days=15)).strftime("%Y-%m-%d")
    mock_snippets = [
        {
            "title": "Acme Robotics Blog: Arm v3 Release",
            "snippet": "Acme Robotics released warehouse-picking arm v3 with automated obstacle avoidance.",
            "source_url": "https://acme.com/blog/arm-v3",
            "published_at": recent_date,
            "source_tier": 1
        },
        {
            "title": "TechCrunch: Acme Robotics Series B",
            "snippet": "Acme Robotics closed $45M in Series B financing for European warehouse deployment.",
            "source_url": "https://techcrunch.com/2026/acme-b",
            "published_at": recent_date,
            "source_tier": 2
        }
    ]

    mock_gemini = (
        "• Acme Robotics launched its warehouse-picking arm v3 with obstacle avoidance. (https://acme.com/blog/arm-v3)\n"
        "• Closed $45M Series B funding for European deployment. (https://techcrunch.com/2026/acme-b)"
    )

    brief = research_company(
        company_name="Acme Robotics",
        company_url="https://acme.com",
        recency_days=90,
        mock_snippets=mock_snippets,
        mock_gemini_response=mock_gemini
    )

    assert isinstance(brief, ResearchBrief)
    assert brief.status == "FOUND"
    assert len(brief.signals) == 2
    assert brief.signals[0].source_tier == 1
    assert brief.signals[0].guard_check_passed is True
    assert "warehouse-picking arm v3" in brief.signals[0].headline

def test_research_company_stale_snippets_fallback():
    """Verify snippets outside recency window trigger NO_SIGNALS_FOUND."""
    stale_date = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%d")
    mock_snippets = [
        {
            "title": "Old News",
            "snippet": "Acme founded in 2020.",
            "source_url": "https://acme.com/history",
            "published_at": stale_date,
            "source_tier": 1
        }
    ]

    brief = research_company(
        company_name="Acme Robotics",
        company_url="https://acme.com",
        recency_days=90,
        mock_snippets=mock_snippets
    )

    assert brief.status == "NO_SIGNALS_FOUND"
    assert brief.signals == []

def test_research_company_hallucination_dropped_by_guard():
    """Verify hallucinated Gemini summary is dropped by containment check."""
    recent_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
    mock_snippets = [
        {
            "title": "Acme v3 Arm",
            "snippet": "Acme Robotics released warehouse-picking arm v3 with obstacle avoidance.",
            "source_url": "https://acme.com/blog/arm-v3",
            "published_at": recent_date,
            "source_tier": 1
        }
    ]

    # Gemini output fabricates an ungrounded acquisition
    mock_gemini_hallucinated = "• Acme was acquired by Microsoft for $2B in cash. (https://acme.com/news)"

    brief = research_company(
        company_name="Acme Robotics",
        company_url="https://acme.com",
        recency_days=90,
        mock_snippets=mock_snippets,
        mock_gemini_response=mock_gemini_hallucinated
    )

    # Containment check drops the ungrounded signal -> falls back to NO_SIGNALS_FOUND
    assert brief.status == "NO_SIGNALS_FOUND"
    assert brief.signals == []

def test_research_company_never_raises_on_empty():
    """Assert empty or non-existent company returns NO_SIGNALS_FOUND without raising exceptions."""
    brief1 = research_company(company_name="")
    assert brief1.status == "NO_SIGNALS_FOUND"

    brief2 = research_company(company_name="NonExistentCompanyXYZ12345", mock_snippets=[])
    assert brief2.status == "NO_SIGNALS_FOUND"
    assert brief2.signals == []
