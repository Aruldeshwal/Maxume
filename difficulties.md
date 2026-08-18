# Difficulties & Technical Challenges Solved

### 1. Google Cloud CSE Lockdown for New Accounts
* **Difficulty**: Google Cloud permanently blocks `customsearch.googleapis.com` with `HTTP 403 (Permission Denied)` on new projects, and locks the "Search the entire web" toggle.
* **Resolution**: Built a zero-config, real-time Google News RSS and live press wire aggregator, plus public search decoders for direct `/in/` LinkedIn profiles.

### 2. Word Document Spilling Over to Page 2
* **Difficulty**: Injecting multiple projects with lengthy bullet points into an already complete master resume template pushed Education onto a second page.
* **Resolution**: Re-calibrated paragraph metrics (`DocxEngine.rebuild_resume`) with exact `Pt` line spacing and strict single-page guardrails (top 3 projects, max 3 bullets each with compact point spacing).

### 3. Metadata Tags Appearing in Resume Bullet Text
* **Difficulty**: Synced repository summary files included metadata headers (`**GitHub**: ...`, `**Language**: ...`) which were treated as bullet points by fallback extractors.
* **Resolution**: Created a strict regex-based metadata sanitizer (`is_valid_bullet_point`) that automatically detects and strips markdown headers, repository URLs, and tags before document generation.

### 4. Fake Technology Hallucinations in Skills Section
* **Difficulty**: Static placeholder skill lists injected technologies the user did not possess (e.g. Go, Rust).
* **Resolution**: Built `skills_engine.py` to extract only authentic skills verified across the user's 12 codebase repositories, dynamically sorting by target JD relevance.

### 5. Multi-Screenshot Ingestion & Clipboard Pasting
* **Difficulty**: Users often capture long job descriptions using multiple screenshots or direct clipboard captures (`Win + Shift + S`) rather than single file uploads.
* **Resolution**: Added a global `paste` event listener, multi-image carousel strip, and Pillow grayscale compression pipeline under 300KB before Gemini Multimodal OCR.

### 6. Tab Switching State Destruction in React
* **Difficulty**: React unmounted `<Optimizer />` upon switching tabs, resetting form inputs, logs, and compiled assets.
* **Resolution**: Replaced conditional rendering with persistent DOM wrappers using CSS visibility (`block` / `hidden`), preserving 100% of in-flight execution state.

### 7. Fabricated Percentage Metrics in Resume Bullets
* **Difficulty**: LLM prompts designed to produce Google XYZ bullets hallucinated artificial metrics (e.g. "35% latency reduction on 10k users") for open-source projects.
* **Resolution**: Implemented the **Grounded Hybrid AI Bullet Engine**, shifting focus to authentic system architecture, concurrency safety, atomic database transactions, room multiplexing, and protocol mechanisms without fake percentages.

### 8. Single-Language Misrepresentation on GitHub
* **Difficulty**: GitHub's primary language tag labeled multi-tiered applications with only one language (e.g. Maxume as only "Python").
* **Resolution**: Built a multi-manifest parser inspecting `package.json`, `requirements.txt`, `Cargo.toml`, and GitHub Languages API to construct comprehensive, multi-ecosystem tech stacks.

### 9. Generic Placeholder Links in Networking Outreach
* **Difficulty**: Searching for "Recruiter" produced generic search pages rather than real named employees.
* **Resolution**: Built public search decoders with strict `/in/` profile validation, live DNS MX deliverability verification via Google DNS-over-HTTPS, and Hunter.io corporate email permutation synthesis with multi-channel search buttons.

### 10. Windows File Locking (`ERROR_SHARING_VIOLATION`) During Installer Runs
* **Difficulty**: The background sidecar executable (`maxume_backend.exe`) locked itself in memory, preventing the NSIS setup installer from overwriting the file during upgrades.
* **Resolution**: Implemented `nsExec::Exec 'taskkill.exe /F /IM maxume.exe /IM maxume_backend.exe /T'` inside NSIS `customInit` and `customInstall` macros, plus Tauri window destruction event cleanup.

### 11. Upstream Model Deprecations and Static Fallback Repetition
* **Difficulty**: Upstream cloud model name shifts (`llama-3.3-70b-versatile` and `gemini-2.5-flash` returning 404s) caused the reranking pipeline to drop into fallback mode, which was previously sorted alphabetically and returned the same first 3 projects.
* **Resolution**: Updated model lists to verified active production endpoints (`gemini-3-flash-preview`, `qwen/qwen3.6-27b`, `openai/gpt-oss-120b`) and constructed a weighted semantic relevance matcher (`score_project_relevance`) ensuring tailored project selection even when offline.

### 12. Static Quota Counter Disconnected from Backend
* **Difficulty**: The frontend quota rings displayed static initial state without reflecting actual cloud API calls.
* **Resolution**: Added an `api_quotas` table in SQLite, connected automatic increments into `scheduler.execute_task`, and polled `GET /api/quotas` every 3 seconds to reflect live usage numbers.

