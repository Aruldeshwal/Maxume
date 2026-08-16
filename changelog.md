# Changelog: Maxume

All notable changes to Maxume are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/); every entry should be traceable to one Conventional Commit (see `gitworkflow.md` §2).

Categories per release: `Added`, `Changed`, `Fixed`, `Removed`, `Security`.

---

## [Unreleased]

### Added
- Tauri v2 + React TypeScript frontend with Legion Red & Black dark mode theme.
- Python FastAPI backend sidecar with PyInstaller target-triple packaging.
- SQLite SSOT database schema with tables for projects, applications, networking contacts, and company signals.
- Incremental Git Watcher with commit-hash signature comparison and markdown live demo URL extraction.
- Paragraph-Level DOCX style cloning engine (`docx_engine.py`) with OXML clickable hyperlink embedding.
- Single-page resume compile guardrail (enforcing maximum 4 projects and 4 bullets per project).
- Dynamic local Ollama model discovery (`GET /api/ollama/models`) with hardware VRAM budget guardrails.
- Pillow screenshot downscaling and grayscale compression pipeline (`image_optimizer.py`).
- Gemini 2.5 Flash-Lite multimodal OCR and semantic project selection/reranker (`gemini_service.py`).
- 5-Stage Company Signal Research pipeline (`company_research.py`) with 3-Stage Hallucination Guard (`containment.py`).
- Google Custom Search Engine (CSE) LinkedIn Employee Lookup module (`employee_lookup.py`).
- Groq LPU Creative Generation service (`groq_service.py`) for grounded cover letters, referrals, and emails.
- Token-Bucket Rate Limiter and asynchronous backoff scheduler (`scheduler.py`).
- Legion Dark Mode React UI tabs: `Dashboard.tsx`, `ProjectSync.tsx`, `Optimizer.tsx`, and `HistoryLogs.tsx`.
- Personalization `SignalCard.tsx` with distinct verified and muted informational none-found notice states.
- Networking `ContactCard.tsx` with referral pitch generator and clipboard copying.
- Live execution stream logger `TerminalLog.tsx` with phase telemetry and guard indicators.
- Vitest unit test suite covering `SignalCard`, `QuotaRing`, `TerminalLog`, and `App`.

---

## How to Use This File (for implementers and coding agents)

*   Every `feat:` or `fix:` commit adds exactly one bullet here, under the matching category, in the same commit.
*   Write entries for what a user or downstream developer would care about, not internal refactor detail (`refactor:` and `chore:` commits generally do **not** need a changelog line unless they change observable behavior).
*   When cutting a release (`gitworkflow.md` §5, Step 4), rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` and open a fresh empty `[Unreleased]` section above it.

### Example of a properly formed future entry:
```
## [0.3.0] - 2026-09-01

### Added
- Company signal research pipeline with hallucination guard (`company_research.py`).
- Personalization Brief UI card, including the "no recent signal found" state.

### Fixed
- SQLite schema: corrected `AUTOINCREMENT` keyword and a mismatched CHECK
  constraint on `networking_contacts.referral_status`.

### Security
- Company-signal fetcher now respects `robots.txt` and applies an 8s
  per-source timeout to prevent a slow external site from blocking the
  pipeline.
```
