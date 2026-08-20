# Architecture Specification: Maxume System Design

## 1. System Topology Overview

Maxume is built on a **Decoupled Client-Sidecar Topology**. All heavy computation, file generation, and API integration runs locally on the user's machine. The desktop shell is **Tauri v2** (Rust + React 18 + Vite); the backend is a **Python FastAPI Sidecar** compiled with PyInstaller and managed as a subprocess, orchestrating the local SQLite SSOT, Word `.docx` manipulation, local Ollama inference, and zero-cost cloud APIs.

```
                     +----------------------------------+
                     |         Maxume Tauri UI          |
                     |  (React 18, TypeScript, Tailwind)|
                     +-----------------+----------------+
                                       |
                                       | HTTP REST API (http://127.0.0.1:8000)
                                       v
                     +-----------------+----------------+
                     |    Python FastAPI Sidecar        |
                     | (FastAPI, SQLite, python-docx)   |
                     +---+-------+-------+-------+------+
                         |       |       |       |
      Incremental Sync   |       |       |       | Real Employee Discovery & Hunter.io
      & GitHub Profile   |       |       |       | (Live Search Decoders + DNS-over-HTTPS)
    +----------------v---+       |       |       +--------------------+
    |  GitHub / Local    |       |       |                            |
    |  (package.json,    |       |       |                            v
    |  Cargo, req.txt)   |       |       |                +-----------+-----------+
    +--------------------+       |       |                |  DNS MX Mail Validator|
                                 |       |                |  + Hunter.io Pattern  |
             Local SQLite DB     |       |                |  Synthesizer ($0)     |
             (SSOT, Projects,    |       |                +-----------------------+
             Quotas, Contacts)   |       |
    +----------------v-----------+       | High-Context OCR & MMR Reranking
    |  maxume_local.db           |       | (Gemini 3 Flash API - $0)
    +----------------------------+       | 
                                         v
                     Local Inference     +------------------------------+
                     (Ollama API - $0)   |  Gemini Flash OCR & Rerank   |
    +----------------v-----------+       |  + MMR Diversity Selection   |
    |  Ollama (Local VRAM)       |       |  + Groq Qwen 3.6 / GPT-OSS   |
    |  Qwen 2.5 7B Instruct      |       |  + Grounded Containment Guard|
    +----------------------------+       +------------------------------+
```

---

## 2. Hybrid Cloud-Local Inference & Optimization Pipeline

To minimize cloud API usage, preserve privacy, and maintain a **$0/month permanent free tier**, Maxume implements a multi-provider scheduling pipeline:

1. **Maximal Marginal Relevance (MMR) & Skill-Cluster Project Matching**
   * *Engine*: `project_matcher.py` + `gemini_service.py`.
   * *Execution*: Evaluates candidate projects against target Job Descriptions using MMR to maximize **unique skill-cluster coverage** while penalizing redundancy. Single-stack roles (e.g. Pure MERN) get 100% on-stack projects with zero out-of-scope technologies; multi-stack roles (e.g. MERN + Python/FastAPI) get complete multi-domain coverage.

2. **Grounded Codebase Analysis & Bullet Synthesis**
   * *Engine*: Groq LPU (`qwen/qwen3.6-27b`, `openai/gpt-oss-120b`) / Gemini 3 Flash / Local Ollama.
   * *Execution*: Reads detected multi-manifest technologies (`Prisma`, `Socket.io`, `Zustand`, `FastAPI`, `Tauri`) and synthesizes high-impact bullets focusing on **authentic system design, concurrency safety, and atomic transactions without fabricating fake metrics**.

3. **Multimodal Screenshot OCR & Reranking**
   * *Engine*: Google Gemini 3 Flash (`gemini-3-flash-preview`).
   * *Execution*: Compresses screenshots via Pillow and extracts full job descriptions, followed by semantic reranking of candidate projects.

4. **Company Technical Dossier, Pitch Style Engine & Humanized Outreach**
   * *Engine*: `company_research.py` + `groq_service.py`.
   * *Execution*: Ingests landing page metadata and OpenGraph descriptions ($0 cost) to extract company missions and industry domains (*EdTech, DevTools, AI/ML, FinTech*). Deconstructs JD text into core architectural priorities (*Real-Time Concurrency, Atomic Database Integrity, High-Throughput APIs, Complex State Synchronization*). Dynamically generates 3 distinct pitch styles (**Engineering Deep-Dive**, **3-Part Scannable Matrix**, or **Executive Cold Pitch**) with an Anti-AI buzzword blacklist and embedded live demo/GitHub links. Instant in-app regeneration supported via `POST /api/regenerate-copy` (<1.5s).

5. **Verified Real Employee Networking & Strategic Outreach Engine**
   * *Engine*: `networking_engine.py` (Multi-Stream Decoders + Google DNS-over-HTTPS + Batched Groq).
   * *Execution*: Enforces a 4-Stage Verification Filter (student/customer blacklist, 1800s/1900s timeline sanity check, corporate preposition verification) to discover 100% genuine internal corporate staff. Classifies contacts into 3 Strategic Archetypes (`👑 Decision Maker`, `🎯 Talent Gateway`, `🌐 Network Bridge`), verifies mail routing via DNS MX (*Zoho Mail*, *Google Workspace*, *Microsoft 365*), and synthesizes strict $\le 200$-character LinkedIn connection notes in **1 single batched Groq request** ($0 search cost, 66% quota savings).

6. **Single-Page Paragraph-Level DOCX Compilation**
   * *Engine*: `python-docx` + raw Word OXML XML relationships.
   * *Execution*: Injects clickable hyperlinks, styles headers with brief tech stacks and formatted timelines, and calibrates line spacing to strictly fill **exactly 1 single page**.

7. **Real-Time Daily API Quota Tracker**
   * *Engine*: SQLite `api_quotas` table + `scheduler.py` auto-incrementing.
   * *Execution*: Auto-increments daily API counts upon every successful Gemini/Groq execution and serves live counts via `GET /api/quotas` for 3-second frontend dashboard polling.

---

## 3. Storage & Data Persistence

* **Database**: Local SQLite database (`maxume_local.db`) with thread-safe connection pooling.
* **Schema Tables**:
  - `projects`: Directory path, commit hash, summary markdown, live demo URL, visibility flag (`is_hidden`), and timestamps.
  - `api_quotas`: Daily date (`YYYY-MM-DD`), provider (`gemini`, `groq`), request count.
  - `applications`: Company name, role title, status, raw JD, output path, personalization status.
  - `application_projects`: Junction table linking applications to ranked projects.
  - `networking_contacts`: Real employee name, tagline, LinkedIn `/in/` profile, domain, primary email, alternative patterns, DNS MX provider, and multi-channel links.
  - `config`: Local settings, default directories, and user preferences.
