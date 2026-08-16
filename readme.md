# Maxume 🦅
> **Local-First, Airgapped AI Job Application Assistant with Hybrid Cloud Intelligence**

Maxume is a tactical desktop and web application that automates technical resume customization, cover letter synthesis, company signal research, and networking referral outreach. It pairs **local-first privacy and local LLM inference (Ollama)** with **high-speed, zero-cost cloud AI (Groq LPU & Google Gemini Flash)** to produce tailored, recruiter-ready application packs in under 30 seconds.

---

## 🌟 Key Architecture & Capabilities

### 1. Incremental Git Project Watcher & GitHub Profile Sync
* **Automatic Repository Discovery**: Scans local directories or syncs directly with public GitHub profiles (`@Aruldeshwal`).
* **AI Bullet Synthesizer**: Uses **Google's XYZ Formula** (*"Accomplished [X] as measured by [Y], by doing [Z]"*) to generate high-impact, architecture-focused engineering bullet points.
* **Live Demo Extraction**: Automatically extracts live demo links (Vercel, Render, Streamlit, etc.) and embeds them directly into project title hyperlinks.
* **Granular Visibility Control**: Toggle projects between **Active on Resume** and **Hidden from Resume**, or delete test repositories with 1 click.

### 2. Single-Page Paragraph-Level DOCX Engine
* **Native Word OXML Hyperlinks**: Injects clickable hyperlinks with custom HEX styling directly into your master `.docx` template.
* **Brief Tech Stack & Timeline Dates**: Formats project headings with title, tech stack in brief, and exact timeline:
  $$\text{\textbf{Project Title (Live Link)}} \mid \textit{Tech Stack in Brief} \mid \textit{Month Year – Month Year}$$
* **Adaptive Bullet Headroom Filling**: Dynamically expands bullet coverage (3 high-impact bullets per project, or up to 4 for 2 projects) to maximize page density while strictly fitting on **exactly 1 single page**.
* **Clean Metadata Stripping**: Filters out markdown headers, repo URLs, and metadata tags (`GitHub:`, `Language:`, `Tech Stack:`) to ensure only authentic achievements enter your resume.
* **Windows File-Lock Resilience**: Automatically detects if Microsoft Word has the resume file open, saving to a fallback filename without failing the run.

### 3. Authentic Skills Synthesizer (Zero Hallucinations)
* **Codebase-Grounded Extraction**: Scans all 12 verified local/GitHub projects and master template to extract only genuine technical competencies.
* **ATS-Optimized Categories**: Groups skills into *Programming Languages*, *Frameworks & Web*, *Databases & Cloud/DevOps*, and *Core Competencies & AI*.
* **JD Relevance Ranking**: Prioritizes candidate skills requested by the target Job Description at the front of each category without hallucinating unrepresented tech (e.g. Go, Rust).

### 4. Real-Time Company News Wire & 3-Stage Hallucination Guard
* **Real-Time News Wire**: Integrates Google News RSS and live press wires to pull dated news, product launches, and funding rounds from verified Tier 1/Tier 2 publications (*Reuters*, *blog.google*, *TechCrunch*, *CNBC*, etc.).
* **Deterministic Containment Check**: Post-hoc verification algorithm (`passes_containment_check`) validates that every entity, metric, and claim exists in the source text before entering your cover letter.

### 5. Targeted Networking & Referral Outreach Hub
* **Role-Specific Personas**: Synthesizes targeted referral contacts (*Senior Engineers*, *Engineering Managers*, *Technical Recruiters*) with direct LinkedIn search links.
* **75-Word Referral Pitches**: Generates personalized, concise outreach messages ready to copy and send with a single click.

### 6. Seamless Multi-Screenshot & Clipboard OCR (`Ctrl+V`)
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
| **Document Processing** | `python-docx`, Word OXML Manipulation, Pillow |
| **Local LLM** | Ollama (`qwen2.5:7b-instruct`) with dynamic VRAM guardrails |
| **Cloud AI ($0/mo)** | Groq LPU (`llama-3.3-70b-versatile`), Google Gemini (`gemini-2.5-flash`) |
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

### 3. Step 1: Start the Python Backend Engine
In a dedicated terminal, activate the Python virtual environment and launch FastAPI:

```powershell
# Navigate to sidecar
cd sidecar

# Create and activate virtual environment (first time only)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements (first time only)
pip install -r requirements.txt

# Start FastAPI Sidecar (runs on http://127.0.0.1:8000)
python app/main.py
```

---

### 4. Step 2: Choose Your Frontend Mode

#### Mode A: Run in Web Browser (Fastest Development Mode) 🌐
In a second terminal:
```powershell
# In project root directory
npm install      # (first time only)
npm run dev
```
Open **[http://localhost:1420](http://localhost:1420)** in Google Chrome, Edge, or Brave.

---

#### Mode B: Run Native Windows Desktop App (Development Mode) 🖥️
In a second terminal:
```powershell
# In project root directory
npm run tauri dev
```
*(This opens the native Maxume Windows desktop window with hardware acceleration and live reload).*

---

#### Mode C: Install Standalone Windows Desktop App (.exe / .msi) 📦
Run the production installer generated by Tauri:
```powershell
# Double-click the Windows NSIS Setup executable:
src-tauri/target/release/bundle/nsis/Maxume_0.1.0_x64-setup.exe

# Or the Windows MSI installer:
src-tauri/target/release/bundle/msi/Maxume_0.1.0_x64_en-US.msi
```
* Once installed, launch **Maxume** from your Windows **Start Menu** or **Desktop Shortcut**.
* Keep the Python sidecar running (`python sidecar/app/main.py`) in the background.

---

### 5. Building Standalone Windows Packages from Source
To compile and bundle fresh Windows binaries and installers:

```powershell
npm run tauri build
```
Compiled outputs will be located in:
* `src-tauri/target/release/bundle/nsis/Maxume_0.1.0_x64-setup.exe`
* `src-tauri/target/release/bundle/msi/Maxume_0.1.0_x64_en-US.msi`
* `src-tauri/target/release/maxume.exe` (Standalone portable executable)

---

### 6. Running Automated Tests
Maxume includes a 100% automated test suite across backend Python and frontend Vitest:

```powershell
# Run backend Python tests (37 tests)
.\sidecar\venv\Scripts\pytest.exe sidecar/tests/

# Run frontend React tests (7 tests)
npm run test

# Run all tests together
.\sidecar\venv\Scripts\pytest.exe sidecar/tests/; npm run test
```

---

## 🎯 End-to-End Application Workflow

1. **`[P] Projects Sync`**:
   - Enter your GitHub username (`@Aruldeshwal`) and click **"Sync GitHub Repositories"**.
   - The engine discovers all 12 repositories, extracts live demo links, generates XYZ formula engineering bullets, and displays active/hidden toggles.
2. **`[A] Apply & Optimize`**:
   - Enter Company Name (`Google`, `Microsoft`, etc.) and Role Title (`Software Engineer`).
   - Paste Job Description text, or press **`Ctrl+V`** to paste screenshots directly from your clipboard (`Win + Shift + S`).
   - Click **"Compile & Optimize Resume Pack"**.
3. **Inspect Output**:
   - View the generated **Single-Page Word Resume (`.docx`)** with active hyperlinks, tech stacks, and timelines.
   - Read the tailored **Cover Letter**, **Outreach Email**, and **Verified Company Signals**.
   - Review **Targeted LinkedIn Referral Personas** and copy custom 75-word referral outreach pitches.
   - Click **"Open Output Folder"** to open the generated application pack directly in Windows File Explorer.

---

## 📁 Repository Structure

```
Maxume/
├── sidecar/                   # Python FastAPI Backend Engine
│   ├── app/
│   │   ├── main.py            # REST Endpoints & Orchestration
│   │   ├── database.py        # SQLite SSOT & Thread-Safe Transactions
│   │   ├── docx_engine.py     # OXML Hyperlink & Paragraph DOCX Rebuilder
│   │   ├── github_sync.py     # GitHub Profile Sync & AI XYZ Bullet Synthesizer
│   │   ├── skills_engine.py   # Code-Grounded Candidate Skills Categorizer
│   │   ├── company_research.py# Real-Time News Wire & Hallucination Guard
│   │   ├── employee_lookup.py # Targeted LinkedIn Networking Personas
│   │   ├── groq_service.py    # High-Speed Creative Copy Generation
│   │   ├── gemini_service.py  # Multi-Screenshot Multimodal OCR & Project Reranking
│   │   ├── scheduler.py       # Token-Bucket Rate Limiter & Backoff
│   │   └── image_optimizer.py # Pillow Grayscale Image Compressor
│   └── tests/                 # Comprehensive Backend Pytest Suite
├── src-tauri/                 # Tauri v2 Desktop Engine & Rust Configuration
│   ├── src/                   # lib.rs and main.rs desktop entrypoints
│   ├── icons/                 # Multi-resolution Windows application icons
│   └── tauri.conf.json        # Tauri v2 Desktop & Bundling Manifest
├── src/                       # React 18 + TypeScript Frontend
│   ├── components/            # Reusable UI (QuotaRing, SignalCard, ContactCard, etc.)
│   ├── tabs/                  # Main Views (Dashboard, ProjectSync, Optimizer, HistoryLogs)
│   └── App.tsx                # Persistent Tab Navigation & Live Telemetry
├── Master_Resume.docx         # Master Resume Template (Contains {{PROJECTS}} & {{SKILLS}})
└── package.json               # Frontend Tooling & Scripts
```

---

## 🔒 Security & Privacy
* **Airgapped Storage**: Master resumes, local source code, and generated application packs remain stored 100% locally on your file system.
* **$0/Month Operating Cost**: Built entirely on generous free developer tiers (Groq 14.4k req/day, Gemini 1000 req/day, Ollama Local).
* **Strict Containment Check**: Prevents fabricated AI claims from reaching prospective employers.

---

## 📄 License
MIT License. Created by [Arul Deshwal](https://github.com/Aruldeshwal).
