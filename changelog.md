# Maxume Project Changelog

All notable changes, architectural pivots, and enhancements are documented here.

---

## [v1.0.0] - 2026-08-17 (Production Release)

### Added
- **AI High-Impact Resume Bullet Synthesizer**: Implemented Google's XYZ formula (*Accomplished X as measured by Y, by doing Z*) with architectural power verbs in `github_sync.py`.
- **Project Visibility Controls**: Added `is_hidden` column in SQLite, Active/Hidden filter tabs, hide/unhide toggles, and repo deletion in `ProjectSync.tsx`.
- **Direct Clipboard Pasting (`Ctrl+V`)**: Added global keyboard paste listener for multi-screenshot ingestion directly from screenshot tools.
- **Authentic Skills Synthesizer**: Built `skills_engine.py` to extract only candidate's genuine technologies from verified repositories, eliminating fake tech hallucinations (e.g. Go, Rust).
- **Real-Time News Wire**: Built Google News RSS integration in `company_research.py` for dated, real-time public company signals and launches.
- **Targeted LinkedIn Referral Personas**: Added automated LinkedIn persona generation (*Tech Leads*, *Engineering Managers*, *Recruiters*) with tailored 75-word referral outreach drafts in `employee_lookup.py`.
- **Tab State Persistence**: Re-architected `App.tsx` tab wrappers with CSS visibility to prevent state loss across navigation.
- **Windows Explorer Output Opener**: Added `POST /api/open-folder` endpoint and UI button to open compiled output folders directly in Windows.

### Changed
- **Single-Page DOCX Calibration**: Calibrated `DocxEngine` with strict paragraph-level line spacing (`Pt`), limiting projects to top 3 and bullets to 2 each to guarantee exact 1-page fit.
- **Metadata Cleansing**: Added strict bullet filter in `docx_engine.py` and `gemini_service.py` to strip `GitHub:`, `Language:`, and header labels.
- **SQLite Concurrency & Upsert**: Updated `create_application` with `ON CONFLICT` clause and child cascade cleanup for seamless re-optimization.

### Removed
- Removed legacy Google CSE API keys and dead code in favor of native, zero-cost Google News RSS wire and targeted LinkedIn personas.
- Removed hardcoded dummy text placeholders in `Optimizer.tsx`.
