# Technical Interview Talking Points & Architecture Highlights

When discussing Maxume in system design, full-stack, and AI engineering interviews, highlight these key architectural decisions and problem-solving examples:

---

## 1. How would you design a local-first, airgapped AI document compiler?
* **Local Privacy vs Cloud Speed**: Master resumes and local source code never leave the user's machine (stored in SQLite3). Stateless tasks (creative copy synthesis, OCR transcription) are offloaded to high-speed zero-cost cloud APIs (Groq, Gemini Flash).
* **Word Document Engineering**: Direct manipulation of Word OXML `<w:hyperlink>` and paragraph formatting in `python-docx` allows programmatically styling active hyperlinks into existing templates without corrupting document formatting or styles.
* **Layout Constraints**: Bounding projects to top 3 and bullets to 2 each with explicit point-level paragraph metrics (`space_before=0`, `space_after=1.5pt`, `line_spacing=1.05`) guarantees single-page ATS compliance.

---

## 2. How do you prevent LLMs from hallucinating in high-stakes workflows?
* **Deterministic Containment Algorithm**: We do not rely on prompt engineering alone. A post-hoc deterministic containment check (`passes_containment_check`) extracts all named entities, numbers, percentages, and currencies from the generated claim and ensures they exist verbatim in the scraped source text before persisting or injecting the signal.
* **Codebase-Grounded Skills Synthesis**: Instead of asking an LLM to invent skills, `skills_engine.py` builds an exact evidence corpus from the candidate's actual local Git repositories and master resume, whitelisting only genuine technologies and sorting them by target JD relevance.

---

## 3. How do you handle cloud API rate limits and resilience in production?
* **Token-Bucket Scheduler**: Implemented `TokenAwareScheduler` with a token-bucket algorithm enforcing strict requests-per-minute (RPM) limits across providers.
* **Cascaded Multi-Tier Failover**:
  - LLM Generation: Local Ollama (`qwen2.5:7b-instruct`) ➔ Groq (`llama-3.3-70b-versatile`) ➔ Google Gemini (`gemini-2.5-flash`) ➔ Algorithmic Heuristic Fallback.
  - Research: Google News RSS Wire ➔ Direct Domain Scraper ➔ Candidate Headlines.
* **Exponential Backoff**: Traps HTTP 429 errors and automatically retries with jitter and exponential backoff.
