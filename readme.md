# Maxume: AI Job Application Maximizer
### Complete Engineering Specifications & Project Blueprint

Maxume is a local-first hybrid desktop application designed to maximize job application quality and speed. It orchestrates a local open-weights LLM with zero-cost cloud APIs to produce tailored resumes, cover letters, personalized outreach emails, and targeted networking referral campaigns — and, distinctively, grounds that personalization in real, verifiable, company-specific signals rather than generic template language.

---

## Documentation Directory

This blueprint consists of the following documents. They are the single source of truth for anyone (human or AI coding agent) implementing Maxume — read them before writing code, and keep them updated as the implementation evolves.

| # | File | Purpose |
|---|---|---|
| 1 | `readme.md` | System entry point, design philosophy, quick-start roadmap |
| 2 | `architecture.md` | System topology, hybrid pipeline mechanics, local/cloud boundaries |
| 3 | `projectoverview.md` | Core workflow, incremental Git-sync, DOCX style-copying algorithm |
| 4 | `companyresearch.md` | Company-signal scraping pipeline and the hallucination guard |
| 5 | `ui.md` | Aesthetic and UI layout spec (Legion Red & Black dark mode) |
| 6 | `codestandards.md` | Folder layout, rate limiting, code quality rules |
| 7 | `progresstracker.md` | Phased timeline, milestones, SQLite schema |
| 8 | `gitworkflow.md` | Branching model, micro-commit discipline, release checklist |
| 9 | `changelog.md` | Running log of shipped changes, Conventional Commits mapping |
| 10 | `security.md` | PII isolation, credential storage, scraping ethics |
| 11 | `apicontracts.md` | JSON schemas for Ollama, Gemini, Groq, Google CSE, and company-signal fetch |
| 12 | `envsetup.md` | Installation, dependencies, bootstrap sequence |
| 13 | `decisions.md` | Architecture Decision Records (ADRs) |
| 14 | `difficulties.md` | Technical risk register: VRAM, rate limits, scraping brittleness, hallucination |
| 15 | `testing.md` | Test strategy: unit, integration, manual QA gates |
| 16 | `learnings.md` | Retrospective insights on local-first LLM product development |
| 17 | `interviewprep.md` | Interview-ready Q&A mapped to Maxume's design decisions |
| 18 | `cliprompt.md` | The master execution prompt for scaffolding Maxume with an agentic coding CLI (Claude Code / Cursor / Aider) |

---

## Key Design Principles

*   **Absolute Privacy**: PII-containing data (master resume, contact details) is processed exclusively by the local LLM (Ollama), or opt-in cloud failover only with explicit, per-session consent.
*   **Zero Operating Cost**: Built entirely on permanent free tiers — Ollama (local), Gemini Developer API, Groq Cloud, Google Custom Search.
*   **VRAM Containment**: Targets an RTX 3060 Laptop (6GB VRAM), keeping local inference under a ~5.2GB working budget via context capping and Flash Attention.
*   **Tauri v2 + Python Sidecar**: Native Rust webview UI, freeing hardware headroom for local AI inference.
*   **Grounded Personalization, Not Fabrication**: Every company-specific claim in generated cover letters and outreach emails must trace back to a real, cited, recently-fetched source. If no such signal exists, Maxume says so explicitly rather than inventing one — see `companyresearch.md`.

---

## Quick Start

1. Read `envsetup.md` and provision your local Ollama model + free-tier API keys.
2. Read `architecture.md` and `projectoverview.md` to understand the pipeline end to end.
3. If using an agentic coding CLI to scaffold the app, hand it `cliprompt.md` directly — it references every other doc by name and encodes the build order, git discipline, and quality gates.
4. Track implementation against `progresstracker.md`'s phase checklist.
