# Project Overview & Workflow Specification: Maxume

## 1. Core Workflow Pipeline

The Maxume workspace operates as a local-first state machine. It orchestrates user assets (Master Resume, Projects folder, API keys) and target application inputs (Job Description text/screenshot, Company Link) into a compiled output directory.

```
 [User Inputs]
  - Master Resume (docx)
  - /projects Folder (markdown repo)
  - Target JD (Text / Screenshot)
  - Company URL
        |
        v
 [Step 1: Folder Sync & Watcher]
  - Executed on startup / manual trigger
  - Scans /projects, extracts URLs
  - Incremental Git checks (skip unchanged)
  - Generates [dir_name]_summary.md using local Ollama/Gemini
        |
        v
 [Step 2: JD & Screening Analysis]
  - Preprocesses screenshot (Pillow compression)
  - Gemini OCR + keyword clustering
        |
        v
 [Step 3: Reranking & Selection]
  - Local vector similarity top-8 retrieval
  - Gemini reranks top 3-4 projects
  - Pulls top 4-5 bullet points per project
        |
        v
 [Step 4: Company Signal Research (Grounded)]
  - Google CSE + targeted fetch of company newsroom/blog/careers page
  - Gemini summarizes ONLY retrieved snippets, with inline source citations
  - Hallucination Guard: if no signal found within the recency window,
    the brief is marked NO_SIGNALS_FOUND and downstream generation is
    instructed to stay generic rather than invent a detail
  - See companyresearch.md for full pipeline detail
        |
        v
 [Step 5: Resume & Asset Assembly]
  - Injects bullets into Docx via Paragraph-level Rebuilding
  - Generates cover letter and emails via Groq (Llama 3.3 70B), consuming
    the Step 4 brief (or its NO_SIGNALS_FOUND flag) as grounding context
  - Google CSE queries LinkedIn employees (HR & SDEs)
        |
        v
 [Step 6: Outputs Saved]
  - Writes files to /output/[company_name]/
  - Displays networking contact cards and the personalization brief
    (or "no recent signal found" notice) in the React UI
```

---

## 2. Incremental Git Synchronizer & Watcher

The `/projects` master directory is the Single Source of Truth (SSOT) for engineering project experience. It contains subdirectories representing individual projects, each housing project code and raw markdown experience logs.

### Git Repository Detection & State Optimization
To minimize API overhead and avoid redundant local LLM runs, Maxume implements an **Incremental Git Watcher** in the Python sidecar:

1.  **Repository Handshake**: On folder watch initiation, the backend runs `git rev-parse --is-inside-work-tree` from `/projects` to verify Git tracking.
2.  **Commit Signature Hashing**: If tracked, the sidecar reads the current commit hash of each sub-folder via `git log -1 --format="%H" -- [subdirectory_path]`.
3.  **State Lookup**: The backend checks the local SQLite database (`maxume_local.db`) for a matching subdirectory path and commit hash.
4.  **Conditional Summarization**:
    *   *Match Found*: Skip generation — `[directory_name]_summary.md` is up to date.
    *   *No Match*: Trigger a background summarization task; the sidecar passes all markdown files in that subdirectory to the local LLM (or Gemini, per failover settings) to output a structured project summary highlighting tech stack and quantitative achievements.
5.  **State Upkeep**: The new commit hash and subdirectory path are recorded in SQLite, preventing duplicate runs.

---

## 3. Paragraph-Level DOCX Style-Copying & Link Embedding

Word documents (`.docx`) store content as raw XML. Naive text-swap libraries corrupt formatting because Word fragments strings like `{{PROJECTS}}` across multiple XML `<w:r>` runs.

Maxume uses **Paragraph-Level Rebuilding** with `python-docx`:

### Rebuilding Algorithm
1.  **Tag Location**: Parse document paragraphs, identify ones containing exact placeholder tags `{{PROJECTS}}` and `{{SKILLS}}`.
2.  **Parent Context Extraction**: Capture the reference paragraph's style properties (margins, line-spacing, tab stops, parent style template).
3.  **Bullet Construction**: For each ranked project, create a new paragraph immediately preceding the placeholder, copying reference style characteristics:
    ```python
    new_para = doc.add_paragraph(style=placeholder_para.style)
    new_para.paragraph_format.left_indent = placeholder_para.paragraph_format.left_indent
    new_para.paragraph_format.line_spacing = placeholder_para.paragraph_format.line_spacing
    ```
4.  **Placeholder Pruning**: Delete the original placeholder paragraph once styled paragraphs are injected.
5.  **Single-Page Guardrail**: Enforce a strict limit of 4 projects and 4 bullets per project to guarantee a one-page compile.

### Live Link Hyperlink Extraction and Embedding
During folder-watch sync, the sidecar parses markdown project files for hyperlinked references (e.g. `[Live Demo](https://...)` or raw URLs) and catalogs them in SQLite. When a project is selected for resume generation, Maxume constructs an active MS Word hyperlink run on the project title:

```python
def add_hyperlink(paragraph, url, text, color="990000", underline=True):
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = docx.oxml.shared.OxmlElement('w:hyperlink')
    hyperlink.set(docx.oxml.shared.qn('r:id'), r_id)
    new_run = docx.oxml.shared.OxmlElement('w:r')
    rPr = docx.oxml.shared.OxmlElement('w:rPr')
    if color:
        c = docx.oxml.shared.OxmlElement('w:color')
        c.set(docx.oxml.shared.qn('w:val'), color)
        rPr.append(c)
    if underline:
        u = docx.oxml.shared.OxmlElement('w:u')
        u.set(docx.oxml.shared.qn('w:val'), 'single')
        rPr.append(u)
    new_run.append(rPr)
    text_node = docx.oxml.shared.OxmlElement('w:t')
    text_node.text = text
    new_run.append(text_node)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink
```
Recruiters can click a project title inside Word or Google Docs and land directly on the live deployment.

---

## 4. Where Personalization Enters the Pipeline

Company-signal research (Step 4) is deliberately placed **after** reranking and **before** creative generation, for two reasons:

1.  It only needs to run once per application (per company), regardless of how many projects were matched — running it earlier would waste API calls on companies that get filtered out later in edge cases (e.g. duplicate applications).
2.  Groq's creative-generation prompt (Step 5) needs the finished brief — or its explicit absence — as a hard constraint before it starts drafting, not as something bolted on afterward. See `companyresearch.md` for why this ordering matters to the hallucination guard.
