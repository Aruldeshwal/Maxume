# Engineering Learnings & Key Insights

### 1. Document Engineering with Python-Docx
* `python-docx` manages styles at the paragraph and run level, but lacks high-level APIs for hyperlinks. Embedding Word `<w:hyperlink>` directly via `oxml` with relationship IDs (`r:id`) is the most reliable way to insert styled, clickable URLs without corrupting document XML schemas.
* Word line spacing must be set explicitly using `Pt(1.5)` space-after and `1.05` line-spacing to guarantee that dynamic content fits within 1-page constraints.

### 2. High-Impact Resume Bullet Crafting (Google XYZ Formula)
* Simple tech-stack listings (*"Used React and Node.js"*) are weak for recruiter screening.
* Structuring bullets around **Accomplished [X] as measured by [Y], by doing [Z]** using power action verbs (*Architected*, *Engineered*, *Implemented*, *Optimized*) and architectural depth (caching, concurrency, latency, throughput) produces significantly higher impact.

### 3. Local-First & Airgapped Architecture
* Combining a local SQLite SSOT with local inference (Ollama) ensures that candidate master resumes, source code, and application logs never leave the local machine.
* Cloud AI (Groq, Gemini) should be utilized strictly for stateless tasks (creative copy synthesis, OCR transcription) using non-sensitive snippets.

### 4. Deterministic Guardrails Over Prompt Engineering
* LLMs cannot be trusted to self-police hallucinations through prompts alone.
* Post-hoc deterministic entity and number containment checks (`passes_containment_check`) provide mathematical guarantees against false claims reaching employers.
