# Environment Setup & Configuration Guide

## 1. Environment Files
Maxume uses local environment variables in `sidecar/.env` and `.env`.

### Complete `.env` Specification:

```ini
# --- Local Machine File Paths ---
MASTER_RESUME_PATH="../Master_Resume.docx"
PROJECTS_DIR_PATH="C:\\Users\\aruld\\OneDrive\\Desktop\\Git-Projects-Sync"
OUTPUT_DIR_PATH="C:\\Users\\aruld\\OneDrive\\Desktop\\Job-Content"

# --- Local Ollama Inference Engine ---
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL_NAME="qwen2.5:7b-instruct"
OLLAMA_CONTEXT_LIMIT=2048

# --- Zero-Cost Cloud AI Keys ($0/Month) ---
GEMINI_API_KEY="your_google_gemini_api_key_here"
GROQ_API_KEY="your_groq_api_key_here"

# --- Company Research & Personalization ---
PERSONALIZATION_ENABLED=true
PERSONALIZATION_RECENCY_DAYS=90
PERSONALIZATION_MAX_SIGNALS=5
```

---

## 2. API Key Acquisition (100% Free Tiers)

### A. Groq Cloud API Key (Free)
1. Sign up at [https://console.groq.com](https://console.groq.com).
2. Go to **API Keys** ➔ Click **Create API Key**.
3. Copy key (`gsk_...`) and paste as `GROQ_API_KEY`.
* *Free Tier Allowance*: 14,400 requests/day running `llama-3.3-70b-versatile`.

### B. Google Gemini API Key (Free)
1. Sign up at [https://aistudio.google.com](https://aistudio.google.com).
2. Click **Get API Key** ➔ **Create API Key**.
3. Copy key and paste as `GEMINI_API_KEY`.
* *Free Tier Allowance*: 1,000 requests/day running `gemini-2.5-flash` for multimodal OCR and reranking.

---

## 3. Local Engine Setup (Ollama)
1. Download Ollama from [https://ollama.com](https://ollama.com).
2. Pull the recommended high-performance instruct model:
   ```powershell
   ollama pull qwen2.5:7b-instruct
   ```
3. Start the Ollama daemon:
   ```powershell
   ollama serve
   ```
