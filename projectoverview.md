# Project Overview & Single Source of Truth (SSOT)

## 1. Executive Summary
**Maxume** is a local-first, airgapped AI Job Application Assistant built to solve the modern technical job application problem. Instead of generic AI resume tools that hallucinate technologies or output plain text, Maxume parses real local/GitHub source code, embeds clickable Word hyperlinks into `.docx` master templates, formats concise tech stacks and timelines, enforces strict single-page limits with adaptive bullet filling, and personalizes application materials with verified company news and referral contacts.

---

## 2. Core Functional Pillars

```mermaid
graph TD
    A[Local Codebase / GitHub Sync] -->|Incremental Git Watcher| B[(SQLite Local SSOT)]
    B -->|XYZ Formula Bullet Synthesizer| C[AI Engineering Highlights]
    D[Target Job Description / Screenshots] -->|Gemini Multimodal OCR| E[JD Parser & Project Reranker]
    C --> F[DocxEngine]
    E --> F
    B -->|Skills Engine (Zero Hallucinations)| F
    F -->|OXML Hyperlinks + Tech Stack + Timeline| G[Single-Page Master_Resume.docx]
    D -->|Real-Time News RSS Wire| H[Company Research Signals]
    H -->|3-Stage Containment Guard| I[Personalized Cover Letter & Outreach]
    D -->|Targeted Persona Engine| J[LinkedIn Referral Contacts & Drafts]
```

### Pillar 1: Project Knowledge Base (SSOT)
- **Watcher & GitHub Sync**: Tracks local repository folders and GitHub profile repos (`@Aruldeshwal`).
- **AI Bullet Generation**: Synthesizes engineering bullet points using Google's XYZ formula (*Accomplished [X] as measured by [Y], by doing [Z]*).
- **Live Demo & Timeline Extraction**: Automatically extracts live URLs and computes active project timelines (e.g. `Oct 2024 – Dec 2024`).
- **Visibility Toggle**: Supports marking repositories as `Active on Resume` or `Hidden from Resume` to keep non-relevant repos off the resume.

### Pillar 2: Paragraph-Level DOCX Engine
- **Active Word OXML Hyperlinks**: Generates Word `<w:hyperlink>` relationships directly in python-docx, styling live project titles in bold crimson with active external URLs.
- **Brief Tech Stack & Timeline**: Formats project headers with title, brief tech stack, and timeline dates: `Project Title | Tech Stack | Month Year – Month Year`.
- **Adaptive Bullet Headroom Filling**: Dynamically allocates 3 high-impact bullets per project (or up to 4 for 2 projects) with calibrated paragraph line spacing (`Pt(0)` before, `Pt(1.5)` after, `1.05` line-spacing) ensuring the document strictly fills exactly 1 single page.
- **Metadata Cleansing**: Automatically filters out markdown syntax, bold labels, and repository URLs from resume bullet text.
- **File-Lock Safe Writer**: Catches Windows Word file-lock exceptions and saves to safe fallback paths without failing the run.

### Pillar 3: Authentic Skills Synthesis
- **Zero-Hallucination Grounding**: Scans all 12 verified repositories and master resume text to whitelist only authentic technologies.
- **ATS Categorization**: Formats skills into *Programming Languages*, *Frameworks & Libraries*, *Databases & DevOps*, and *Core Competencies & AI*.
- **JD Alignment**: Dynamically prioritizes skills matching the target job description to the front of each category.

### Pillar 4: Real-Time Signal Research & Networking Hub
- **Real-Time News Wire**: Aggregates real-time news, launches, and funding rounds from Google News RSS and direct company announcements.
- **3-Stage Hallucination Containment**: Deterministic verification (`passes_containment_check`) rejects ungrounded claims.
- **Targeted Referral Outreach**: Builds targeted LinkedIn referral search personas (*Tech Leads*, *Engineering Managers*, *Tech Recruiters*) with tailored 75-word outreach pitches.

---

## 3. Technology Architecture & Zero-Cost Cloud Model

* **Frontend**: React 18, Vite, TypeScript, Tailwind CSS (Tactical Red/Black palette).
* **Sidecar Backend**: FastAPI running on Python 3.13 (`http://127.0.0.1:8000`).
* **Desktop Runtime**: Tauri v2.
* **Database**: Local SQLite3 (`maxume_local.db`) with thread-safe `with self.get_connection() as conn:` context managers.
* **Zero Cost Strategy**:
  - **Ollama**: Local open-source inference (`qwen2.5:7b-instruct`) with dynamic VRAM limits.
  - **Groq LPU**: Free tier (14,400 requests/day) running `llama-3.3-70b-versatile`.
  - **Google Gemini**: Free tier (1,000 requests/day) running `gemini-2.5-flash` for multimodal screenshot OCR.
  - **Google News RSS Wire**: Free, unlimited real-time press and news aggregation.
