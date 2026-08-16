"""Paragraph-Level DOCX Style Cloning & Rebuilding Engine for Maxume."""

import os
from typing import List, Dict, Any, Optional, Union
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
import docx.opc.constants
import docx.oxml.shared

MAX_PROJECTS = 4
MAX_BULLETS_PER_PROJECT = 4

def add_hyperlink(paragraph, url: str, text: str, color: str = "990000", underline: bool = True):
    """
    Embed an active clickable hyperlink in a python-docx paragraph using precise OXML ordering.
    Verbatim implementation from projectoverview.md §3.
    """
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = docx.oxml.shared.OxmlElement('w:hyperlink')
    hyperlink.set(docx.oxml.shared.qn('r:id'), r_id)
    new_run = docx.oxml.shared.OxmlElement('w:r')
    rPr = docx.oxml.shared.OxmlElement('w:rPr')
    if color:
        c = docx.oxml.shared.OxmlElement('w:color')
        c.set(docx.oxml.shared.qn('w:val'), color)
        rPr.append(c)
    if underline:
        u = docx.oxml.shared.OxmlElement('w:u')
        u.set(docx.oxml.shared.qn('w:val'), 'single')
        rPr.append(u)
    new_run.append(rPr)
    text_node = docx.oxml.shared.OxmlElement('w:t')
    text_node.text = text
    new_run.append(text_node)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink

def copy_paragraph_style(source_para, target_para):
    """Clone layout settings, indentation, and alignment from a reference paragraph."""
    if source_para.style:
        try:
            target_para.style = source_para.style
        except Exception:
            pass
    target_para.paragraph_format.alignment = source_para.paragraph_format.alignment
    target_para.paragraph_format.left_indent = source_para.paragraph_format.left_indent
    target_para.paragraph_format.right_indent = source_para.paragraph_format.right_indent
    target_para.paragraph_format.space_before = source_para.paragraph_format.space_before
    target_para.paragraph_format.space_after = source_para.paragraph_format.space_after
    target_para.paragraph_format.line_spacing = source_para.paragraph_format.line_spacing

def insert_paragraph_before(target_para, text="", style=None):
    """Insert a new paragraph before the specified target paragraph in OXML tree."""
    new_p = docx.oxml.shared.OxmlElement('w:p')
    target_para._p.addprevious(new_p)
    new_para = docx.text.paragraph.Paragraph(new_p, target_para._parent)
    if style:
        new_para.style = style
    elif target_para.style:
        new_para.style = target_para.style
    if text:
        new_para.add_run(text)
    return new_para

def remove_paragraph(paragraph):
    """Safely remove a paragraph element from its parent XML element."""
    p_element = paragraph._p
    parent = p_element.getparent()
    if parent is not None:
        parent.remove(p_element)

class DocxEngine:
    @staticmethod
    def rebuild_resume(
        template_path: str,
        output_path: str,
        projects: List[Dict[str, Any]],
        skills: Union[List[str], Dict[str, List[str]]],
        hyperlink_color: str = "990000"
    ) -> str:
        """
        Rebuilds a resume document by replacing {{PROJECTS}} and {{SKILLS}} placeholders
        with styled content, enforcing single-page limits (max 4 projects, max 4 bullets).
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Master resume template not found: {template_path}")

        doc = Document(template_path)
        
        # Enforce single-page guardrail
        bounded_projects = projects[:MAX_PROJECTS]
        
        # Locate placeholder paragraphs
        projects_placeholder = None
        skills_placeholder = None

        for p in doc.paragraphs:
            if "{{PROJECTS}}" in p.text:
                projects_placeholder = p
            if "{{SKILLS}}" in p.text:
                skills_placeholder = p

        # 1. Inject Projects
        if projects_placeholder is not None:
            for proj in bounded_projects:
                title = proj.get("title") or proj.get("directory_name") or "Project"
                tech_stack = proj.get("tech_stack", "")
                demo_url = proj.get("live_demo_url") or proj.get("url")
                date_str = proj.get("date", "")
                
                # Project Title Heading Paragraph
                title_para = insert_paragraph_before(projects_placeholder)
                copy_paragraph_style(projects_placeholder, title_para)
                
                # Add hyperlink if live demo URL exists, otherwise plain bold title
                if demo_url:
                    add_hyperlink(title_para, demo_url, title, color=hyperlink_color, underline=True)
                else:
                    r = title_para.add_run(title)
                    r.bold = True
                
                # Add tech stack & metadata to title line
                if tech_stack:
                    title_para.add_run(f" | {tech_stack}")
                if date_str:
                    r_date = title_para.add_run(f" ({date_str})")
                    r_date.italic = True

                # Bullets for this project (capped at MAX_BULLETS_PER_PROJECT)
                bullets = proj.get("bullets", [])[:MAX_BULLETS_PER_PROJECT]
                for bullet_text in bullets:
                    bullet_para = insert_paragraph_before(projects_placeholder)
                    copy_paragraph_style(projects_placeholder, bullet_para)
                    bullet_para.paragraph_format.left_indent = Inches(0.25)
                    bullet_para.add_run(f"• {bullet_text.lstrip('•- ')}")

            # Remove original {{PROJECTS}} placeholder
            remove_paragraph(projects_placeholder)

        # 2. Inject Skills
        if skills_placeholder is not None:
            if isinstance(skills, dict):
                for category, skill_list in skills.items():
                    skill_para = insert_paragraph_before(skills_placeholder)
                    copy_paragraph_style(skills_placeholder, skill_para)
                    r_cat = skill_para.add_run(f"{category}: ")
                    r_cat.bold = True
                    skill_para.add_run(", ".join(skill_list))
            elif isinstance(skills, list):
                skill_para = insert_paragraph_before(skills_placeholder)
                copy_paragraph_style(skills_placeholder, skill_para)
                skill_para.add_run(" • ".join(skills))
            
            # Remove original {{SKILLS}} placeholder
            remove_paragraph(skills_placeholder)

        # Save to output path
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc.save(output_path)
        return output_path
