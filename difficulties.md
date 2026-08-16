# Difficulties & Technical Challenges Solved

### 1. Google Cloud CSE Lockdown for New Accounts
* **Difficulty**: Google Cloud permanently blocks `customsearch.googleapis.com` with `HTTP 403 (Permission Denied)` on new projects, and locks the "Search the entire web" toggle.
* **Resolution**: Built a zero-config, real-time Google News RSS and live press wire aggregator, plus automated LinkedIn persona targeting for senior engineers and managers.

### 2. Word Document Spilling Over to Page 2
* **Difficulty**: Injecting multiple projects with lengthy bullet points into an already complete master resume template pushed Education onto a second page.
* **Resolution**: Re-calibrated paragraph metrics (`DocxEngine.rebuild_resume`) with exact `Pt` line spacing and strict single-page guardrails (top 3 projects, max 2 bullets each).

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
