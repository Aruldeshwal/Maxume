# Changelog: Maxume

All notable changes to Maxume are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/); every entry should be traceable to one Conventional Commit (see `gitworkflow.md` §2).

Categories per release: `Added`, `Changed`, `Fixed`, `Removed`, `Security`.

---

## [Unreleased]

### Added
- Nothing yet — this file is maintained in-commit starting from Phase 1 of `progresstracker.md`.

---

## How to Use This File (for implementers and coding agents)

*   Every `feat:` or `fix:` commit adds exactly one bullet here, under the matching category, in the same commit.
*   Write entries for what a user or downstream developer would care about, not internal refactor detail (`refactor:` and `chore:` commits generally do **not** need a changelog line unless they change observable behavior).
*   When cutting a release (`gitworkflow.md` §5, Step 4), rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` and open a fresh empty `[Unreleased]` section above it.

### Example of a properly formed future entry:
```
## [0.3.0] - 2026-09-01

### Added
- Company signal research pipeline with hallucination guard (`company_research.py`).
- Personalization Brief UI card, including the "no recent signal found" state.

### Fixed
- SQLite schema: corrected `AUTOINCREMENT` keyword and a mismatched CHECK
  constraint on `networking_contacts.referral_status`.

### Security
- Company-signal fetcher now respects `robots.txt` and applies an 8s
  per-source timeout to prevent a slow external site from blocking the
  pipeline.
```
