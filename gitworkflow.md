# Git Workflow & Release Lifecycle Specification: Maxume

## 1. Local Development Branching Strategy

Maxume is developed locally following a streamlined, robust branch-per-feature strategy, since Tauri's Rust compilation and Python's virtual env packaging can easily introduce system platform conflicts:

```
  main         =============================================> (Local Release v1.0.0)
                ^                     ^
                | Merge PR            | Merge PR
  dev          -+---------------------+---------------------> (Bleeding-edge Integration)
                 \                   /
  feature/docx-   +=================+ (Targeted Sandbox Iterations)
  engine
```

*   **`main` Branch**: Reserved exclusively for stable, production-ready desktop builds. No raw commits.
*   **`dev` Branch**: The primary integration trunk. All feature branches merge here. Code must compile cleanly without breaking the Tauri Rust sidecar wrapper.
*   **Feature Branches (`feature/` or `fix/`)**: Isolated sandboxes, e.g. `feature/docx-style-cloner`, `feature/company-research-guard`, before PRs into `dev`.

---

## 2. Micro-Commit Discipline (Mandatory)

This is the single most important rule for anyone — human or AI coding agent — implementing Maxume: **one task = one commit = one push.**

*   A commit corresponds to one checklist item from `progresstracker.md`, not to "a good stopping point." If a task is too large for a single coherent commit, split the task, not the commit.
*   **Conventional Commits format** is required for every commit message:
    ```
    <type>(<scope>): <short summary>

    <optional body: what changed and why>
    <optional footer: BREAKING CHANGE, refs>
    ```
    Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `style`.
    Scopes should match the module touched, e.g. `docx_engine`, `company_research`, `ui`, `scheduler`.

    Example:
    ```
    feat(company_research): add hallucination guard containment check

    Adds a deterministic keyword-containment check that verifies Gemini's
    summarized signals actually appear in the source snippets before they
    are marked guard_check_passed. Falls back to NO_SIGNALS_FOUND if every
    candidate signal fails the check.

    refs: companyresearch.md §4, progresstracker.md Phase 3
    ```
*   Push after every commit — do not batch several commits before pushing. This keeps `dev` reflecting real, incremental progress and makes any failure easy to bisect.
*   Never combine a documentation update with an unrelated code change in the same commit — use `docs:` commits for pure documentation work.

---

## 3. Documentation-as-You-Go

Six documents are living artifacts that get written to **in-commit, as work happens**, not backfilled at the end:

| Document | Updated when... |
|---|---|
| `changelog.md` | Every `feat`/`fix` commit adds one line under "Unreleased" |
| `difficulties.md` | A real failure mode is hit during implementation (not hypothesized in advance) |
| `decisions.md` | A nontrivial implementation choice is made between two or more real options |
| `learnings.md` | A retrospective insight emerges — usually written at phase boundaries, not per-commit |
| `architecture.md` | The actual system shape diverges from what was originally planned |
| `interviewprep.md` | A design decision produces a genuinely good interview talking point |

An agentic coding CLI executing `cliprompt.md` is expected to make these edits as part of the same commit as the code change they document, not as a separate cleanup pass.

---

## 4. Commit-Triggered Project Summarizer (Workspace Pipeline)

Maxume uses standard local folder watch hooks to automate project synchronization.

### The Automated Sync Trigger Loop
```
  [User Action]
   -> Commit changes in `/projects/web-scrapper`
   -> Push changes to GitHub (Local workspace updates)

  [Maxume Background Watcher Process]
   -> Scans project folder directories on interval
   -> Runs: `git rev-parse HEAD` on active project sub-folders
   -> Compare retrieved hash against database record:
      - Hash Matches: Skip summarization (Project unchanged).
      - Hash Differs: Trigger API summarization loop.

  [Summarizer Execution Loop]
   1. Locate latest commit message via: `git log -1 --pretty=format:%B`
   2. Collect all raw project markdown log files.
   3. Package files into prompt payload and send to Ollama / Gemini.
   4. Update / write local project summary markdown: `[dir_name]_summary.md`.
   5. Extract live deployment URLs and persist details to local SQLite database.
```

---

## 5. Production Compilation & Desktop Release Checklist

Before building final executables for Windows (`.msi` / `.exe`) or Linux (`.deb` / `.tar.gz`):

### Step 1: Python Dependency Bundling
```bash
cd sidecar && source venv/bin/activate
pip freeze > requirements.txt
pyinstaller --noconfirm --onedir --console --name "maxume_backend" "app/main.py"
```
Tauri sidecar naming rules require the output binary to match the target triple, e.g. `maxume_backend-x86_64-pc-windows-msvc.exe`.

### Step 2: Tauri Configuration Lock
```json
"bundle": {
  "externalBin": [
    "sidecar/maxume_backend"
  ]
}
```
```bash
npm run lint && npm run build
```

### Step 3: Compile System Binary Packages
```bash
npm run tauri build
```
Outputs land in `src-tauri/target/release/bundle/`:
*   *Windows*: `.msi` and a portable `.exe`.
*   *Linux*: `.deb` and `.AppImage`.

### Step 4: Pre-Release Changelog Cut
Move all entries from `changelog.md`'s "Unreleased" section into a new dated version heading before tagging the release — see `changelog.md` for format.
