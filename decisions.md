# Architectural Decisions (ADR): Maxume Design Log

## ADR 1: Screenshot OCR Strategy for Job Descriptions

### Context
When a user uploads a job description screenshot, the app must extract underlying text. Raw high-DPI screenshots can exceed 15MB, slowing uploads and inflating visual token consumption on free cloud APIs.

### Options Considered
*   **A (Direct Base64 Multimodal Upload)**: Stream the raw screenshot directly to the Gemini API.
*   **B (Local Image Preprocessing & Compression)**: Use `Pillow` in the sidecar to compress/downscale before upload.
*   **C (Local OCR Fallback via Tesseract)**: Run OCR fully offline via `pytesseract`.

### Decision
**Approach B**. Downscaling to 150 DPI and converting to grayscale slashes payload from 15MB to under 300KB with negligible text legibility loss, minimizing latency and API usage.

*Why not C*: Tesseract requires platform-specific C++ binary installs, degrading setup experience across Windows/Linux/macOS targets.

---

## ADR 2: Multi-Tiered Project Reranking Mechanics

### Context
With 30+ project folders in `/projects`, sending full file contents to an LLM for keyword matching would exceed local Ollama's VRAM-constrained context window (2K–3K tokens) and violate Gemini RPM limits.

### Options Considered
*   **A (Local Semantic Vector Search)**: Generate local embeddings, `numpy` cosine similarity on SQLite.
*   **B (Semantic Filtering + Gemini Reranking)**: Filter top 8 locally, pass to Gemini to choose top 4.

### Decision
**Approach B**. Pure embedding similarity misses exact, specialized keyword combinations recruiters' ATS systems key on. Local filtering to 8 candidates, then Gemini reranking, gives accurate ATS optimization at zero cost.

---

## ADR 3: DOCX Template Replacement Mechanics

### Context
Word documents store content in internal XML runs (`<w:r>`). Naive regex replacement on raw XML breaks because Word randomly partitions strings like `{{PROJECTS}}` into fragmented runs.

### Options Considered
*   **A (Run-Level Regex Swapping)**: Directly match/replace strings in raw XML text runs.
*   **B (Paragraph-Level Rebuilding)**: Locate the paragraph containing `{{PROJECTS}}`, clear it, and write new paragraphs programmatically, copying the template paragraph's formatting.

### Decision
**Approach B**. Robust against Word's unpredictable XML fragmentation; `python-docx` cloning of layout settings (indentation, line heights, font family) guarantees clean, crash-free compilation.

---

## ADR 4: Company Signal Discovery Method (New)

### Context
Personalizing outreach requires finding real, recent, company-specific facts. Options differ in cost, reliability, and how easy they make it to cite a verifiable source.

### Options Considered
*   **A (Dedicated paid News API)**: e.g. NewsAPI.org paid tier, GNews — reliable structured results but breaks the $0/month principle at any real usage volume.
*   **B (Google CSE, reused from employee-lookup credentials)**: Free, already provisioned, returns structured JSON with snippet + URL + date-adjacent metadata.
*   **C (Full-site crawling of arbitrary news aggregators)**: Broadest coverage, but highest scraping-fragility and ethics surface area (see `security.md` §4).

### Decision
**Approach B, supplemented by a direct fetch of the company's own domain when known** (Tier 1 in `companyresearch.md` §3). Reuses existing free credentials, keeps the $0/month principle intact, and Google's snippet+URL structure is exactly the shape the hallucination guard's containment check needs. Direct fetch of the company's own newsroom/blog is added as a first-party supplement because self-published company content is the highest-trust, least-ambiguous source available — but only when `robots.txt` allows it.

*Why not A*: paid tiers are a real recurring cost for a tool explicitly designed to have none.
*Why not C alone*: aggregator content is harder to attribute to an original, checkable source, which directly undermines the containment check's reliability.

---

## ADR 5: Hallucination Guard Design (New)

### Context
An LLM asked to "personalize a cover letter with recent company news" will, if not constrained, sometimes produce a plausible-sounding but unverifiable or outright fabricated detail. Because this output goes directly into an outbound email a real recruiter reads, the cost of a wrong claim is higher here than almost anywhere else in the pipeline.

### Options Considered
*   **A (Trust the summarization prompt alone)**: Rely entirely on careful prompt engineering ("only use the snippets provided") with no independent verification.
*   **B (A second LLM call to fact-check the first)**: Ask a separate model call to verify the summary against the source snippets.
*   **C (Deterministic post-hoc containment check + recency filter + grounded prompt, three independent layers)**: Combine a hard recency filter, a defensively-written grounded prompt, and a cheap non-LLM containment check that verifies key entities/numbers appear in the source text.

### Decision
**Approach C**, detailed fully in `companyresearch.md` §4.

*Why not A alone*: prompt-only grounding measurably reduces but does not eliminate drift, and drift here has outsized real-world cost.
*Why not B*: using a second LLM to fact-check a first LLM just moves the hallucination risk one level up — the fact-checker can itself hallucinate a "yes, this is grounded" verdict, and it doubles the API cost of every research pass for a check that a plain string-containment function does more reliably and for free.
*Why C wins*: each layer catches a different failure mode (stale data, prompt drift, subtle entity substitution), and the final layer is deterministic, so it cannot itself introduce new hallucination risk. The tradeoff is that Stage D is strict — it will sometimes drop a true, well-sourced signal because the phrasing didn't match closely enough for the containment check to confirm it. That tradeoff is accepted deliberately: silently under-personalizing is a far smaller cost than shipping a wrong fact in outbound correspondence.
