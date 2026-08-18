# Engineering Learnings & Key Insights

### 1. Document Engineering with Python-Docx
* `python-docx` manages styles at the paragraph and run level, but lacks high-level APIs for hyperlinks. Embedding Word `<w:hyperlink>` directly via `oxml` with relationship IDs (`r:id`) is the most reliable way to insert styled, clickable URLs without corrupting document XML schemas.
* Word line spacing must be set explicitly using `Pt(1.5)` space-after and `1.05` line-spacing to guarantee that dynamic content fits within 1-page constraints.

### 2. Grounded Architecture Over Fabricated Metrics
* Generic percentages (e.g. "35% latency reduction on 10k users") look artificial to experienced engineering hiring managers when applied to personal or open-source projects.
* Focusing on **authentic architectural mechanisms** (e.g. atomic database transactions, compound unique constraints, room multiplexing, IPC sidecar lifecycles, TF-IDF vectorization) delivers far higher credibility and interview impact.

### 3. Local-First & Airgapped Architecture
* Combining a local SQLite SSOT with local inference (Ollama) ensures that candidate master resumes, source code, and application logs never leave the local machine.
* Cloud AI (Groq, Gemini) should be utilized strictly for stateless tasks (creative copy synthesis, OCR transcription) using non-sensitive snippets.

### 4. Deterministic Guardrails Over Prompt Engineering
* LLMs cannot be trusted to self-police hallucinations through prompts alone.
* Post-hoc deterministic entity and number containment checks (`passes_containment_check`) provide mathematical guarantees against false claims reaching employers.

### 5. Multi-Manifest Dependency Inspection
* A single language identifier on GitHub (`language: "Python"`) is inadequate for modern multi-tier applications.
* Simultaneously parsing `package.json`, `requirements.txt`, `Cargo.toml`, and GitHub's `/languages` API is required to capture the full breadth of frameworks and tools used in a repository.

### 6. Zero-Cost DNS MX Validation for Outreach
* Residential ISPs block direct SMTP port 25 connections to prevent spam, making socket-level email handshakes unreliable on personal machines.
* Utilizing **Google DNS-over-HTTPS** to query MX records provides a 100% reliable, zero-block method to verify that a target company domain receives mail and identify its enterprise mail host provider (*Zoho Mail*, *Google Workspace*, *Microsoft 365*).

### 7. Windows Installer Process Lifecycle Management
* On Windows, running background binaries prevent installer overwrites with `ERROR_SHARING_VIOLATION`.
* NSIS pre-install hooks (`nsExec::Exec 'taskkill.exe /F /IM maxume.exe /IM maxume_backend.exe /T'`) combined with Tauri window destruction listeners guarantee seamless upgrades without file lock errors.

### 8. Resilient Multi-Tier Project Matching
* Fallback systems should never default to fixed or alphabetical ordering.
* Pre-scoring candidates with a domain-aware semantic relevance metric guarantees that the best projects for a role (e.g. ML vs. Full Stack) are always surfaced even if cloud LLM endpoints hit rate limits or transient outages.

### 9. Reasoning Model Tag Cleansing in Automated Pipelines
* Modern reasoning LLMs (such as Qwen 3.6 / DeepSeek variants) emit `<think>...</think>` thoughts in raw output.
* Automated extraction pipelines must explicitly sanitize thinking tags prior to parsing JSON or inserting text into downstream resumes and cover letters.

