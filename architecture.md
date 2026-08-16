# Architecture Specification: Maxume System Design

## 1. System Topology Overview

Maxume is built on a **Decoupled Client-Sidecar Topology**. All heavy computation and API integration runs on the user's own machine. The frontend is **Tauri v2** (Rust + React); the backend is a **Python FastAPI Sidecar**, compiled and packaged alongside Tauri, orchestrating the local database, local filesystem, the local LLM engine (Ollama), and cloud API integrations.

```
                     +----------------------------------+
                     |         Maxume Tauri UI          |
                     |  (React, TypeScript, Tailwind)   |
                     +-----------------+----------------+
                                       |
                                       | IPC Channels (Tauri Commands)
                                       v
                     +-----------------+----------------+
                     |    Python FastAPI Sidecar        |
                     | (FastAPI, SQLite, python-docx)   |
                     +---+-------+-------+-------+------+
                         |       |       |       |
      Local Projects     |       |       |       | Public Profiles + Company Signals
      & Watcher          |       |       |       | (Google CSE + Company Site Fetch)
    +----------------v---+       |       |       +--------------------+
    |  /projects Folder  |       |       |                            |
    |  (Git Commit Check)|       |       |                            v
    +--------------------+       |       |                +-----------+-----------+
                                 |       |                |  Google Search JSON   |
             Local SQLite DB     |       |                |  + Company Newsroom / |
             (Logs, History,     |       |                |  Blog Fetch  ($0)     |
             Research Signals)   |       |                +-----------------------+
    +----------------v-----------+       |
    |  maxume_local.db           |       | High-Context Processing, Screen OCR,
    +----------------------------+       | and Signal Summarization (Grounded)
                                         | (Gemini 2.5 Flash-Lite API - $0)
                     Local Inference     |
                     (Ollama API - $0)   v
    +----------------v-----------+    +--+--------------------------+
    |  Ollama (Local VRAM)       |    |  Gemini API (Cloud - $0)    |
    |  Qwen 2.5 7B Instruct      |    |  + Hallucination Guard Pass |
    |  Q4_K_M                    |    +------------------------------+
    +----------------------------+
```

---

## 2. Hybrid Cloud-Local Inference Pipeline

To minimize cloud API usage, preserve maximum privacy, and keep costs at **$0/month**, Maxume implements a multi-provider scheduling pipeline with five stages:

1.  **PII Sanitization & Master Resume Parsing (Local Ollama)**
    *   *Input*: Local master resume in `.docx` format containing email, phone, and home address.
    *   *Engine*: Local Ollama running `qwen2.5:7b-instruct`.
    *   *Execution*: Ollama extracts structured skills, work experience, and template style metadata locally. PII never leaves the machine at this stage.

2.  **Semantic Reranking & Key Matching (Local Embeddings + Gemini Rerank)**
    *   *Input*: Raw job description text or a compressed screenshot.
    *   *Execution*: A local cosine-similarity filter over `/projects` pulls the top 8 candidate projects; their titles and bullet summaries (no PII) are passed to **Gemini 2.5 Flash-Lite** to pick the best 3–4 matches and extract 4–5 strong bullets each.

3.  **Company Signal Research (Google CSE + Targeted Fetch + Gemini, Grounded)**
    *   *Input*: Company name and, where available, its careers/about page URL.
    *   *Execution*: Maxume searches for recent, citable, public signals about the target company — news coverage, product launches, funding rounds, engineering blog posts — and passes only the retrieved snippets (never invented content) to Gemini for a short, source-cited summary. See `companyresearch.md` for the full pipeline and its **hallucination guard**, which forces the stage to explicitly report "no timely signal found" rather than let a downstream model fabricate one.

4.  **Creative Generation (Groq Llama 3.3 70B)**
    *   *Input*: Matched project bullets, target JD, and the company-signal brief from Stage 3 (which may be empty, and must be treated as empty when it is).
    *   *Execution*: High-speed, high-reasoning inference via Groq (`llama-3.3-70b-specdec`) produces cover letters, referral pitches, and application emails at 300+ tokens/second. The system prompt for this stage explicitly forbids referencing company facts that were not present in the Stage 3 brief.

5.  **Networking Discovery (Google CSE Loophole)**
    *   *Input*: Company name and target role families (SDE, HR, Recruiter).
    *   *Execution*: A structured `site:linkedin.com/in/` query surfaces public employee names, taglines, and profile URLs for the networking drawer — no authenticated scraping, no LinkedIn account risk.

---

## 3. Dynamic Local Model Swapping

Maxume is model-agnostic. The default is `qwen2.5:7b-instruct` (Q4_K_M quantization), chosen for its balance of multilingual coding ability and resume-extraction quality on 6GB VRAM. Users can hot-swap models at runtime.

### Dynamic Model Discovery Sequence
*   On boot, the FastAPI sidecar queries `GET http://localhost:11434/api/tags`.
*   The response lists locally available GGUF models.
*   The Tauri React UI surfaces this list in a **Model Manager Settings dropdown** (e.g. `llama3.1:8b`, `mistral:7b`, `gemma3:12b`).

### Dynamic VRAM Guardrails

$$\text{Required VRAM} \approx \text{Model File Size} + \text{Runtime Overhead (~0.3–0.4GB)} + \left( \text{num\_ctx} \times \text{overhead\_factor} \right)$$

On a 6GB RTX 3060 Laptop, background display/OS processes typically reserve 500MB–800MB, leaving a **~5.2–5.5GB working budget**. If a user selects a model whose file size alone would exceed that budget after overhead (e.g. `qwen2.5:14b` at ~9GB), Maxume intercepts the call before dispatch and shows an **in-UI hardware warning**:

> "Target model exceeds VRAM budget. Loading it will force CPU layer offloading, dropping throughput from ~60 tok/s to ~5–8 tok/s. Switch to Qwen 2.5 7B Q4_K_M, or reduce context to 1024 tokens."

See `difficulties.md` §1 for the full VRAM budget math, reconciled against actual base-weight + KV-cache figures.

---

## 4. Zero-Cost Google Custom Search Engine (CSE) Integration

To bypass LinkedIn's login walls and anti-bot mechanisms, Maxume uses Google's Programmable Search Engine API rather than any authenticated scraper.

*   **The Setup**: A free Programmable Search Engine ID plus a Google Custom Search JSON API key, providing 100 free queries/day.
*   **The Query**:
    ```
    GET https://customsearch.googleapis.com/customsearch/v1?q=site:linkedin.com/in/+%22[COMPANY_NAME]%22+AND+(%22Software+Engineer%22+OR+%22SDE%22+OR+%22HR%22+OR+%22Recruiter%22)&cx=[CSE_ID]&key=[API_KEY]
    ```
*   **The Output**: Employee name, title/tagline, and a clean public profile URL — extracted from Google's structured JSON, never from an authenticated LinkedIn session.

---

## 5. Company Signal Fetch Boundary (New)

This stage is architecturally separate from the LinkedIn-employee lookup above, even though both use Google CSE credentials, because it has a different trust boundary: its output is quoted (indirectly) inside outbound cover letters and emails, so correctness matters more than for a contact card. Its full design — source tiering, snippet-only summarization, and the hallucination guard contract — lives in `companyresearch.md` and its request/response schema lives in `apicontracts.md` §5.
