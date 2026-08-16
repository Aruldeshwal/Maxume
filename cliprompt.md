# Maxume — Master CLI Build Prompt

**Target tools**: Claude Code (primary), Cursor, Aider, or any agentic CLI coding tool with file-write, shell, and git access.
**How to use this file**: Paste its full contents as the initial instruction to your coding agent, with all 17 companion documents (`readme.md` through `interviewprep.md`, this file excluded) available in the working directory or attached to context. Do not summarize or paraphrase this prompt to the agent — hand it over verbatim; the constraints below are load-bearing, not stylistic.

---

## 0. Role and Operating Mode

You are implementing **Maxume**, a local-first, zero-operating-cost, hybrid desktop job-application assistant. You have full access to the 17 specification documents listed in `readme.md`'s documentation directory. **Those documents are your source of truth.** Where this prompt and a spec document disagree, the spec document wins — this prompt is an execution wrapper around them, not a replacement for them.

You will work **milestone by milestone**, following the phase breakdown in `progresstracker.md` §2, in order. Do not skip ahead to a later phase's tasks even if they look easy or related — sequencing matters because later phases assume earlier ones are fully committed and tested.

Before writing any code in a phase, re-read the specific docs that phase touches (listed per-phase below). Do not rely on a first read from earlier in the session — specs may have been refined mid-conversation.

---

## 1. Non-Negotiable Execution Rules

1.  **Micro-commit discipline** (`gitworkflow.md` §2): one checklist item from `progresstracker.md` = one commit = one push. Conventional Commits format, mandatory, every time. Never batch multiple checklist items into one commit, and never leave a commit unpushed while starting the next task.
2.  **Documentation-as-you-go** (`gitworkflow.md` §3): when you hit a real implementation snag, add it to `difficulties.md` in the *same commit* as the fix. When you make a nontrivial choice between real options, add an ADR to `decisions.md` in the same commit. Update `changelog.md` in the same commit as any user-observable `feat`/`fix`. Do not defer these to a "docs cleanup" pass at the end — if you find yourself about to do that, stop and go back to write them now, attached to the commits that actually earned them.
3.  **Definition of done** (`testing.md` §6): a checklist item is not complete until it has a passing unit test, a changelog entry (if user-observable), and any discovered difficulty/decision logged. Do not mark a `progresstracker.md` checkbox `[x]` until all of this is true.
4.  **No PII leaves the local machine except through the explicitly documented, consented cloud-failover path** (`security.md` §1, §3). If you write any code path that could send resume content, name, email, or phone number to Gemini, Groq, or any external endpoint outside that documented failover, stop and flag it — do not proceed on the assumption it's probably fine.
5.  **The hallucination guard is not optional and not a "nice to have for later"** (`companyresearch.md`, `decisions.md` ADR 5). Any code path that lets an LLM-generated company fact reach a cover letter or email without passing all three guard layers is a correctness bug, not a polish item, and should block that feature's checklist item from being marked done.
6.  **Ask before assuming on genuinely ambiguous product decisions**; do not ask about things the spec docs already answer. If a doc is silent on something load-bearing (e.g. "what happens if two applications target the same company on the same day"), make the most reasonable choice, document it as an ADR, and keep moving — do not block on it.

---

## 2. Global Definition of Done for the Whole Project

Before considering Maxume "v1 complete," all four milestone gates in `progresstracker.md` §3 must pass, in order:

1.  Perfect Docx Compilation Quality Gate
2.  Offline Failover Validation Check
3.  Zero-Cost Sandbox Verification (150-run batch)
4.  Personalization Integrity Gate (audit of `company_research_signals`)

Do not attempt final release packaging (`gitworkflow.md` §5) until all four have been run and passed at least once against a real build.

---

## 3. Phase-by-Phase Build Instructions

### Phase 1 — Local Backbone
**Read first**: `architecture.md` §1, `codestandards.md` §1, `progresstracker.md` §1, `envsetup.md`.

1. Scaffold the Tauri v2 app and the Python FastAPI sidecar using the exact directory layout in `codestandards.md` §1. Do not deviate from this layout without an ADR explaining why.
2. Wire up sidecar packaging per `gitworkflow.md` §5 Step 1–2 early, even though release is far off — catching PyInstaller/Tauri naming mismatches now is cheaper than at release time.
3. Implement the SQLite schema exactly as specified in `progresstracker.md` §1, including the corrected `AUTOINCREMENT` syntax and the `company_research_signals` table (even though the feature that populates it lands in Phase 3 — the schema should be complete from the start so later migrations aren't needed).
4. Implement the Incremental Git Watcher per `projectoverview.md` §2. Unit-test the commit-hash comparison logic against a disposable temp Git repo fixture, per `testing.md` §2 — never against the developer's real `/projects` folder.

**Exit criteria**: `npm run tauri dev` launches a blank-but-functional shell, the sidecar responds on localhost, and the SQLite schema is migrated. Commit and push each of these four items separately.

---

### Phase 2 — Core Processing & Docx Engines
**Read first**: `projectoverview.md` §3, `decisions.md` ADR 3, `codestandards.md` §5.

1. Implement the Paragraph-Level Rebuilding engine (`docx_engine.py`) exactly per the algorithm in `projectoverview.md` §3, including the hyperlink-embedding function shown there verbatim — do not rewrite it from scratch, the OXML element ordering it uses is deliberate.
2. Implement the single-page guardrail (max 4 projects, max 4 bullets each).
3. Implement markdown hyperlink extraction from `/projects` files and persist URLs to SQLite.
4. Implement the dynamic Ollama model discovery (`GET /api/tags`) and the VRAM guardrail math from `architecture.md` §3 — use the reconciled figures from `difficulties.md` §1 (4.7–4.8GB base load, not the file size alone) when computing whether a candidate model fits.

**Exit criteria**: A fixture `.docx` with `{{PROJECTS}}`/`{{SKILLS}}` placeholders can be rebuilt with injected content, verified both by the unit test in `testing.md` §2 and by manual inspection in real MS Word / Google Docs (Milestone 1's validation checks, run early even though the formal gate is later).

---

### Phase 3 — Multimodal & Cloud APIs
**Read first**: `architecture.md` §2 and §5, `apicontracts.md` §1–5 in full, `companyresearch.md` in full, `decisions.md` ADR 1, 2, 4, 5, `security.md` §4.

This is the largest and highest-risk phase. Build in this sub-order, each as its own set of micro-commits:

1. **Pillow compression pipeline** for screenshot JDs (`decisions.md` ADR 1) — grayscale, 150 DPI, target under 300KB.
2. **Gemini OCR + reranking integration** per `apicontracts.md` §1–2 and `decisions.md` ADR 2 — local top-8 filter, Gemini reranks to top 3–4.
3. **Company Signal Research pipeline** (`company_research.py`) — implement Stages A through E exactly as specified in `companyresearch.md` §2:
   - Stage A/B: Google CSE discovery query + direct fetch of the company's own domain when known, respecting `robots.txt`, 8-second timeout per source, descriptive User-Agent (`security.md` §4).
   - Stage C: the grounded, `temperature: 0.0` Gemini summarization prompt from `apicontracts.md` §5c, used verbatim.
   - Stage D: the deterministic containment check from `apicontracts.md` §5d — implement this as plain string/keyword matching, **not** as another LLM call (`decisions.md` ADR 5 explains why; do not "improve" this into an LLM-based check).
   - Stage E: confirm the function signature and return shape exactly match `apicontracts.md` §5b, including that `NO_SIGNALS_FOUND` is a normal return value, never an exception.
   - Write the unit tests specified in `testing.md` §2 for this module before considering it done — this module has the highest correctness bar in the codebase.
4. **Google CSE employee lookup** per `apicontracts.md` §4 — confirm it shares rate-limiter state with company research per `codestandards.md` §2's note, not a separate quota.
5. **Groq creative generation** per `apicontracts.md` §3 — the system prompt MUST include the grounding constraint block exactly as shown, branching on whether the research brief is populated or `NO_SIGNALS_FOUND`. Do not write a version of this prompt that omits the constraint "you may only reference facts in RESEARCH_BRIEF" — that omission is exactly the bug this whole feature exists to prevent.
6. **Token-Aware Scheduler** (`codestandards.md` §2) wrapping every external API call made in this phase, with exponential backoff on `429` per `difficulties.md` §3.

**Exit criteria**: A full pipeline run against a real (rate-limited, low-volume) test job description produces a resume, cover letter, and email, with the personalization brief correctly populated or correctly showing `NO_SIGNALS_FOUND` depending on the target company. Run the integration tests from `testing.md` §3 (behind `RUN_INTEGRATION=1`) before moving to Phase 4.

---

### Phase 4 — Legion UI & Polish
**Read first**: `ui.md` in full, `codestandards.md` §1 (frontend structure).

1. Implement the Legion Red & Black dark theme per `ui.md` §1's exact palette values — use CSS custom properties, not hardcoded hex per-component, so the theme stays swappable.
2. Build the four tabs per `ui.md` §3. Build `SignalCard.tsx` to handle both the "signals found" and "none found" states explicitly as distinct, intentional designs — the "none found" state must read as informational (muted slate-blue per `ui.md` §1), never as an error or warning.
3. Wire the terminal-log SSE stream to show the phase-by-phase execution log from `ui.md` §3 Tab C, including the two new research-stage log lines.
4. Add the Personalization Toggle and Quota Tracker ring updates per `ui.md` Tab A/C.
5. Frontend component tests per `testing.md` §4.
6. Multi-platform build packaging per `gitworkflow.md` §5 — only after all four milestone gates in `progresstracker.md` §3 have passed at least once.

**Exit criteria**: All four milestone gates pass against a real packaged build, not just `tauri dev`.

---

## 4. What to Do When You Get Stuck

*   **A spec doc is ambiguous on something small**: make the most reasonable call, log it as a one-line ADR, keep moving.
*   **A spec doc is ambiguous on something that changes architecture** (e.g. would require a different DB table, a different API provider, a different trust boundary): stop and ask, don't guess.
*   **You hit a real bug in the spec itself** (not just an implementation difficulty — an actual error in a doc, the way the original `progresstracker.md` had an invalid `AUTO_INCREMENT` keyword): fix the doc in the same commit as the code that revealed the bug, and note the correction in that commit's body.
*   **A milestone gate fails**: do not proceed to the next phase. Fix, re-run the gate, and only then continue.

## 5. Final Note on Scope

This prompt describes a real, sizeable application. Do not attempt to build all four phases in one uninterrupted session without checkpoints — stop after each phase's exit criteria are met, report status against `progresstracker.md`, and confirm before continuing into the next phase. This keeps the micro-commit history reviewable and gives a natural point to catch drift between the running code and the specs early, rather than discovering it at the end.
