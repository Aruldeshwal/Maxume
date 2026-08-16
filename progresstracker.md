# Progress Tracker & DB Schema: Maxume Implementation Roadmap

## 1. Local SQLite Database Schema

Maxume relies on a local **SQLite database (`maxume_local.db`)** to maintain application history logs, targeted networking contact details, personalization research signals, and project incremental sync signatures. This keeps the output folder itself stateless — users can freely rename or move output folders without losing history.

```sql
-- Project Synchronization Signatures (SSOT for Incremental Sync)
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    directory_path TEXT NOT NULL UNIQUE,
    directory_name TEXT NOT NULL,
    last_commit_hash TEXT,
    summary_markdown TEXT,
    live_demo_url TEXT,
    last_synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Job Application Logs
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    role_title TEXT NOT NULL,
    status TEXT CHECK(status IN ('Draft', 'Applied', 'Interviewing', 'Offer', 'Rejected')) DEFAULT 'Draft',
    jd_raw_text TEXT,
    compressed_image_path TEXT,
    output_folder_path TEXT UNIQUE,
    personalization_status TEXT CHECK(personalization_status IN ('Found', 'None Found', 'Not Attempted')) DEFAULT 'Not Attempted',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Scraped LinkedIn Employee Profiles (Associated with Applications)
CREATE TABLE IF NOT EXISTS networking_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER,
    employee_name TEXT NOT NULL,
    employee_tagline TEXT,
    profile_url TEXT NOT NULL,
    referral_message_draft TEXT,
    referral_status TEXT CHECK(referral_status IN ('Not Contacted', 'Message Copied', 'Connected', 'Replied')) DEFAULT 'Not Contacted',
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- Company Research Signals (Personalization Pipeline, see companyresearch.md)
CREATE TABLE IF NOT EXISTS company_research_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER,
    signal_type TEXT CHECK(signal_type IN ('news', 'product_launch', 'funding', 'engineering_blog', 'other')),
    headline TEXT,
    source_url TEXT NOT NULL,
    source_tier INTEGER CHECK(source_tier IN (1, 2, 3)), -- 1=company domain, 2=press, 3=github
    published_at DATETIME,
    used_in_output INTEGER DEFAULT 0,       -- 1 if this signal was actually referenced in generated copy
    guard_check_passed INTEGER DEFAULT 1,   -- 0 if dropped by the hallucination guard's containment check
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
);
```

**Note on `AUTOINCREMENT`**: SQLite's keyword is `AUTOINCREMENT` (one word, no underscore). `INTEGER PRIMARY KEY` alone already auto-increments in SQLite via `ROWID`; `AUTOINCREMENT` is used here anyway for its guarantee against ID reuse, which matters for foreign-key integrity in `networking_contacts` and `company_research_signals`.

---

## 2. Phase-Based Implementation Timeline

```
  Phase 1: Local Backbone (Weeks 1-2)
  [x] Scaffolding Tauri v2 App & Sidecar packaging
  [x] SQLite DB schema migration & python driver integration
  [x] Incremental Git watcher implementation on /projects Folder

  Phase 2: Core Processing & Docx Engines (Weeks 3-4)
  [x] Paragraph-level DOCX style cloning engine
  [x] Markdown hyperlink regex extraction & title embedding
  [x] Dynamic Local Ollama tags lookup & model swapper

  Phase 3: Multimodal & Cloud APIs (Weeks 5-6)
  [x] Pillow local image compression setup for Screenshot JD input
  [x] Gemini 2.5 Flash OCR & Semantic Project Selection Integration
  [x] Company Signal Research pipeline + hallucination guard (company_research.py)
  [x] Google CSE loophole API integration for employee lookup
  [x] Groq Creative Generation API (emails/referrals/cover letters), consuming
      the research brief as a grounding constraint

  Phase 4: Legion UI & Polish (Weeks 7-8)
  [x] React Tailwind styling with Legion Dark Mode theme
  [x] Personalization Brief / SignalCard UI (found + "none found" states)
  [x] Asyncio rate limit queue & backoff telemetry logs on UI
  [x] Multi-platform build packaging (.msi, .deb, .app)
```

---

## 3. Milestones & Quality Validation Checklists

### Milestone 1: Perfect Docx Compilation Quality Gate
*   *Verification*: Open generated `.docx` file in MS Word and Google Docs.
*   *Validation Checks*:
    *   Verify margins, table columns, line spacing, and horizontal rules are preserved.
    *   Verify project titles contain active, clickable hyperlinks that direct to extracted project URLs.
    *   Confirm resume length does not spill onto page 2.

### Milestone 2: Offline Failover Validation Check
*   *Verification*: Run app with system internet adapters disabled.
*   *Validation Checks*:
    *   Ollama detects system is offline and falls back gracefully.
    *   UI prompts user with a clear, localized warning card: *"Offline Mode Active. Cloud integrations (Gemini, Groq, CSE) are suspended. Local projects watcher is active."*
    *   Company signal research silently degrades to `NO_SIGNALS_FOUND` rather than erroring the whole pipeline.

### Milestone 3: Zero-Cost Sandbox Verification
*   *Verification*: Complete 150 consecutive application test runs.
*   *Validation Checks*:
    *   Verify SQLite database records 150 application logs.
    *   Verify Google CSE queries (employee lookup + company signal search combined) do not exceed 100 queries/day.
    *   Verify API spend registers exactly **$0.00** across all provider billing dashboards.

### Milestone 4: Personalization Integrity Gate (New)
*   *Verification*: Run the 150-application test batch and audit `company_research_signals`.
*   *Validation Checks*:
    *   Every row with `used_in_output = 1` has a `source_url` that resolves and actually contains the claimed headline text.
    *   No generated cover letter or email references a company fact absent from a row with `guard_check_passed = 1` for that application.
    *   Applications with `personalization_status = 'None Found'` produce a letter with no company-specific factual claims (background/role-based framing only) and the UI shows the muted "none found" notice, not an error state.
