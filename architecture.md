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

4. **Real-Time Signal Research & 3-Stage Containment Guard**
   * *Engine*: Google News RSS Wire + Groq / Gemini Flash.
   * *Execution*: Aggregates dated press signals and funding announcements. A deterministic post-hoc containment check (`passes_containment_check`) rejects ungrounded claims.

5. **Targeted Employee Networking & Hunter.io Email Engine**
   * *Engine*: Public Search Decoders + Google DNS-over-HTTPS.
   * *Execution*: Discovers real named employees with direct `/in/` personal profiles, runs live DNS MX validation to verify mail routing servers (*Zoho Mail*, *Google Workspace*, *Microsoft 365*), and synthesizes standard corporate email permutations.

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
