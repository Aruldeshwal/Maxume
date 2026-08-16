# Testing & Quality Assurance Strategy: Maxume

This document defines what "done" means for each layer of Maxume, and is the doc an agentic coding CLI should consult before marking any `progresstracker.md` checklist item complete.

---

## 1. Test Pyramid

```
              /\
             /  \        Manual QA: Milestone gates (progresstracker.md §3)
            /----\        — full-pipeline runs, visual DOCX inspection
           /      \
          / Integr.\     Integration tests: sidecar endpoints, real (rate-limited)
         /----------\     calls to free-tier APIs in CI, mocked in local dev
        /            \
       /   Unit Tests  \  Unit tests: docx_engine, company_research, scheduler,
      /------------------\ git watcher hash comparison — no network, no GPU
```

---

## 2. Unit Test Requirements (Python Sidecar)

Location: `sidecar/tests/`. Framework: `pytest`.

*   **`docx_engine.py`**: Given a fixture `.docx` with `{{PROJECTS}}`/`{{SKILLS}}` placeholders, assert the rebuilt document preserves paragraph style properties (indent, line-spacing) and that placeholder text no longer appears post-injection. No live Word/LibreOffice dependency — assert against the parsed XML tree.
*   **`company_research.py`**:
    *   Given a set of mock snippets within the recency window, assert `research_company()` returns `status: "FOUND"` with signals carrying correct `source_tier` ordering.
    *   Given snippets all outside `PERSONALIZATION_RECENCY_DAYS`, assert `status: "NO_SIGNALS_FOUND"`.
    *   Given a mock Gemini response containing a fact not present in any source snippet, assert `passes_containment_check()` returns `False` for that bullet and it is excluded from the final brief.
    *   Assert the function never raises for "nothing found" — only for genuine transport-level errors (e.g. malformed API key), which should surface as a distinct, catchable exception type, not a silent `NO_SIGNALS_FOUND`.
*   **`scheduler.py`**: Assert `APIRateLimiter.consume()` sleeps approximately the expected duration when tokens are exhausted (use a fake clock, not real `time.sleep`, to keep tests fast); assert `TokenAwareScheduler.execute_task()` retries on a simulated `429` and gives up after `max_retries`.
*   **Git watcher**: Assert commit-hash comparison correctly identifies "unchanged" vs "modified" against a temp Git repo fixture, without touching the user's real `/projects` folder.

---

## 3. Integration Test Requirements

Location: `sidecar/tests/integration/`, gated behind an environment flag (`RUN_INTEGRATION=1`) so they don't run by default in fast local loops.

*   **Ollama round-trip**: Requires a running local Ollama instance; asserts a real `/api/generate` call against `qwen2.5:7b-instruct` returns a non-empty `response` field within a timeout.
*   **Gemini / Groq / Google CSE round-trip**: Uses real free-tier keys from a dedicated test account (never the developer's personal keys); runs against a small, fixed set of inputs to avoid burning quota. Skipped automatically if the relevant `*_API_KEY` env var is absent.
*   **Company research end-to-end**: One test targeting a company known to have stable, old public news (to avoid recency-window flakiness) and one targeting a fictitious/nonexistent company name, asserting the latter reliably produces `NO_SIGNALS_FOUND` rather than an error.

---

## 4. Frontend Testing

*   **Component tests** (Vitest + React Testing Library): `SignalCard.tsx` renders correctly for both the "signals found" and "none found" states; `QuotaRing.tsx` renders correct fill percentage from mock quota data; `TerminalLog.tsx` correctly appends streamed SSE lines in order.
*   **No end-to-end browser automation is required for v1** — Tauri's webview + sidecar IPC surface is small enough that component tests plus the manual milestone gates below give adequate coverage without the maintenance cost of a full E2E suite.

---

## 5. Manual QA Gates

These map directly to the milestones in `progresstracker.md` §3 and must be run before any `main` release tag:

1.  **Docx Compilation Quality Gate** — visual inspection in MS Word and Google Docs.
2.  **Offline Failover Validation** — full pipeline with network disabled.
3.  **Zero-Cost Sandbox Verification** — 150-run batch, verify $0.00 spend across all provider dashboards.
4.  **Personalization Integrity Gate** — audit `company_research_signals` for source traceability and guard-check accuracy, per `progresstracker.md` Milestone 4.

---

## 6. Definition of Done (Per Checklist Item)

A `progresstracker.md` item is not complete until:
1.  The corresponding code is committed per `gitworkflow.md`'s micro-commit rule.
2.  At least one unit test exists and passes for new logic.
3.  `changelog.md` has a matching entry (if the change is user-observable).
4.  Any new failure mode discovered while building it is logged in `difficulties.md`, and any nontrivial choice made is logged in `decisions.md`.
