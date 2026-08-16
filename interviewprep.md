# SDE Interview Preparation Guide: Presenting Maxume

If you are interviewing for Software Engineering (SDE) or Systems Architecture roles, **Maxume** is an exceptional portfolio project. It demonstrates your ability to design robust hybrid systems, optimize local hardware, handle API limits, build high-quality desktop applications, and reason carefully about LLM reliability rather than just LLM capability.

This guide compiles high-impact technical questions and answers to help you explain Maxume's design to engineering managers and technical interviewers.

---

## 1. System Architecture & Hybrid Design

### Q: Why did you choose a hybrid cloud-local architecture instead of running everything locally or in the cloud?
*   **The Pitch**: *"I designed Maxume around a **data-classification and hardware-containment strategy**.
    1.  **Privacy & PII**: A user's master resume contains sensitive PII — physical address, phone number, personal history. Sending this to external cloud models is a privacy risk, so I isolated that stage to run completely locally on Ollama running Qwen 2.5 7B Instruct.
    2.  **Context & Cost**: Processing high-context corporate career pages or OCR on 4K screenshots locally would strain consumer hardware. I routed these non-PII, high-context tasks to Google Gemini's free Developer API.
    3.  **Speed**: For creative drafting, I used Groq's fast LPU endpoints. This multi-provider orchestration keeps operating cost at $0/month while guaranteeing privacy and UI snappiness."*

### Q: Explain the sidecar pattern between Tauri v2 and the Python backend.
*   **The Pitch**: *"Electron-style desktop wrappers are notorious for bloating RAM and consuming GPU VRAM. Since my app targets a local GPU budget under 5.5GB VRAM for local inference, I needed a lightweight client. Tauri v2 compiles to native Rust OS webviews, consuming ~40MB RAM and effectively 0MB GPU VRAM, freeing all available hardware for model inference. I packaged a compiled Python FastAPI sidecar via PyInstaller for file-system watching, XML document manipulation (`python-docx`), and database operations, with Tauri managing the sidecar's lifecycle over local IPC."*

---

## 2. Hardware Constraints & VRAM Engineering

### Q: You ran a 7B model on a 6GB laptop GPU. How did you prevent CUDA OOM errors?
*   **The Pitch**: *"An RTX 3060 Laptop has a 6GB VRAM ceiling; background display processes consume ~500–800MB, leaving roughly 5.2–5.5GB for the application. The Qwen 2.5 7B Instruct model in Q4_K_M quantization loads to about 4.7–4.8GB including runtime overhead — that's the number that actually has to fit the budget, not the raw 4.4GB file size alone. On top of that, KV cache memory scales linearly with context length, so I enforced three constraints:
    1.  **Context Capping**: Locked `num_ctx` to 2048 tokens, keeping KV cache under ~300MB and total VRAM around 5.0–5.1GB — comfortably inside budget.
    2.  **Flash Attention**: Enabled `OLLAMA_FLASH_ATTENTION=1` to optimize memory access.
    3.  **Concurrency Locking**: An asyncio semaphore restricts local model execution to a sequential queue, preventing parallel requests from doubling VRAM and crashing the driver."*
*   *A good follow-up if asked "how did you catch that the numbers didn't add up"*: an earlier version of my design doc actually had a base-load figure that exceeded my stated budget — I caught it doing a reconciliation pass across docs, which is its own small lesson about treating your own architecture docs with the same scrutiny as your code.

---

## 3. Scraping, Search APIs, and Grounding LLM Output in Fact

### Q: LinkedIn aggressively bans scrapers. How did you get employee contact data without that risk?
*   **The Pitch**: *"Directly scraping LinkedIn with headless browsers requires active session cookies and risks a permanent account ban. Instead I built a **Google Search API loophole**: a free Programmable Search Engine scoped to `site:linkedin.com/in/*`, queried through Google's Custom Search JSON API. The structured response gives me public name, headline, and profile URL directly from Google's index — zero login, zero ban risk, zero cost."*

### Q: You added a feature to personalize outreach with real company news. How did you stop the model from just making something up?
*   **The Pitch**: *"That was actually the most interesting reliability problem in the whole project, harder than the VRAM constraints. An LLM asked to 'mention something recent about the company' will, if unconstrained, sometimes produce a plausible but fabricated detail — and here the cost of being wrong is high, because it goes straight into an email a real recruiter reads.
    I built a **three-layer hallucination guard** instead of trusting prompt engineering alone:
    1.  A hard **recency filter** — anything older than 90 days never even reaches the summarizer.
    2.  A **grounded, temperature-0.0 prompt** that gives the model only the raw source snippets and explicitly tells it to say `NO_SIGNALS_FOUND` itself if it can't support a claim.
    3.  A **deterministic, non-LLM containment check** — plain keyword/entity matching that verifies the model's summary actually appears in the source text it was given, and drops anything that doesn't.
    If every candidate signal fails, the pipeline falls back to `NO_SIGNALS_FOUND`, and the UI shows that plainly rather than hiding it — a clean 'nothing found' is a far better user outcome than a confident wrong fact."*
*   **Good follow-up if pressed "why not just use a second LLM call to fact-check the first"**: *"I considered that, but it just moves the hallucination risk up one level — the fact-checking model can itself hallucinate a 'yes this is grounded' verdict, and it doubles API cost per research pass for something a plain string-containment function does more reliably and for free."*

---

## 4. Document Engineering & State Consistency

### Q: How did you handle resume manipulation using python-docx without breaking formatting?
*   **The Pitch**: *"Word documents use erratic internal XML schemas — a string like `{{PROJECTS}}` often gets fragmented across multiple XML runs, so naive text-swapping regularly corrupts formatting. I built a **Paragraph-Level Rebuilding Engine**: locate the paragraph containing the placeholder tag, extract its style metadata (font, size, line-spacing, margins, indents), programmatically inject new paragraphs immediately preceding it that copy those style characteristics, then delete the placeholder paragraph. This guarantees the final resume compiles cleanly and matches the original layout exactly, regardless of how Word originally fragmented the placeholder text."*
