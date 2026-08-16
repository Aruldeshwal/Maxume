# Environment Setup & Installation Guide: Maxume

This guide walks through setting up the local-first, zero-operating-cost Maxume pipeline on your local laptop.

---

## 1. Laptop Hardware Compatibility Check
*   **Operating System**: Windows 10/11 22H2 (Home or Pro)
*   **Target GPU**: NVIDIA RTX 3060 Laptop (6GB VRAM)
*   **CUDA Toolkit**: CUDA 11.8 or newer (required for hardware-accelerated local inference)
*   **NVIDIA Graphics Driver**: Version 531.00 or higher

---

## 2. Setting Up the Local LLM (Ollama)

1.  **Download Ollama**: Visit [ollama.com](https://ollama.com) and download the Windows installer.
2.  **Install & Start**: Launch the installer. Once complete, a local tray icon confirms the API server is active on `http://localhost:11434`.
3.  **Download the Qwen 2.5 7B Instruct Model**: Open your terminal (PowerShell or Bash) and run:
    ```bash
    ollama pull qwen2.5:7b-instruct
    ```
    *This downloads the `Q4_K_M`-quantized GGUF model (~4.4GB) to `%HOMEPATH%/.ollama/` on disk. The `-instruct` suffix must match `OLLAMA_MODEL_NAME` in `.env` below and the `model` field in `apicontracts.md` §1 — a mismatch here is a common source of silent 404s from the Ollama API.*
4.  **Hardware Optimization Check**: To maximize inference speed and keep the KV cache within your VRAM budget, enable **Flash Attention**:
    *   *Windows PowerShell*:
        ```powershell
        [System.Environment]::SetEnvironmentVariable('OLLAMA_FLASH_ATTENTION', '1', 'User')
        ```
    *   *Linux Bash*:
        ```bash
        export OLLAMA_FLASH_ATTENTION=1
        ```

---

## 3. Creating the Cloud Developer Accounts ($0)

### Step A: Google AI Studio (Gemini Developer Key)
1.  Navigate to [aistudio.google.com](https://aistudio.google.com).
2.  Log in with your Google Account.
3.  Click **Create API Key**.
4.  Copy your key. *Gives 1,000 free requests/day using `gemini-2.5-flash-lite`. This key is shared by JD-OCR, project reranking, and company-signal summarization — all three draw from the same daily quota.*

### Step B: Groq Cloud (Fast LPU Writing Key)
1.  Navigate to [console.groq.com](https://console.groq.com).
2.  Sign up for a free developer account.
3.  Go to **API Keys** and click **Create API Key**.
4.  Copy your key. *Gives 14,400 free daily requests, for compiling cover letters, emails, and referrals.*

### Step C: Google Custom Search Engine Loophole
To enable zero-risk LinkedIn contact lookup **and** company signal discovery (both share this one key + CX pair):
1.  Create a Google Programmable Search Engine at [cse.google.com](https://cse.google.com).
2.  Click **Add**.
3.  Name your search engine. For broadest coverage, configure it to search the entire web rather than restricting to `linkedin.com/in/*` only — the `site:` restriction for employee lookup is applied per-query in code (see `apicontracts.md` §4), not baked into the engine config, since the same engine is reused for company-signal news queries in §5.
4.  Copy the **Search Engine ID (CX)** from the control panel.
5.  Get a free Custom Search JSON API key at [developers.google.com/custom-search/v1/overview](https://developers.google.com/custom-search/v1/overview).
6.  Copy your API key. *Registers 100 free queries/day, shared across both use cases.*

---

## 4. Bootstrapping the Application Codebase

### Frontend Bootstrap (Tauri v2 + Node)
```bash
cd maxume-app
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Python Sidecar Setup (FastAPI Backend)
```bash
cd sidecar
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install fastapi uvicorn python-docx Pillow requests pydantic python-dotenv beautifulsoup4 --break-system-packages
```
*Note: `sqlite3` is part of the Python standard library and is never installed via pip — an earlier draft of this guide incorrectly listed `SQLite3` as a pip package; that entry has been removed. `beautifulsoup4` was added for parsing company newsroom/blog pages in the company-research pipeline (`company_research.py`).*

---

## 5. Local Environmental Configuration (.env)

Create a file named `.env` inside `sidecar/`:

```env
# Local Machine Folders Config
MASTER_RESUME_PATH="C:/Users/Legion/Documents/Master_Resume.docx"
PROJECTS_DIR_PATH="C:/Users/Legion/Documents/projects"
OUTPUT_DIR_PATH="C:/Users/Legion/Documents/output"

# Swappable Ollama Settings
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL_NAME="qwen2.5:7b-instruct"
OLLAMA_CONTEXT_LIMIT=2048

# Zero-Cost Developer Keys ($0/Month)
GEMINI_API_KEY="AIzaSyA..."
GROQ_API_KEY="gsk_..."
GOOGLE_CSE_KEY="AIzaSyB..."
GOOGLE_CSE_CX="018274..."

# Company Research / Personalization Tuning (see companyresearch.md)
PERSONALIZATION_ENABLED=true
PERSONALIZATION_RECENCY_DAYS=90
PERSONALIZATION_MAX_SIGNALS=5
```

Now launch the developer workspace:
```bash
npm run tauri dev
```
Maxume's dashboard displays in Legion Red & Black dark mode, primed to optimize your job applications.
