# Maxume Project Changelog

All notable changes, architectural pivots, and enhancements are documented here.

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
