# Project Overview & Single Source of Truth (SSOT)

## 1. Executive Summary
**Maxume** is a local-first, airgapped AI Job Application Assistant built to solve the modern technical job application problem. Instead of generic AI resume tools that hallucinate technologies or output plain text, Maxume parses real local/GitHub source code, embeds clickable Word hyperlinks into `.docx` master templates, formats concise tech stacks and timelines, enforces strict single-page limits with adaptive bullet filling, dynamically matches the most relevant candidate projects to any Job Description using multi-factor semantic scoring, synthesizes Hunter.io-style verified corporate emails, tracks live daily API quotas, and personalizes application materials with verified company news and multi-channel referral contacts.

---

## 2. Core Functional Pillars

```mermaid
graph TD
    A[Local Codebase / GitHub Sync] -->|Incremental Git Watcher| B[(SQLite Local SSOT)]
    B -->|Grounded Hybrid AI Bullet Synthesizer| C[High-Impact Engineering Highlights]
    D[Target Job Description / Screenshots] -->|Gemini Multimodal OCR| E[JD Parser]
    B -->|Semantic Relevance Scorer + Active Gemini Reranker| F[Dynamically Matched Top Projects]
    C --> G[DocxEngine]
    F --> G
    B -->|Skills Engine (Zero Hallucinations)| G
    G -->|OXML Hyperlinks + Tech Stack + Timeline| H[Single-Page Master_Resume.docx]
    D -->|Real-Time News RSS Wire| I[Company Research Signals]
    I -->|3-Stage Containment Guard| J[Personalized Cover Letter & Outreach]
    D -->|Real Person Discovery & Hunter.io Engine| K[Multi-Channel Outreach & Email Synthesizer]
    G -->|Live Request Quota Tracking| L[SQLite Daily Quota Tracker & Dashboard]
```

### Pillar 1: Project Knowledge Base & Multi-Manifest SSOT
- **Incremental Commit-Hash Sync**: Compares GitHub `pushed_at` commit timestamps against the SQLite SSOT. Unchanged repositories are instantly marked as `unchanged` (0.5s total sync), preventing redundant LLM calls, avoiding GitHub API rate limits, and **preserving custom in-app edits** made to existing projects.
- **Multi-Manifest Tech Stack Extractor**: Inspects remote `package.json`, `requirements.txt`, `Cargo.toml`, and GitHub Languages API to detect complete, multi-ecosystem technical stacks (e.g. `Tauri v2`, `FastAPI`, `React`, `Prisma`, `Socket.io`).
- **Realistic Timeline Calculator**: Computes authentic 1–3 month development sprint windows based on repository creation and commit milestones (e.g. `Oct 2025 – Nov 2025`), eliminating generic `2024 – Present` placeholders.
- **Grounded Hybrid AI Bullet Engine**: Focuses on **actual system design, concurrency safety, atomic database transactions, room multiplexing, and protocol mechanisms** without inventing fake percentages or artificial traffic loads.
- **In-App Project Details Editor**: Edit any project's **Tech Stack**, **Timeline**, **Live Demo Link**, or **Bullet Points** directly in the UI with instant SQLite SSOT synchronization (`PUT /api/projects/{id}`).
- **Visibility Control**: Supports marking repositories as `Active on Resume` or `Hidden from Resume` to keep non-relevant repos off the resume.

### Pillar 2: Dynamic Semantic Project Matching & Reranking
- **Multi-Factor Semantic Relevance Scorer**: Computes weighted keyword and domain matching (`score_project_relevance`) against target Job Descriptions, evaluating tech stacks, directory names, and project highlights.
- **Dynamic Role Adaptation**:
  - *Machine Learning / Data Science Jobs* $\rightarrow$ Automatically prioritizes `sentiment-analysis-app` and `Maxume`.
  - *Full-Stack / Next.js / TypeScript Jobs* $\rightarrow$ Automatically prioritizes `Metro-Connect`, `EzNotes`, and `Calvero`.
  - *Backend / Node / MongoDB Jobs* $\rightarrow$ Automatically prioritizes `Book-IT`, `SlotSwap`, and `Productivity-Overload`.
- **Active Model Verification**: Uses currently verified production endpoints (`gemini-3-flash-preview`, `gemini-3.1-flash-lite-preview`, `qwen/qwen3.6-27b`, `openai/gpt-oss-120b`) with reasoning tag stripping (`<think>.*?</think>`).

### Pillar 3: Paragraph-Level DOCX Engine & Single-Page Calibration
- **Active Word OXML Hyperlinks**: Generates Word `<w:hyperlink>` relationships directly in python-docx, styling live project titles in bold crimson with active external URLs.
- **Brief Tech Stack & Timeline**: Formats project headers with title, brief tech stack, and timeline dates: `Project Title | Tech Stack | Month Year – Month Year`.
- **Adaptive Bullet Headroom Filling**: Dynamically allocates 3 high-impact bullets per project (or up to 4 for 2 projects) with calibrated paragraph line spacing (`Pt(0)` before, `Pt(1.5)` after, `1.05` line-spacing) ensuring the document strictly fills exactly 1 single page.
- **Metadata Cleansing**: Automatically filters out markdown syntax, bold labels, and repository URLs from resume bullet text.
- **File-Lock Safe Writer**: Catches Windows Word file-lock exceptions and saves to safe fallback paths without failing the run.

### Pillar 4: Real-Time Quota Tracking, Company Dossier & Humanized Outreach Hub
- **Real-Time Daily API Quota Tracker**: Persists daily request counts in SQLite (`api_quotas` table) and exposes `GET /api/quotas`, updating the UI dashboard rings live as runs execute.
- **Company Technical Dossier**: Scrapes landing page metadata and hero value propositions ($0 cost) to extract exact product missions and industry categories (*EdTech, DevTools, AI/ML, FinTech*).
- **JD Architectural Challenge Deconstructor**: Analyzes Job Description text to identify core engineering priorities (*Real-Time Concurrency, Atomic Database Integrity, High-Throughput APIs, Complex State Synchronization*).
- **3 Toggleable Pitch Styles**: Dynamically generates either **Engineering Deep-Dive** (for Tech Leads/EMs), **3-Part Scannable Matrix** (for Recruiters), or **Executive Cold Pitch** (for Founders/VPs) with sub-1.5s live regeneration.
- **Humanized Engineering Voice & Anti-AI Blacklist**: Strictly purges robotic filler words (*"delve", "testament", "tapestry", "foster", "synergy", "cognitive friction"*) in favor of authentic developer problem $\rightarrow$ friction $\rightarrow$ fix storytelling.
- **Active Live Demo & GitHub Link Embeddings**: Seamlessly embeds verified project repository URLs and live deployment links in outreach copy.
- **3-Stage Hallucination Containment**: Deterministic verification (`passes_containment_check`) rejects ungrounded claims.
- **4-Stage Employment Authenticity Verifier**: Eliminates EdTech course participants, bootcamp students, and corrupt dates (1800s/1900s), discovering genuine internal corporate employees.
- **3-Archetype Strategic Classifier**: Segregates contacts into `👑 Decision Maker`, `🎯 Talent Gateway`, and `🌐 Network Bridge`.
- **Strict $\le 200$-Character LinkedIn Connection Note Guard**: Synthesizes notes under 180 chars with deterministic bounds to fit LinkedIn's 200-char free invite limit in 1 single batched Groq request.
- **Hunter.io-Style Email Engine**: Generates corporate email permutations (`first.last@company.com`, `first@company.com`, `f.last@company.com`) from the company domain with 1-click copy and pre-filled `mailto:` compose links.
- **DNS-over-HTTPS MX Deliverability**: Validates company mail servers via Google DNS-over-HTTPS, identifying mail host providers (*Zoho Mail*, *Google Workspace*, *Microsoft 365*) and confidence ratings.
- **Multi-Channel Contact Bar**: Provides direct Google Contact Dork, GitHub User Search, and Twitter/X lookup buttons to bypass LinkedIn connection gates.

---

## 3. Technology Architecture & Zero-Cost Cloud Model

* **Frontend**: React 18, Vite, TypeScript, Tailwind CSS (Tactical Red/Black palette).
* **Sidecar Backend**: FastAPI running on Python 3.13 (`http://127.0.0.1:8000`).
* **Desktop Runtime**: Tauri v2.
* **Database**: Local SQLite3 (`maxume_local.db`) with thread-safe `with self.get_connection() as conn:` context managers.
* **Zero Cost Strategy**:
  - **Ollama**: Local open-source inference (`qwen2.5:7b-instruct`) with dynamic VRAM limits.
  - **Groq LPU**: Free tier (14,400 requests/day) running `qwen/qwen3.6-27b` and `openai/gpt-oss-120b`.
  - **Google Gemini**: Free tier (1,000 requests/day) running `gemini-3-flash-preview` for multimodal screenshot OCR and project reranking.
  - **Google News RSS Wire**: Free, unlimited real-time press and news aggregation.
  - **Hunter.io Pattern Synthesizer & DNS MX Validator**: $0.00 / free forever with no API limits.
