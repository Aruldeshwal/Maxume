# User Interface (UI) Design Specification: Maxume

## 1. Visual Theme & Style Guide

Maxume features a sleek, high-contrast dark mode aesthetic inspired by the **Lenovo Legion Gaming Rig** family. The design is clean, tactical, and functional, using crisp typography and sharp neon-red indicators for application status and AI pipeline state.

### Palette Scheme
*   **Primary Background**: Deep Obsidian Black (`#080808` / `#0C0C0C`)
*   **Secondary/Card Background**: Brushed Charcoal Matte (`#121212` / `#1E1E1E`)
*   **Primary Accent/Highlights**: Crimson Core Red (`#E11D48` / `#BE123C`)
*   **Glowing/Status Accents**: Neon Cyber-Red (`#FF003C`)
*   **Primary Text**: High-Contrast Off-White (`#F5F5F5`)
*   **Secondary Text**: Slate-Grey (`#A3A3A3` / `#737373`)
*   **System Borders**: Dark Charcoal Outlines (`#2D2D2D` / `#3F3F46`)
*   **Neutral/Informational Accent**: Muted Slate-Blue (`#64748B`) — reserved for non-alarming status notices, such as "no personalization signal found," so it isn't mistaken for an error state.

### Typography
*   *Headers & Titles*: Sharp, modern geometric sans-serif (JetBrains Mono, Inter, or System Segoe UI Bold).
*   *Body Copy*: Highly readable, clean modern sans-serif (Inter, Roboto, or system fonts).

---

## 2. Global Layout & Dashboard Structure

The desktop interface uses a **Flexible Single-Page Dashboard** powered by Tauri and React, divided into three vertical sections:

```
+---------------------------------------------------------------------------------------+
| [M] Maxume        (Status: Ollama Qwen 2.5 7B [Online] | Free Tier Quotas [100%])     |
+---------------------+---------------------------------------------+-------------------+
|  Navigation         |              Main Display Workspace         |    Networking     |
|                     |                                             |    Referral       |
|  [H] Home           |  Target Application Hub                     |    Drawer         |
|  [P] Projects Sync  |  +---------------------------------------+  |                   |
|  [A] Apply & Parse  |  | Drag & Drop JD Screen / Input Text    |  |  [Personalization]|
|  [L] History Logs   |  +---------------------------------------+  |  Signal found: 2  |
|  [S] Settings       |                                             |  or "None found"  |
|                     |  Job Link: [ https://company.com/careers/ ] |                   |
|                     |                                             |  [Name]           |
|                     |  [COMPILE & OPTIMIZE RESUME] (Button)       |  SDE at Amazon    |
|                     |                                             |  [Headline]       |
|                     |  Generated Outputs:                         |                   |
|                     |  [Resume.docx]  [CoverLetter.txt]  [Email]  |  [Copy Referral]  |
+---------------------+---------------------------------------------+-------------------+
```

---

## 3. Core Tab-By-Tab Blueprint

### Tab A: Home / Master Dashboard
*   **Quick Analytics Widgets**:
    *   *System Status Indicator*: Local Ollama status (model loaded, current VRAM allocation, e.g. "4.9GB/5.2GB used").
    *   *Free Quota Tracker*: Circular neon-red progress rings for Gemini API (1,000/day), Groq API (14,400/day), and Google CSE (100/day).
    *   *Total Applications Compiled*: Count of folders generated inside `/output`.
*   **Core Call-to-Action**: Large glowing crimson button: *"Start New Job Optimization"*.

### Tab B: Project Synchronizer (The SSOT Manager)
*   **Folder Mapping Configuration**: Text inputs to bind `/projects` to your local folder.
*   **Repository Metadata Panel**: Git connection state (e.g. "Git Repo Detected", "Active Branch: main", "Current Commit: `a8b27c...`").
*   **Project Incremental List**: A tabular grid of detected subdirectories:

    | Project Directory | Last Sync Hash | Status | Summary Markdown File |
    |---|---|---|---|
    | `ecommerce_api` | `e98a12` | Up to Date | `ecommerce_api_summary.md` |
    | `kv_store_db` | `7d3c01` | *Modified* | *Needs Sync* |

*   **Manual Override controls**: A primary button to force-sync and override summaries, using local Ollama `qwen2.5:7b-instruct` or cloud fallback.

### Tab C: Application Optimizer (The Engine Room)
*   **Dual Input Area**:
    *   *Left Box*: Text area for pasting job descriptions; also supports dragging and dropping JD screenshots.
    *   *Right Box*: URL field for job links or company websites.
*   **Advanced Parameter Slider**: Configurable sliders for tuning LLM outputs:
    *   *Local Model*: Dropdown of locally detected Ollama GGUF files.
    *   *Context Capping Slider*: Sets `num_ctx` from 1024 to 4096 tokens (default locked to **2048** for VRAM defense).
    *   *Personalization Toggle*: On by default; a per-application switch to skip company signal research entirely (saves CSE/Gemini quota when the user already knows there won't be anything to find).
*   **The Processor Action State**: On clicking "Optimize Asset Pack", the UI transitions into a tactical terminal logger, printing execution phases:
    1.  `[Sidecar] Compressing Screenshot & Executing Gemini OCR...`
    2.  `[Local DB] Performing Semantic Project Similarity Retrieval...`
    3.  `[Research] Searching for recent company signals...`
    4.  `[Research] 2 signals found and verified` *(or)* `[Research] No qualifying signals in the last 90 days`
    5.  `[Ollama] Swapping Resume Section {{PROJECTS}} & {{SKILLS}}...`
    6.  `[Google CSE] Querying public profile employees for Amazon...`
    7.  `[Completed] Pack successfully written to /output/amazon/`
*   **Output Explorer Grid**: Cards displaying file items in `/output/[company_name]`, with quick-action buttons to open the folder locally or copy email/cover letter text to the clipboard.

### Tab D: Networking & Referrals Hub (Right Sliding Panel)
*   Whenever a job compilation completes, a right-hand panel slides open.
*   **Personalization Brief Card** (new, sits above the contact cards):
    *   If signals were found: up to 3 compact cards, each with a one-line headline, source domain, and publish date, linking out to the original source.
    *   If none were found: a single muted-slate notice card, not styled as an error — *"No recent public signal found for [Company]. Your letter was written on your background and the role alone."*
*   **Employee Contact Cards**: Profile details extracted from Google Custom Search API:
    *   *Avatar Placeholder* (default grey-shaded profile icon).
    *   *Name* (publicly indexed string).
    *   *Tagline/Headline* (e.g. "SDE-II at AWS | Golang | distributed systems").
    *   *Profile URL*: clickable text hyperlink opening in the system default browser.
*   **The Generate Referral Button**: Opens a small overlay inside the drawer. Selecting the targeted person generates a personalized referral pitch based on their title and your resume (and the personalization brief, if populated).
*   **Copy & Paste Widget**: A prominent, glowing red button copying the compiled message to the clipboard with a temporary checkmark indicator: `"Referral Copied!"`.
