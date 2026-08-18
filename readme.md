# Maxume 🦅
> **Local-First, Airgapped AI Job Application Assistant with Grounded Hybrid Intelligence**

Maxume is a tactical desktop and web application that automates technical resume customization, single-page DOCX compilation, authentic skills extraction, dynamic project matching via Maximal Marginal Relevance (MMR), company signal research, verified employee networking, real-time daily quota tracking, and corporate email discovery. It pairs **local-first privacy and local LLM inference (Ollama)** with **high-speed, zero-cost cloud AI (Groq LPU & Google Gemini Flash)** to produce tailored, recruiter-ready application packs in under 30 seconds.

---

## 🌟 Key Architecture & Capabilities

### 1. Incremental Git Project Watcher & GitHub Profile Sync
* **Automatic Repository Discovery**: Scans local directories or syncs directly with public GitHub profiles (`@Aruldeshwal`).
* **Incremental Commit-Hash Sync**: Compares GitHub `pushed_at` timestamps against your local SQLite database in ~0.5s. Skips unchanged repositories, avoids rate limits, and **preserves custom in-app edits**.
* **Force Full Re-Sync Option**: Re-analyzes all 13 repositories from GitHub from scratch with a single click (`[Force Full]`).
* **Multi-Manifest Tech Stack Extractor**: Inspects remote `package.json`, `requirements.txt`, `Cargo.toml`, and GitHub Languages API to detect complete, multi-ecosystem technical stacks (e.g. `Tauri v2`, `FastAPI`, `React`, `Prisma`, `Socket.io`).
* **Realistic Timeline Calculator**: Computes authentic 1–3 month development sprint windows based on repository creation and commit milestones (e.g. `Oct 2025 – Nov 2025`), eliminating generic `2024 – Present` placeholders.
* **Grounded Hybrid AI Bullet Synthesizer**: Focuses on **actual system design, concurrency safety, atomic database transactions, room multiplexing, and protocol mechanisms** without inventing fake percentages or artificial traffic loads.
* **In-App Project Details Editor**: Edit any project's **Tech Stack**, **Timeline**, **Live Demo Link**, or **Bullet Points** directly in the UI with instant SQLite SSOT synchronization.
* **Granular Visibility Control**: Toggle projects between **Active on Resume** and **Hidden from Resume**, or delete test repositories with 1 click.

### 2. Maximal Marginal Relevance (MMR) & Skill-Cluster Project Matcher
* **Zero Stack Redundancy**: Projects are selected sequentially using MMR to maximize **unique skill-cluster coverage** against the target Job Description.
* **Bounded by Employer Scope (Zero Out-of-Scope Injections)**:
  - *Pure MERN Stack Roles* $\rightarrow$ Evaluates only requested skills, guaranteeing 100% MERN projects (`Book-IT`, `SlotSwap`, `Productivity-Overload`) with **zero out-of-scope Python/ML injected**.
  - *Hybrid Roles (e.g. MERN + Python/FastAPI)* $\rightarrow$ Surfaces the best project from each requested domain (`Metro-Connect`, `Maxume`, `EzNotes`) providing 100% JD coverage.
  - *Machine Learning Roles* $\rightarrow$ Selects `sentiment-analysis-app` and `Maxume`.

### 3. Single-Page Paragraph-Level DOCX Engine
* **Native Word OXML Hyperlinks**: Injects clickable hyperlinks with custom HEX styling directly into your master `.docx` template.
* **Brief Tech Stack & Timeline Dates**: Formats project headings with title, tech stack in brief, and exact timeline:
  $$\text{\textbf{Project Title (Live Link)}} \mid \textit{Tech Stack in Brief} \mid \textit{Month Year – Month Year}$$
* **Adaptive Bullet Headroom Filling**: Dynamically expands bullet coverage (3 high-impact bullets per project, or up to 4 for 2 projects) with calibrated paragraph line-spacing to maximize page density while strictly fitting on **exactly 1 single page**.
* **Clean Metadata Stripping**: Filters out markdown headers, repo URLs, and metadata tags (`GitHub:`, `Language:`, `Tech Stack:`) to ensure only authentic achievements enter your resume.
* **Windows File-Lock Resilience**: Automatically detects if Microsoft Word has the resume file open, saving to a fallback filename without failing the run.

### 4. Real-Time Daily Quota Tracking Dashboard
* **SQLite Persistence**: Automatically tracks daily API calls in `api_quotas` table in local SQLite DB.
* **Real-Time UI Rings**: Polls `GET /api/quotas` every 3 seconds to update the `0/1000 req` (Gemini) and `0/14400 req` (Groq) rings live on the dashboard.

### 5. Authentic Skills Synthesizer (Zero Hallucinations)
* **Codebase-Grounded Extraction**: Scans all 12 verified local/GitHub projects and master template to extract only genuine technical competencies.
* **ATS-Optimized Categories**: Groups skills into *Programming Languages*, *Frameworks & Web*, *Databases & Cloud/DevOps*, and *Core Competencies & AI*.
* **JD Relevance Ranking**: Prioritizes candidate skills requested by the target Job Description at the front of each category without hallucinating unrepresented tech (e.g. Go, Rust).

### 6. Real-Time Company News Wire & 3-Stage Hallucination Guard
* **Real-Time News Wire**: Integrates Google News RSS and live press wires to pull dated news, product launches, and funding rounds from verified Tier 1/Tier 2 publications (*Reuters*, *blog.google*, *TechCrunch*, *CNBC*, etc.).
* **Deterministic Containment Check**: Post-hoc verification algorithm (`passes_containment_check`) validates that every entity, metric, and claim exists in the source text before entering your cover letter.

### 7. Targeted Real Employee Networking & Hunter.io Email Engine
* **Zero-Placeholder Discovery**: Queries public search streams specifically for real named individuals with exact personal `/in/` LinkedIn profiles (no generic search filler).
* **Live DNS MX Deliverability Verification**: Validates company mail servers via Google DNS-over-HTTPS, identifying providers (*Zoho Mail*, *Google Workspace*, *Microsoft 365*).
* **Hunter.io Corporate Email Permutations**: Generates standard corporate email variations (`first.last@company.com`, `first@company.com`, `f_initial.last@company.com`) with 1-click copy and pre-filled `mailto:` compose triggers.
* **Multi-Channel Contact Action Bar**: Provides direct Google Contact Dork, GitHub User Search, and Twitter/X lookup buttons to bypass LinkedIn connection gates.
* **75-Word Referral Pitches**: Generates personalized, concise outreach messages ready to copy and send with a single click.

### 8. Seamless Multi-Screenshot & Clipboard OCR (`Ctrl+V`)
* **Instant Clipboard Pasting**: Press `Ctrl+V` anywhere in the Optimizer tab to paste job description screenshots directly from your clipboard (e.g. `Win + Shift + S`).
* **Multi-Screenshot Carousel**: Upload and inspect multiple screenshot parts with live thumbnail previews and individual removal.
* **Pillow Grayscale Compression**: Compresses images below 300KB before dispatching to Gemini Multimodal OCR.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend UI** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons |
| **Desktop Shell** | Tauri v2 (Rust) |
| **Backend Sidecar** | Python 3.13, FastAPI, Uvicorn, SQLite3 |
| **Project Matching** | Maximal Marginal Relevance (MMR), Skill-Cluster Engine |
| **Document Processing** | `python-docx`, Word OXML Manipulation, Pillow |
| **Local LLM** | Ollama (`qwen2.5:7b-instruct`) with dynamic VRAM guardrails |
| **Cloud AI ($0/mo)** | Groq LPU (`qwen/qwen3.6-27b`, `openai/gpt-oss-120b`), Google Gemini (`gemini-3-flash-preview`) |
| **Testing** | Pytest, Vitest, AnyIO, Asyncio |

---

## 🚀 Complete Running & Installation Guide

### 1. Prerequisites
Ensure the following tools are installed on your machine:
* **Node.js** (v18 or higher) — [Download Node.js](https://nodejs.org)
* **Python** (v3.10 to v3.13) with `pip` and `venv` — [Download Python](https://python.org)
* **Rust & Cargo** *(Required only for building or developing the Tauri desktop shell)* — [Install Rust](https://rustup.rs)
* *(Optional)* **Ollama** for airgapped offline local LLM inference — [Download Ollama](https://ollama.com)

---

### 2. Environment Configuration
Create a `.env` file in `sidecar/.env` (or copy from `sidecar/.env.example`):

```ini
# --- Zero-Cost Cloud AI Keys ($0/Month) ---
GEMINI_API_KEY="your_google_gemini_api_key"
GROQ_API_KEY="your_groq_cloud_api_key"

# --- Machine Paths ---
MASTER_RESUME_PATH="../Master_Resume.docx"
PROJECTS_DIR_PATH="C:\\Users\\aruld\\OneDrive\\Desktop\\Git-Projects-Sync"
OUTPUT_DIR_PATH="C:\\Users\\aruld\\OneDrive\\Desktop\\Job-Content"

# --- Local Ollama (Optional) ---
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL_NAME="qwen2.5:7b-instruct"
```

> **Where to get free API keys:**
> * **Groq API Key (Free, 14.4k req/day)**: [https://console.groq.com/keys](https://console.groq.com/keys)
> * **Gemini API Key (Free, 1000 req/day)**: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

### 3. Running in Development Mode

#### Option A: Web Development Server
1. **Start Python Sidecar Backend**:
   ```bash
   cd sidecar
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
2. **Start Vite React Frontend**:
   ```bash
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

#### Option B: Full Tauri Desktop Application
```bash
npm run tauri dev
```

---

### 4. Building the Production Windows Installer (`.exe` & `.msi`)
```bash
# 1. Package Python Sidecar
cd sidecar
.\venv\Scripts\python.exe build_sidecar.py
cd ..

# 2. Build Tauri Desktop Installer
npm run tauri build
```
The generated installer `.exe` and `.msi` packages will be placed in:
```
src-tauri/target/release/bundle/nsis/Maxume_0.1.0_x64-setup.exe
src-tauri/target/release/bundle/msi/Maxume_0.1.0_x64_en-US.msi
```
