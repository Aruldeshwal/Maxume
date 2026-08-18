# Architectural Decision Records (ADR)

## ADR-001: Local-First Desktop App Architecture (Tauri + FastAPI Sidecar)
* **Status**: Accepted
* **Context**: Complete privacy for sensitive resumes and local source code while allowing high-performance Python document manipulation (`python-docx`, `PIL`).
* **Decision**: Pair a lightweight Tauri v2 frontend shell with an asynchronous FastAPI sidecar running locally on `127.0.0.1:8000`.

## ADR-002: Native Word OXML for Hyperlink Injection
* **Status**: Accepted
* **Context**: `python-docx` lacks high-level APIs for creating clickable hyperlinks in paragraph text.
* **Decision**: Construct OXML `<w:hyperlink>` relationships directly with `<w:rPr>` color runs, preserving template styles while adding active hyperlinks to live project URLs.

## ADR-003: Zero-Cost Developer Tier Cloud AI
* **Status**: Accepted
* **Context**: Users want $0/month operational costs without maintaining paid cloud subscriptions.
* **Decision**: Combine local Ollama inference (`qwen2.5:7b-instruct`) with generous free-tier cloud APIs (Groq LPU 14.4k req/day and Google Gemini Flash 1,000 req/day).

## ADR-004: Token-Bucket Rate Limiter & Automatic Backoff
* **Status**: Accepted
* **Context**: Cloud free tiers enforce strict RPM (Requests Per Minute) limits.
* **Decision**: Implement a centralized `TokenAwareScheduler` in `scheduler.py` that throttles outbound requests and applies exponential backoff on HTTP 429.

## ADR-005: 3-Stage Deterministic Hallucination Containment Guard
* **Status**: Accepted
* **Context**: LLM hallucination in job applications risks candidate reputation.
* **Decision**: Run a deterministic post-hoc containment algorithm (`passes_containment_check`) validating that all named entities and numbers exist in the scraped source text.

## ADR-006: Codebase-Grounded Authentic Skills Synthesis
* **Status**: Accepted
* **Context**: Static skill lists hallucinate unrepresented technologies (e.g. Go, Rust).
* **Decision**: Build `skills_engine.py` to scan all 12 verified repositories and master template, ranking genuine candidate skills by target JD relevance with zero hallucinations.

## ADR-007: Real-Time News Wire over Deprecated Google CSE
* **Status**: Accepted
* **Context**: Google locked down legacy Custom Search JSON API for all new developer accounts.
* **Decision**: Route company research through Google News RSS wire and direct domain fetch, providing dated real-time press releases with $0 spend and zero API locks.

## ADR-008: Calibrated Paragraph Metrics for Strict 1-Page Resume Layout
* **Status**: Accepted
* **Context**: Injected projects and bullets caused the resume to spill over to page 2.
* **Decision**: Enforce max 3 projects and calibrated point-level paragraph metrics (`Pt(0)` before, `Pt(1.5)` after, `1.05` line spacing) to guarantee a strict 1-page fit.

## ADR-009: Multi-Screenshot Base64 Ingestion with Clipboard Paste (`Ctrl+V`)
* **Status**: Accepted
* **Context**: Job descriptions often span multiple screenshots and users prefer pasting directly from clipboard.
* **Decision**: Add a global `Ctrl+V` paste listener and multi-image carousel strip, compressing images under 300KB before dispatching to Gemini Multimodal OCR.

## ADR-010: Adaptive Document Headroom Filling for Maximum Page Density
* **Status**: Accepted
* **Context**: Fixed 2-bullet caps left excessive unused whitespace at the bottom of the resume page.
* **Decision**: Dynamically allocate 3 bullets per project (or 4 bullets for 2 projects) with padding fallbacks to maximize information density while respecting the single-page boundary.

## ADR-011: Windows File-Lock Tolerant Document Writer
* **Status**: Accepted
* **Context**: On Windows, opening a `.docx` file in Microsoft Word locks the file from being overwritten, causing `PermissionError: [Errno 13]`.
* **Decision**: Wrap document and text file writers in try-except blocks that detect `PermissionError` and automatically write to a timestamped / suffixed path instead of crashing.

## ADR-012: Grounded Hybrid AI Resume Bullet Synthesis (Zero Fake Percentages)
* **Status**: Accepted
* **Context**: LLM prompts asking for Google XYZ bullets produced fabricated production traffic and latency percentages for student/open-source projects.
* **Decision**: Refactor bullet synthesis to focus on **authentic architectural mechanisms, concurrency safety, atomic database transactions, and data integrity** based on detected codebase manifests without inventing synthetic metrics.

## ADR-013: Multi-Manifest & Languages API Tech Stack Extraction
* **Status**: Accepted
* **Context**: Single-language tagging on GitHub misrepresented complex multi-tier projects (e.g. labeling Maxume as only "Python").
* **Decision**: Simultaneously inspect `package.json`, `requirements.txt`, `Cargo.toml`, and GitHub Languages API to construct full, multi-ecosystem tech stacks.

## ADR-014: Real Employee Discovery & Live DNS MX Validation
* **Status**: Accepted
* **Context**: Static search queries for "Recruiter" produced generic search links rather than real actionable individuals.
* **Decision**: Query public search streams specifically for direct `/in/` personal profiles, validate company mail servers via Google DNS-over-HTTPS (*Zoho Mail*, *Google Workspace*, *Microsoft 365*), and synthesize Hunter.io email variations with 1-click copy and `mailto:` triggers.

## ADR-015: NSIS Pre-Install Hook for Shared File Overwrite
* **Status**: Accepted
* **Context**: Upgrading the application while `maxume_backend.exe` was running in the background caused NSIS installer `ERROR_SHARING_VIOLATION`.
* **Decision**: Implement `nsExec::Exec 'taskkill.exe /F /IM maxume.exe /IM maxume_backend.exe /T'` in NSIS `customInit` and `customInstall` lifecycle macros to automatically terminate lingering background processes before file copying.

## ADR-016: Multi-Factor Semantic Relevance Scorer for Dynamic Project Matching
* **Status**: Accepted
* **Context**: Candidate projects were previously sorted alphabetically, causing the same first 3 projects to be selected sequentially on fallback or API errors.
* **Decision**: Build a weighted semantic matcher (`score_project_relevance`) scoring candidate tech stacks, directory names, domain keywords, and highlights against the target JD, ensuring dynamic and role-tailored project selection across AI and offline fallbacks.

## ADR-017: Daily API Quota Tracking with Automatic SQLite Increments
* **Status**: Accepted
* **Context**: Dashboard quota rings showed static `0/1000 req` and `0/14400 req` without tracking actual cloud API consumption.
* **Decision**: Create an `api_quotas` table in SQLite, automatically increment counters on successful task completion in `scheduler.py`, expose `GET /api/quotas`, and poll from `App.tsx` every 3 seconds to render live API usage in real time.

## ADR-018: Maximal Marginal Relevance (MMR) & Skill-Cluster Project Matching
* **Status**: Accepted
* **Context**: Multi-stack job descriptions (e.g. React/Next.js + Python/FastAPI) suffered from tech-stack redundancy when greedy matching selected 3 pure React projects, leaving Python/FastAPI completely unrepresented.
* **Decision**: Implement Maximal Marginal Relevance (MMR) where each candidate project is evaluated for its marginal coverage gain of unrepresented JD skills with a redundancy penalty for already-covered technologies, bounded strictly to skills explicitly requested in the JD.


