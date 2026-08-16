# Architectural Retrospective & Takeaways: Maxume

## 1. Key Engineering Takeaways

Building a local-first, zero-operating-cost AI productivity application like Maxume yields several critical architectural insights:

*   **VRAM is a Hard Boundary**: Unlike cloud systems where scaling is a budget question, local consumer laptops operate under strict hardware limits. Capping the context window of local LLMs isn't an optimization — it's a prerequisite for usable generation speed (60+ tok/s) and avoiding CUDA OOM crashes. It's also worth sanity-checking the arithmetic explicitly, not just qualitatively: a "budget" and a "base load" figure that don't actually leave headroom for each other is a bug hiding in the design doc, not just in the code (see the VRAM reconciliation in `difficulties.md` §1).
*   **The Power of Hybrid Orchestration**: You don't need to run everything locally to build a private, high-performance tool. Routing PII-sensitive data through a local model (Ollama) while leveraging fast cloud APIs (Gemini, Groq) for non-sensitive creative tasks is the optimal pattern for local-first productivity tools.
*   **Decoupled Sidecar Pattern**: Combining **Tauri v2** with a **Python FastAPI Sidecar** is a strong desktop architecture. Tauri handles native UI with near-zero VRAM overhead, preserving GPU capacity for `python-docx`, `Pillow`, and local LLM execution.
*   **Grounding Beats Cleverness**: The instinct when adding "personalization" to an AI product is to ask the model to be more creative. The better instinct is almost always the opposite — constrain what the model is allowed to assert, and build an independent, deterministic check behind the constraint rather than trusting the prompt alone. A three-layer guard (recency filter, grounded prompt, non-LLM containment check) caught failure modes that a single well-written prompt alone did not, without adding meaningful latency or cost.
*   **"Found Nothing" Is a Valid, First-Class Outcome**: Treating `NO_SIGNALS_FOUND` as an error state (or worse, silently falling back to a generic-sounding fabrication) would have been the easy path. Designing it as an expected, cleanly-surfaced UI state — instead of something to be embarrassed about or hide — turned out to be both the more honest choice and the simpler one to implement and test.

---

## 2. Zero-Cost API Synergy

Orchestrating multiple free APIs into a unified workspace demonstrates how capable the current free-tier developer ecosystem is:

1.  **Gemini Developer API**: Exceptional for context-heavy work, screenshot OCR, and — at `temperature: 0.0` — grounded summarization where creativity is actively unwanted (1,000 requests/day).
2.  **Groq API**: Blazing-fast creative writing speeds (14,400 daily requests).
3.  **Google Custom Search Loophole**: Safely fetches employee profiles and company signals (100 free searches/day, shared across both use cases) without triggering bans or requiring authenticated session cookies.
4.  **Ollama**: Unlimited local intelligence for secure data.

By mapping each micro-task to the ideal provider — including matching "this task must not hallucinate" tasks to a `temperature: 0.0` call plus a deterministic check, rather than to a more "creative" model — Maxume achieves a high-performance system at an operating cost of exactly **$0**.

---

## 3. Future-Proofing & Extensibility

*   **Model-Agnostic Interface**: Decoupling LLM interactions into an OpenAI-compatible JSON endpoint keeps Maxume future-proof — a more efficient local model can be adopted with zero code changes, just a settings-menu swap.
*   **Stateless File Storage**: Writing resume packs to `/output/[company_name]` while recording state in SQLite means output folders can be freely moved or backed up without breaking application history.
*   **The Same Guard Pattern Generalizes**: The three-layer grounding approach built for company research (recency/source filter → constrained prompt → deterministic verification) isn't specific to news summarization — it's a reusable template for any future feature where an LLM output will be shown to a third party as fact.
