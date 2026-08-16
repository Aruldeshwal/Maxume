# Code Standards & Architectural Rules: Maxume

## 1. Directory Structure Layout

```
maxume-app/
├── src-tauri/                 # Rust Native Desktop Configuration
│   ├── src/
│   │   └── main.rs            # Tauri main thread (manages sidecar processes & IPC)
│   ├── tauri.conf.json        # Manifest declaring python-sidecar binaries
│   └── Cargo.toml             # Rust package configuration
├── src/                       # Tauri Webview Frontend (React)
│   ├── components/            # Shared UI Widgets (Legion Red & Black Theme)
│   │   ├── ContactCard.tsx    # Scraped LinkedIn Profile Card
│   │   ├── SignalCard.tsx     # Personalization signal / "none found" card
│   │   ├── QuotaRing.tsx      # Quota usage indicator
│   │   └── TerminalLog.tsx    # Live CLI compilation stream logger
│   ├── tabs/                  # Main layout views
│   │   ├── Dashboard.tsx
│   │   ├── ProjectSync.tsx
│   │   └── Optimizer.tsx
│   ├── App.tsx                # Main entry point
│   └── index.css              # Custom Tailwind directives
├── sidecar/                   # Python FastAPI Backend Sidecar
│   ├── app/
│   │   ├── main.py            # FastAPI Application Entrypoint
│   │   ├── database.py        # SQLite Database connection (SQLite SSOT)
│   │   ├── docx_engine.py     # python-docx paragraph style cloner
│   │   ├── company_research.py# Signal discovery, snippet extraction, guard checks
│   │   └── scheduler.py       # Asyncio rate-limit & backoff queue scheduler
│   ├── requirements.txt       # Python dependency layout
│   └── .env                   # Configuration file (API keys and local paths)
└── package.json               # Node.js dependencies (TypeScript, Vite, Tailwind)
```

---

## 2. Python Sidecar: Asyncio Rate-Limiting Scheduler

To handle burst requests across multi-provider endpoints (Google Custom Search, Groq, Gemini) and prevent lockout from `429 Too Many Requests`, the sidecar implements an asynchronous, prioritized **Token-Bucket Rate Limiter**.

```python
import asyncio
import time
from typing import Dict, Any, Callable, Coroutine
import logging

class APIRateLimiter:
    def __init__(self, requests_per_minute: int, max_tokens: int):
        self.rate = requests_per_minute / 60.0  # Tokens added per second
        self.capacity = max_tokens
        self.tokens = max_tokens
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()

    async def consume(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.last_refill = now

            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

            if self.tokens < 1.0:
                sleep_duration = (1.0 - self.tokens) / self.rate
                logging.info(f"[Limiter] Rate threshold hit. Sleeping {sleep_duration:.2f}s...")
                await asyncio.sleep(sleep_duration)
                self.tokens = 0.0
            else:
                self.tokens -= 1.0

class TokenAwareScheduler:
    def __init__(self):
        self.limiters = {
            "gemini": APIRateLimiter(requests_per_minute=15, max_tokens=15),
            "groq": APIRateLimiter(requests_per_minute=30, max_tokens=30),
            "google_cse": APIRateLimiter(requests_per_minute=10, max_tokens=10),
        }

    async def execute_task(self, provider: str, task: Callable[[], Coroutine[Any, Any, Any]], max_retries: int = 3) -> Any:
        limiter = self.limiters.get(provider)
        if not limiter:
            return await task()

        retries = 0
        backoff = 2.0

        while retries < max_retries:
            await limiter.consume()
            try:
                return await task()
            except Exception as e:
                if "429" in str(e) or "ResourceExceeded" in str(e):
                    retries += 1
                    sleep_time = backoff ** retries
                    logging.warning(f"[Scheduler] 429 detected for {provider}. Backing off {sleep_time}s...")
                    await asyncio.sleep(sleep_time)
                else:
                    raise e
        raise TimeoutError(f"Task failed after maximum retries under rate limit scheduler for {provider}")
```

Note: `google_cse` is shared between the LinkedIn-employee lookup and the company-signal discovery stage in `company_research.py` — both draw from the same 100/day budget, so the scheduler treats them as one provider, not two.

---

## 3. Frontend & Sidecar Contract Rules

*   **Tauri Command Isolation**: The React frontend must never execute direct HTTP calls to Gemini, Groq, or Google APIs. All networking, folder watching, and database reads are initiated as Tauri Sidecar requests, keeping API key handling contained on the Python side.
*   **JSON API Interface**: The FastAPI sidecar exposes local endpoints over localhost. Tauri communicates with the sidecar using strong TypeScript typing.
*   **IPC Communication Guard**: Long-running operations (syncing `/projects`, generating resume packs, running company research) must use Server-Sent Events (SSE) or WebSockets to stream log output back to Tauri's terminal view in real time, preventing UI freezes.

---

## 4. `company_research.py` Module Contract

*   Exposes a single primary function, `research_company(company_name: str, company_url: str | None) -> ResearchBrief`, returning the structured type defined in `apicontracts.md` §5.
*   Never raises on "nothing found" — that is a valid, expected return value (`ResearchBrief.status == "NO_SIGNALS_FOUND"`), not an exception path.
*   Network fetches (beyond the Google CSE call) must set a descriptive `User-Agent`, respect `robots.txt`, and time out after 8 seconds per source — a slow company blog should never block the rest of the pipeline. See `security.md` §4 for the full scraping-ethics policy.
*   The post-hoc containment check (hallucination guard Stage D, see `companyresearch.md` §4) is implemented as plain string/keyword matching in this module — deliberately not another LLM call, to keep it fast, deterministic, and free of its own hallucination risk.

---

## 5. General Code Quality Rules

*   Python: type-hint all public function signatures; run `ruff` for linting and `black` for formatting before every commit.
*   TypeScript: `strict` mode on; no `any` in component props.
*   No secrets, tokens, or `.env` contents in code comments, log statements, or committed fixtures — see `security.md` §2.
*   Every new sidecar endpoint gets at least one corresponding test in `sidecar/tests/` before it is considered done — see `testing.md`.
