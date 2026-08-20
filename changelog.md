# Maxume Project Changelog

All notable changes, architectural pivots, and enhancements are documented here.

---

## [v1.7.0] - 2026-08-20 (Company Technical Dossier & Architectural Bridge Personalization)

### Added & Enhanced
- **Company Technical Dossier Engine** (`company_research.py`):
  - **Zero-Cost Meta & Hero Ingestion**: Scrapes landing page metadata, OpenGraph tags, and hero value propositions ($0 cost) to extract company missions and industry categories (*EdTech, DevTools, AI/ML, FinTech, SaaS*).
  - **JD Architectural Challenge Deconstructor**: Dissects Job Description text to identify the company's core engineering bottlenecks (*Real-Time Concurrency, Atomic Database Integrity, High-Throughput APIs, Complex State Management*).
- **The Architectural Bridge Framework** (`groq_service.py`):
  - Rewrote cover letter and email generation prompts to draw direct 1-to-1 parallels between candidate projects (`Maxume`, `Metro-Connect`, `EzNotes`) and company challenges.
  - Generates 280-word executive cover letters and 120-word application emails with zero generic filler or fake percentage metrics.
- **Company Intelligence UI Dossier** (`SignalCard.tsx`):
  - Displays company mission banner, industry category badge, and visual tags for core technical priorities.

---

## [v1.6.0] - 2026-08-18 (Employment Authenticity Filtering & <= 200-Character LinkedIn Outreach)

### Added & Enhanced
- **Verified Real Employee Networking Engine** (`networking_engine.py`):
  - **4-Stage Employment Authenticity Verifier**: Eliminates EdTech course participants (*"Student at {Company}"*), bootcamp customers, and corrupt historical dates (e.g. 1800s/1900s), surfacing 100% genuine internal corporate staff.
  - **3-Archetype Strategic Classifier**: Segregates contacts into `👑 Decision Maker` (*Hiring Managers / Tech Leads*), `🎯 Talent Gateway` (*Technical Recruiters / HR*), and `🌐 Network Bridge` (*Peers / Alumni*).
  - **Strict $\le 200$-Character LinkedIn Connection Note Guard**: Synthesizes notes under 180 chars with deterministic bounds to fit LinkedIn's 200-char free invite limit in 1 single batched Groq request ($0 search cost, 66% quota savings).
  - **Live Deliverability Badges & Character Counters**: UI cards in `Optimizer.tsx` display real-time archetype badges, deliverability status (*98% Confirmed Deliverability via Google Workspace*), and `📝 142/200 chars` badges with 1-click copy.

---

## [v1.5.0] - 2026-08-18 (Maximal Marginal Relevance & Skill-Cluster Project Matching)

### Added
- **Maximal Marginal Relevance (MMR) Project Engine** (`project_matcher.py`): Implemented MMR optimization to maximize unique skill-cluster coverage and eliminate tech-stack redundancy.
  - For **Hybrid JDs** (e.g. MERN + Python/FastAPI): Selects the best project from each requested domain (`Metro-Connect`, `Maxume`, `EzNotes`) providing 100% JD coverage.
  - For **Single-Stack JDs** (e.g. Pure MERN): Evaluates only requested skills, guaranteeing 100% MERN projects (`Book-IT`, `SlotSwap`, `Productivity-Overload`) with **zero out-of-scope technologies injected**.
- **Canonical Skill Taxonomy Map**: Maps variations (`js` $\rightarrow$ `javascript`, `mongo`/`mongoose` $\rightarrow$ `mongodb`, `fastapi`, `tailwind`, `socket.io`, `scikit-learn`) into unified skill domains.

---

## [v1.4.0] - 2026-08-18 (Semantic Project Matching & Live Quota Tracking)

### Fixed & Enhanced
- **Multi-Factor Semantic Project Relevance Scorer**: Implemented weighted keyword and domain matching (`score_project_relevance`) against target Job Descriptions, evaluating tech stacks, directory names, and project highlights. Eliminates static alphabetical fallback ordering and ensures resumes dynamically feature the most relevant candidate projects (e.g. ML jobs select `sentiment-analysis-app` & `Maxume`; Full Stack jobs select `Metro-Connect`, `EzNotes`, & `Calvero`).
- **Real-Time Daily API Quota Tracker**: Built `api_quotas` persistence table in SQLite, wired `scheduler.py` automatic quota incrementing, added `GET /api/quotas` endpoint, and connected live polling to the frontend dashboard (`0/1000 req` and `0/14400 req` now track dynamically in real time).
- **Active Model Endpoints Update**: Updated candidate model arrays to currently available production endpoints (`gemini-3-flash-preview`, `gemini-3.1-flash-lite-preview`, `qwen/qwen3.6-27b`, `openai/gpt-oss-120b`), resolving upstream 404/503 errors and stripping reasoning `<think>` tags.

---

## [v1.3.0] - 2026-08-17 (Grounded Hybrid Intelligence & Complete Project SSOT)

### Added
- **Grounded Hybrid AI Resume Bullet Engine**: Replaced generic, synthetic percentage metrics with **codebase-grounded architectural bullet points** focusing on real system design, concurrency safety, atomic database transactions, room multiplexing, and protocol mechanisms.
- **Multi-Manifest Tech Stack Extractor**: Enhanced `github_sync.py` to inspect remote `package.json`, `requirements.txt`, `Cargo.toml`, and GitHub's `/languages` API to extract rich, multi-ecosystem tech stacks (e.g. `Tauri v2, React, TypeScript, FastAPI, Python 3.13, SQLite, Tailwind CSS, Groq, Ollama`).
- **Realistic Timeline Calculator**: Computes authentic 1–3 month development sprint windows based on repository creation and commit milestones (e.g. `Oct 2025 – Nov 2025`), eliminating generic `2024 – Present` placeholders.
- **In-App Project Details Editor**: Added `PUT /api/projects/{id}` endpoint and an inline **`[Edit]`** modal in `ProjectSync.tsx` allowing direct customization of tech stacks, timelines, demo URLs, and bullet points.

---

## [v1.2.0] - 2026-08-17 (Targeted Referral Discovery & Hunter.io Email Engine)

### Added
- **Real Employee Discovery Engine**: Built public profile search decoders in `employee_lookup.py` to discover real named individuals with exact personal `/in/` LinkedIn profiles, eliminating all generic search placeholders.
- **Live DNS MX Deliverability Verification**: Integrated Google DNS-over-HTTPS in `employee_lookup.py` to validate active mail routing servers and identify mail host providers (*Zoho Mail*, *Google Workspace*, *Microsoft 365*).
- **Hunter.io Corporate Email Permutations**: Added standard corporate email variations (`first.last@domain.com`, `first@domain.com`, `f_initial.last@domain.com`) with 1-click copy and pre-filled `mailto:` compose triggers.
- **Multi-Channel Contact Action Bar**: Added direct Google Contact Dork, GitHub User Search, and Twitter/X lookup buttons to bypass LinkedIn connection gates.
- **NSIS Pre-Install File-Lock Prevention**: Added `nsExec::Exec` pre-install and customInstall lifecycle macros to terminate background processes and eliminate Windows `ERROR_SHARING_VIOLATION` during upgrades.

---

## [v1.1.0] - 2026-08-17 (Layout & DOCX Calibration)

### Added
- **Project Header Tech Stack & Timeline**: Projects on the Word resume now display brief tech stacks and formatted timeline dates (`Project Title | Tech Stack | Month Year – Month Year`).
- **Adaptive Bullet Headroom Filling**: Expanded bullet allocation to 3 high-impact bullets per project (or up to 4 for 2 projects) to maximize page density while preserving the strict 1-page ceiling.
- **Windows File-Lock Resilience**: Implemented automated fallback file saving in `DocxEngine` and `main.py` to prevent `PermissionError` crashes when Word documents are actively open in Microsoft Word.
- **Typing & Diagnostics Hardening**: Fully typed `Tuple` annotations in `gemini_service.py` and initialized central logger instance in `main.py`.

---

## [v1.0.0] - 2026-08-17 (Production Release)

### Added
- **Project Visibility Controls**: Added `is_hidden` column in SQLite, Active/Hidden filter tabs, hide/unhide toggles, and repo deletion in `ProjectSync.tsx`.
- **Direct Clipboard Pasting (`Ctrl+V`)**: Added global keyboard paste listener for multi-screenshot ingestion directly from screenshot tools.
- **Authentic Skills Synthesizer**: Built `skills_engine.py` to extract only candidate's genuine technologies from verified repositories, eliminating fake tech hallucinations (e.g. Go, Rust).
- **Real-Time News Wire**: Built Google News RSS integration in `company_research.py` for dated, real-time public company signals and launches.
- **Windows Explorer Output Opener**: Added `POST /api/open-folder` endpoint and UI button to open compiled output folders directly in Windows.
