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
      GitHub Profile     |       |       |       | Real Employee Discovery & Hunter.io
      & Local Manifests  |       |       |       | (Live Search Decoders + DNS-over-HTTPS)
    +----------------v---+       |       |       +--------------------+
    |  GitHub / Local    |       |       |                            |
    |  (package.json,    |       |       |                            v
    |  Cargo, req.txt)   |       |       |                +-----------+-----------+
    +--------------------+       |       |                |  DNS MX Mail Validator|
                                 |       |                |  + Hunter.io Pattern  |
             Local SQLite DB     |       |                |  Synthesizer ($0)     |
             (SSOT, Projects,    |       |                +-----------------------+
             Contacts, History)  |       |
    +----------------v-----------+       | High-Context OCR & Reranking
    |  maxume_local.db           |       | (Gemini 2.5 Flash API - $0)
    +----------------------------+       | 
                                         v
                     Local Inference     +------------------------------+
                     (Ollama API - $0)   |  Gemini Flash OCR & Rerank   |
    +----------------v-----------+       |  + Groq Llama 3.3 70B ($0)   |
    |  Ollama (Local VRAM)       |       |  + Grounded Containment Guard|
    |  Qwen 2.5 7B Instruct      |       +------------------------------+
    +----------------------------+
```

---

## 2. Hybrid Cloud-Local Inference Pipeline

To minimize cloud API usage, preserve privacy, and maintain a **$0/month permanent free tier**, Maxume implements a multi-provider scheduling pipeline:

1. **Grounded Codebase Analysis & Bullet Synthesis**
   * *Engine*: Groq LPU (`llama-3.3-70b-versatile`) / Gemini 2.5 Flash / Local Ollama.
   * *Execution*: Reads detected multi-manifest technologies (`Prisma`, `Socket.io`, `Zustand`, `FastAPI`, `Tauri`) and synthesizes high-impact bullets focusing on **authentic system design, concurrency safety, and atomic transactions without fabricating fake metrics**.

2. **Multimodal Screenshot OCR & Reranking**
   * *Engine*: Google Gemini 2.5 Flash.
   * *Execution*: Compresses screenshots via Pillow and extracts full job descriptions, followed by semantic reranking of candidate projects.

3. **Real-Time Signal Research & 3-Stage Containment Guard**
   * *Engine*: Google News RSS Wire + Gemini Flash.
   * *Execution*: Aggregates dated press signals and funding announcements. A deterministic post-hoc containment check (`passes_containment_check`) rejects ungrounded claims.

4. **Targeted Employee Networking & Hunter.io Email Engine**
   * *Engine*: Public Search Decoders + Google DNS-over-HTTPS.
   * *Execution*: Discovers real named employees with direct `/in/` personal profiles, runs live DNS MX validation to verify mail routing servers (*Zoho Mail*, *Google Workspace*, *Microsoft 365*), and synthesizes standard corporate email permutations.

5. **Single-Page Paragraph-Level DOCX Compilation**
   * *Engine*: `python-docx` + raw Word OXML XML relationships.
   * *Execution*: Injects clickable hyperlinks, styles headers with brief tech stacks and formatted timelines, and calibrates line spacing to strictly fill **exactly 1 single page**.

---

## 3. Storage & Data Persistence

* **Database**: Local SQLite database (`maxume_local.db`) with thread-safe connection pooling.
* **Schema Tables**:
  - `projects`: Directory path, commit hash, summary markdown, live demo URL, visibility flag (`is_hidden`), and timestamps.
  - `applications`: Company name, role title, status, raw JD, output path, personalization status.
  - `application_projects`: Junction table linking applications to ranked projects.
  - `networking_contacts`: Real employee name, tagline, LinkedIn `/in/` profile, domain, primary email, alternative patterns, DNS MX provider, and multi-channel links.
  - `config`: Local settings, default directories, and user preferences.
