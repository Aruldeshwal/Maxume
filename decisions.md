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
* **Decision**: Enforce max 3 projects and max 2 bullets each, calibrated with exact paragraph metrics (`Pt(0)` before, `Pt(1.5)` after, `1.05` line spacing) to guarantee a strict 1-page fit.

## ADR-009: Multi-Screenshot Base64 Ingestion with Clipboard Paste (`Ctrl+V`)
* **Status**: Accepted
* **Context**: Job descriptions often span multiple screenshots and users prefer pasting directly from clipboard.
* **Decision**: Add a global `Ctrl+V` paste listener and multi-image carousel strip, compressing images under 300KB before dispatching to Gemini Multimodal OCR.
