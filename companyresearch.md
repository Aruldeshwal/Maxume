# Company Signal Research & Personalization Pipeline: Maxume

## 1. Why This Exists

Generic cover letters ("I am excited about your company's mission and innovative culture...") are worse than useless — recruiters pattern-match them instantly, and they can actively signal low effort. The fix is to ground outreach in something true and current about the target company: a product launch, a funding round, a recent piece of press, an engineering blog post.

The failure mode to avoid is worse than the problem being solved: an LLM confidently fabricating a company detail ("congratulations on your recent Series C") that is stale, wrong, or invented. A single hallucinated fact in an outbound cover letter can read as either careless or dishonest. This document specifies how Maxume gets personalization *right* — sourced, current, and honest about its own gaps — via a dedicated **hallucination guard**.

---

## 2. Pipeline Stages

```
 [Company Name + Careers/About URL, if known]
        |
        v
 [Stage A: Source Discovery]
  - Google CSE query: "[COMPANY_NAME]" news OR "product launch" OR funding
  - Targeted fetch of company's own /newsroom, /blog, /press pages if the
    domain is known (from the JD or company URL input)
  - Recency filter: discard anything older than a configurable window
    (default: 90 days) — stale news reads worse than no news
        |
        v
 [Stage B: Snippet Extraction (No Summarization Yet)]
  - Collect raw, verbatim snippets + source URL + published date per hit
  - Cap at 5 candidate signals to keep the downstream prompt small and
    keep the summarizer from having to arbitrate between too many facts
        |
        v
 [Stage C: Grounded Summarization (Gemini 2.5 Flash-Lite)]
  - Prompt is constructed so Gemini can ONLY use the literal snippets
    passed to it - it is explicitly instructed not to add outside
    knowledge, infer facts not stated, or resolve ambiguity by guessing
  - Output is structured JSON (see apicontracts.md §5), one entry per
    retained signal, each carrying its source URL back out
        |
        v
 [Stage D: Hallucination Guard Check]
  - If Stage A/B produced zero qualifying snippets -> brief is marked
    NO_SIGNALS_FOUND. Stage C is skipped entirely (nothing to summarize).
  - If Stage C's output references any fact/entity not traceable to a
    snippet passed in (checked via a lightweight substring/keyword
    containment check, not another LLM call - see §4) -> that signal is
    dropped and, if none remain, the brief falls back to NO_SIGNALS_FOUND
        |
        v
 [Stage E: Handoff to Creative Generation]
  - The brief (populated or NO_SIGNALS_FOUND) is passed to Groq as a hard
    constraint block in the system prompt, not as loose context
```

---

## 3. Source Tiering

Not all sources are equal. Maxume ranks candidate signals in this priority order when more than the cap of 5 are found:

1.  **Company's own domain** (newsroom, blog, press page) — highest trust, first-party.
2.  **Major/tech press** (results from reputable outlets surfaced via Google CSE).
3.  **Company's public GitHub org** (release notes, changelogs) — useful for engineering-team-specific personalization.
4.  *Excluded entirely*: forums, unverified social posts, aggregator sites with no clear original source, anything behind a paywall Maxume can't actually read the full text of.

If Stage A only turns up Tier-4-only material, that does not count as a qualifying signal — it is treated the same as finding nothing.

---

## 4. The Hallucination Guard, Concretely

The guard is not a single feature — it's three independent checks stacked together, because any one of them failing silently is how a fabricated detail would slip into a cover letter:

1.  **Recency check** (Stage A): a hard filter, not a preference. Anything outside the recency window never reaches summarization.
2.  **Grounding-only prompt constraint** (Stage C): the summarization prompt is written defensively — it states the exact snippets as the *only* permissible source of fact, tells the model to output `NO_SIGNALS_FOUND` itself if the snippets don't actually support a usable claim, and forbids elaboration.
3.  **Post-hoc containment check** (Stage D): a cheap, deterministic check — not another LLM call — that verifies key named entities and numbers in Gemini's summary actually appear in the source snippets it was given. This catches the case where a grounded prompt still drifts. A signal that fails this check is dropped silently from the brief; it is never surfaced to the user as an error, since the correct behavior is simply "don't personalize on that one."

If every candidate signal is dropped by Stage D, the brief becomes `NO_SIGNALS_FOUND` — the same state as if Stage A found nothing at all. From the creative-generation prompt's point of view, "found nothing" and "found something we couldn't verify" are identical: both mean "write a strong, professional, non-generic letter without inventing company-specific color."

---

## 5. What the User Sees

*   **Signal found**: The Networking/Personalization panel shows 1–3 short signal cards (headline, source domain, date), each with a link to the source. The generated cover letter/email references at least one of them, and the reference is visibly traceable to a listed source.
*   **No signal found**: The panel shows a plain, non-alarming notice — *"No recent public signal found for [Company] in the last 90 days. Your cover letter was written on your background and the role alone."* This is a normal, expected state for smaller or private companies, not an error.
*   Maxume never silently substitutes a stale or off-topic fact to avoid showing this notice. An honest "nothing found" is a better outcome than a plausible-sounding wrong one.

---

## 6. Configuration

| Setting | Default | Notes |
|---|---|---|
| `PERSONALIZATION_RECENCY_DAYS` | 90 | Signals older than this are discarded at Stage A |
| `PERSONALIZATION_MAX_SIGNALS` | 5 | Cap on candidate snippets passed to Gemini |
| `PERSONALIZATION_MIN_SIGNALS_FOR_USE` | 1 | Minimum signals surviving Stage D to avoid NO_SIGNALS_FOUND |
| `PERSONALIZATION_ENABLED` | true | User can disable this stage entirely per-application to save quota |

---

## 7. Relationship to Other Docs

*   Request/response JSON schema: `apicontracts.md` §5.
*   Database table for persisted signals: `progresstracker.md` §1 (`company_research_signals`).
*   Risk register entry for scraping brittleness and residual hallucination risk: `difficulties.md` §4.
*   Design rationale (why Gemini + containment-check over a dedicated grounding API): `decisions.md` ADR 4 and ADR 5.
*   Ethical/legal scraping boundaries (robots.txt, no paywall bypass): `security.md` §4.
