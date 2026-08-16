# Technical Risk Assessment: VRAM, API Limits & Personalization Integrity

## 1. Local VRAM Containment (RTX 3060 Laptop 6GB)

The RTX 3060 Mobile has **6GB of physical VRAM**. Background display and OS processes typically consume 500MB–800MB, leaving a **~5.2–5.5GB working budget** for local inference.

### The Linear KV Cache Trap
Qwen 2.5 7B Instruct's `Q4_K_M` GGUF file is **~4.4GB on disk**. On load, Ollama's runtime overhead brings baseline VRAM use to roughly **4.7–4.8GB** — this is the figure that must be reconciled against the working budget, not the base file size alone.

Because attention KV cache memory scales linearly with input/output length, long-context queries swell the footprint further:

$$\text{KV Cache Footprint} \approx \text{Total Tokens} \times 0.15\text{MB (Qwen 7B, FP16 attention)}$$

*   *At 2K context (Maxume's default)*: KV cache adds ~300MB, bringing total VRAM to **~5.0–5.1GB** — fits inside the 5.2GB budget with a thin but real margin.
*   *At 16K context*: KV cache swells by ~2.4GB, bringing total to **~7.1–7.2GB**. This overflows the 6GB card entirely, forcing Ollama to offload layers to system RAM and dropping speeds from **~60 tok/s to under 8 tok/s**.

```
  Context Window Memory Impact (Qwen 2.5 7B Instruct Q4_K_M)

  [2K Context]  ===> [== Base + runtime: 4.8GB ==][KV Cache: 0.3GB] --> ~5.1GB VRAM (fits, 60 tok/s)

  [16K Context] ===> [== Base + runtime: 4.8GB ==][===== KV Cache: 2.4GB =====] --> ~7.2GB (RAM spill, 8 tok/s)
```

**Why this matters for the build**: an earlier draft of this document stated a 5.5GB base load against a 5.2GB budget — a number that doesn't fit its own constraint. The corrected figures above (4.8GB base + 0.3GB KV cache at 2K context = ~5.1GB) are the ones the VRAM guardrail math in `architecture.md` §3 should be implemented against.

### Mitigation Actions
1.  **Strict Context Cap**: `num_ctx = 2048` (max `3072`) inside local inference requests.
2.  **Flash Attention Activation**: `OLLAMA_FLASH_ATTENTION=1`.
3.  **Local Model Selection**: Default to efficient 7B/3B GGUF models on 6GB cards; reserve 14B+ for cloud/desktop fallback only.

---

## 2. Local GPU Concurrency Constraints

### The Problem
Consumer GPUs use single-thread CUDA stream designs. Concurrent Ollama calls stack VRAM allocations — two simultaneous project-folder syncs would double requirements to 10+GB and crash the CUDA driver with an OOM error.

### Mitigation Actions
FastAPI enforces strict sequential execution via an asyncio lock:
```python
import asyncio

ollama_lock = asyncio.Lock()

async def run_local_inference(prompt: str):
    async with ollama_lock:
        return await call_ollama_api(prompt)
```
No matter how many directories are tracked or how fast the UI is clicked, local tasks queue and run one at a time.

---

## 3. Cloud API Rate-Limit Mitigation

### The Problem
The zero-cost architecture relies on Gemini (~15 RPM) and Groq (~30 RPM) free-tier limits. A rapid folder-watch sync can burst past these, triggering `429 Too Many Requests` and breaking the workflow.

### Mitigation Actions
*   **Asyncio Token-Bucket Scheduler** (`codestandards.md` §2) routes all third-party API tasks through `TokenAwareScheduler`.
*   **Exponential Retry Backoffs**: on `429`, the scheduler sleeps `2^x` seconds and retries automatically without crashing the desktop app.

---

## 4. Company Signal Research Risk (New)

### Risk A: Scraping Brittleness
Company newsroom/blog page structures change without notice, and some domains actively block automated fetches even when `robots.txt` technically allows them.
*   *Mitigation*: Treat direct-fetch failures as non-fatal — fall back to Google CSE snippet data alone for that source, and if that also fails, fall through to `NO_SIGNALS_FOUND` rather than raising an error that halts the whole application-compile pipeline (`company_research.py` never raises on "nothing found," per `codestandards.md` §4).

### Risk B: Stale or Off-Topic Results
Search results can surface old news that happens to rank well, or content about a similarly-named but different company (a real risk for common company names).
*   *Mitigation*: The hard 90-day recency filter (Stage A) and source-tiering (favoring the company's own domain, `companyresearch.md` §3) reduce both failure modes, though neither is eliminated completely — this residual risk is accepted and is why Stage D's containment check exists as a second, independent layer.

### Risk C: Residual Hallucination Despite Guarding
Even a well-grounded prompt at `temperature: 0.0` can occasionally paraphrase a snippet in a way that subtly changes its meaning (e.g. turning "in talks to raise" into "raised").
*   *Mitigation*: This is precisely what Stage D's deterministic containment check exists to catch — see `decisions.md` ADR 5 for why a non-LLM check was chosen over a second LLM fact-checking pass. This risk is never fully eliminated, only reduced; the milestone gate in `progresstracker.md` (Milestone 4) exists specifically to audit this in aggregate before treating the feature as production-ready.

### Risk D: Quota Contention
Company signal research shares its Google CSE quota with employee lookup (both draw from the same 100/day budget, `codestandards.md` §2 note). A user researching many companies in one session could exhaust the daily quota faster than expected.
*   *Mitigation*: The Personalization Toggle (`ui.md` Tab C) lets a user skip research per-application; the Quota Tracker ring (`ui.md` Tab A) surfaces remaining CSE budget before it's exhausted rather than after.
