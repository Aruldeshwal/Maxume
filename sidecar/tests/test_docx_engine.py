"""Unit tests for Paragraph-Level DOCX Engine and OXML Hyperlink Injection."""

import os
import pytest
import docx
from docx import Document
from app.docx_engine import DocxEngine, add_hyperlink, is_valid_bullet_point

@pytest.fixture
def docx_fixture(tmp_path):
    """Creates a temporary master template with placeholders and sample styles."""
    doc = Document()
    doc.add_heading("John Doe | Full Stack Engineer", level=0)
    
    # Skills Section
    doc.add_heading("TECHNICAL SKILLS", level=1)
    doc.add_paragraph("{{SKILLS}}")
    
    # Projects Section
    doc.add_heading("PROJECT EXPERIENCE", level=1)
    doc.add_paragraph("{{PROJECTS}}")
    
    template_path = str(tmp_path / "template_resume.docx")
    out_path = str(tmp_path / "compiled_resume.docx")
    doc.save(template_path)

    return {
        "template_path": template_path,
        "output_path": out_path,
        "tmpdir": str(tmp_path)
    }

def test_metadata_bullet_filtering():
    assert is_valid_bullet_point("**GitHub**: https://github.com/Aruldeshwal/Maxume") is False
    assert is_valid_bullet_point("**Language / Tech**: Python") is False
    assert is_valid_bullet_point("**Live Demo**: None") is False
    assert is_valid_bullet_point("URL: https://app.vercel.app") is False
    assert is_valid_bullet_point("Architected low-latency resume compiler achieving sub-50ms document assembly.") is True
    assert is_valid_bullet_point("Engineered automated Gemini Multimodal OCR pipeline.") is True

def test_rebuild_resume_basic(docx_fixture):
    projects_data = [
        {
            "title": "Maxume Local AI",
            "tech_stack": "Python, React, SQLite",
            "live_demo_url": "https://maxume.vercel.app",
            "date": "2026",
            "bullets": [
                "**GitHub**: https://github.com/...", # should be dropped
                "Built paragraph-level DOCX engine using Word OXML.",
                "Engineered token-bucket rate limiter for cloud APIs."
            ]
        },
        {
            "title": "KV-Store Core",
            "tech_stack": "Go, Raft",
            "live_demo_url": None,
            "bullets": [
                "Implemented Raft consensus protocol from scratch.",
                "Achieved 45,000 writes/sec throughput."
            ]
        }
    ]

    skills_dict = {
        "Languages": ["Python", "TypeScript", "Go"],
        "Tools": ["Docker", "Git", "Ollama"]
    }

    out_file = DocxEngine.rebuild_resume(
        template_path=docx_fixture["template_path"],
        output_path=docx_fixture["output_path"],
        projects=projects_data,
        skills=skills_dict
    )

    assert os.path.exists(out_file)
    rebuilt_doc = Document(out_file)
    all_text = "\n".join(p.text for p in rebuilt_doc.paragraphs)

    # Assert placeholders were replaced
    assert "{{PROJECTS}}" not in all_text
    assert "{{SKILLS}}" not in all_text

    # Assert project content is present without metadata labels
    assert "Maxume Local AI" in all_text
    assert "GitHub:" not in all_text
    assert "Built paragraph-level DOCX engine" in all_text
    assert "KV-Store Core" in all_text
    assert "Languages: Python, TypeScript, Go" in all_text

def test_single_page_guardrail_capping(docx_fixture):
    """Assert engine enforces max 3 projects and max 2 bullets per project."""
    # Create 7 projects, each with 6 bullets
    oversized_projects = []
    for i in range(1, 8):
        oversized_projects.append({
            "title": f"Project {i}",
            "tech_stack": "Tech",
            "bullets": [f"Architected feature {j} for project {i} with high impact" for j in range(1, 7)]
        })

    skills_data = ["Python", "Go", "Docker", "Kubernetes"]

    out_file = DocxEngine.rebuild_resume(
        template_path=docx_fixture["template_path"],
        output_path=docx_fixture["output_path"],
        projects=oversized_projects,
        skills=skills_data
    )

    rebuilt_doc = Document(out_file)
    all_text = "\n".join(p.text for p in rebuilt_doc.paragraphs)

    # Projects 1-3 must exist
    for i in range(1, 4):
        assert f"Project {i}" in all_text
        # Bullets 1-2 must exist
        for j in range(1, 3):
            assert f"Architected feature {j} for project {i}" in all_text
        # Bullets 3-6 must NOT exist
        assert f"Architected feature 3 for project {i}" not in all_text

    # Projects 4-7 must NOT exist
    for i in range(4, 8):
        assert f"Project {i}" not in all_text
