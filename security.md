# Security & PII Protection Blueprint: Maxume

## 1. PII Containment & Isolation Boundaries

Maxume is engineered to protect your highly sensitive **Personally Identifiable Information (PII)**. Your master resume contains historical records, physical addresses, phone numbers, and personal emails that must remain safe from unauthorized network transmission or indexing.

### The PII Security Guardrail Layout

```
 [ SENSITIVE LOCAL ZONE ]                             [ PUBLIC CLOUD ZONE ]
 (Master Resume, PII Data, Keys)                      (Anonymized Summaries Only)

  +--------------------------+                         +--------------------------+
  |  Master Resume (.docx)   |                         |   Gemini 2.5 Flash API   |
  |  - Email, Phone, Address  |                         |   - Context Parsing      |
  +------------+-------------+                         +------------^-------------+
               |                                                    |
               | Local Parser (Ollama Qwen 2.5 7B)                  |
               v                                                    | No PII Transmitted
  +------------+-------------+                                      |
  |  Structured Profile Log  |                                      |
  |  - Full Name (Strip Address)                                   |
  |  - Tech Bullet Summaries  +-------------------------------------+
  +--------------------------+
```

### Sandbox Containment Protocols
1.  **Strict Local Parsing Default**: Maxume's default configuration routes all parsing of the master `.docx` resume through the local **Ollama** backend. No PII is transmitted to external servers.
2.  **Anonymized Semantic Context Snippeting**: When matching resumes to job descriptions, Maxume strips header sections (name, phone, email, address) entirely before packaging technical bullets for semantic ranking. Contact details are never exposed during third-party API calls.
3.  **Local Output Compilations**: `/output/[company_name]` is hosted exclusively on the local disk. Maxume does not sync or store outputs on remote servers.
4.  **Company Research Isolation**: The company-signal research pipeline (`companyresearch.md`) never transmits any part of the resume, applicant name, or contact details — its outbound requests contain only the target company name and, where known, its public URL.

---

## 2. Low-Overhead Key & Credential Management

Because Maxume is a local desktop application and not a commercial SaaS, it prioritizes **simplicity, reliability, and ease of backup** over heavy credential managers.

### Simple .env Design Rules
*   **Location**: `.env` lives in the local user data folder (e.g. `%APPDATA%/Maxume/` on Windows or `~/.config/maxume/` on Linux).
*   **Exclusions**: The parent development repository strictly excludes `.env` via `.gitignore`, preventing accidental pushes of developer keys.
*   **Security Context**: Plaintext keys in a local `.env` are acceptable here because Maxume runs entirely locally — if an attacker can already read `%APPDATA%/Maxume/.env`, the machine itself is compromised, and no amount of `.env` obfuscation changes that.
*   **Access Control**:
    *   *Linux/macOS*: Maxume restricts `.env` permissions on launch via `os.chmod(env_path, 0o600)`, so only the active user can read or write it.
    *   *Windows*: POSIX-style `chmod` bits are not meaningful on NTFS. Instead, Maxume calls `icacls` (via a small subprocess wrapper) on first launch to strip inherited permissions and grant read/write only to the current user SID. This is noted separately because `envsetup.md` targets Windows 10/11 as the primary platform — a POSIX-only permission story would silently do nothing there.

---

## 3. Dynamic API Failover Protocol with Privacy Waivers

If Maxume is shared with others, they may not have a dedicated RTX-series GPU to run local Ollama models. To remain portable on lightweight machines (MacBooks, integrated Intel laptops), Maxume implements an **Opt-In Cloud Failover**:

1.  **Local Ollama Heartbeat Check**: On boot, the sidecar checks `http://localhost:11434`.
2.  **Offline State Trigger**: If Ollama is offline, missing, or times out, Maxume triggers an **Offline Mode State** in the UI.
3.  **Privacy Consent Waiver Dialog**: Instead of crashing, a neon-red modal appears:

    > **⚠️ PRIVACY WAIVER REQUIRED**
    >
    > Maxume could not connect to a local Ollama server. To parse and match your resume, we would need to temporarily route resume parsing through the cloud-based **Gemini API** or **Groq Cloud API**.
    >
    > *While these API providers maintain data agreements and do not persist inputs, your physical resume details will leave your machine.*
    >
    > [ ] **Yes, I understand and consent to cloud routing.**
    > [ ] **No, I want to operate in local-offline mode (Local Project Watcher only).**

4.  **Graceful Fallback**: If consented, the FastAPI scheduler activates cloud fallback pipelines, mapping resume parsing to **Gemini 2.5 Flash-Lite** with minimal rate limits. If declined, all cloud tasks are suspended and the app runs in local static mode. Company signal research is unaffected either way, since it never handles resume PII in the first place.

---

## 4. Scraping & External Fetch Ethics (New)

The company-signal research pipeline (`companyresearch.md`) is the only part of Maxume that fetches arbitrary external web content beyond documented, authorized API endpoints. It follows explicit rules to stay a good citizen of the sites it reads:

1.  **`robots.txt` compliance**: Before fetching a company's own newsroom/blog page directly, the sidecar checks and honors `robots.txt` for that domain. If disallowed, Maxume falls back to Google CSE search-snippet data only and does not fetch the page body.
2.  **No paywall bypass**: If a source requires a login or returns a paywall interstitial, Maxume discards it as a candidate signal rather than attempting to extract text around the paywall.
3.  **Descriptive User-Agent**: All outbound fetches identify as `Maxume/1.0 (personal job-application assistant; local use)` — no user-agent spoofing.
4.  **Timeouts and rate limits**: Each external fetch times out at 8 seconds; the sidecar never fetches more than a handful of pages per application to avoid looking like a scraper to any single target domain.
5.  **No re-publication**: Fetched snippets are used transiently to ground one generated document for personal use; Maxume does not store or redistribute full page content, only the short cited snippet and its source URL in `company_research_signals`.

This is distinct from the Google CSE **employee lookup** (§ below and `architecture.md` §4), which only ever reads Google's own structured JSON search response — it never fetches LinkedIn pages directly, so none of the above applies to that path.
