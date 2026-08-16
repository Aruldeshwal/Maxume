# Automated Testing Suite & Verification Guide

## 1. Overview
Maxume includes a comprehensive two-tier test suite covering backend Python engines and frontend React components.

---

## 2. Test Execution Commands

```powershell
# 1. Run full backend Python pytest suite
.\sidecar\venv\Scripts\pytest.exe sidecar/tests/

# 2. Run full frontend React vitest suite
npm run test

# 3. Run all tests concurrently
.\sidecar\venv\Scripts\pytest.exe sidecar/tests/; npm run test
```

---

## 3. Backend Test Coverage (37 Tests, 100% Pass)

| Test Module | Coverage & Invariants Verified |
| :--- | :--- |
| `test_docx_engine.py` | Word OXML hyperlink injection, strict 3-project / 2-bullet single-page guardrail, and metadata filtering (`GitHub:`, `Language:`). |
| `test_skills_engine.py` | Authentic candidate skills synthesis from verified repositories with zero fake tech hallucinations. |
| `test_company_research.py` | Multi-source real-time news wire, source tiering (1/2/3), recency filters, and 3-stage hallucination containment guard. |
| `test_github_sync.py` | Public GitHub profile sync, live demo link extraction, and XYZ formula bullet parsing. |
| `test_api_endpoints.py` | FastAPI REST endpoints, request schemas, project visibility toggles, and folder openers. |
| `test_scheduler.py` | Token-bucket rate limiter, token refill rates, and exponential backoff retry on HTTP 429. |
| `test_database.py` | SQLite schema migrations, foreign keys, thread-safe connections, and `ON CONFLICT` upserts. |
| `test_image_optimizer.py` | Pillow grayscale image conversion, dimension resizing, and sub-300KB compression. |
| `test_ollama_manager.py` | Local Ollama discovery, model switching, and dynamic VRAM threshold checks. |
| `test_cloud_services.py` | Gemini Multimodal OCR and Groq creative generation cascades with local fallbacks. |

---

## 4. Frontend Component Test Coverage (7 Tests, 100% Pass)

| Test File | Component Verified |
| :--- | :--- |
| `src/components/QuotaRing.test.tsx` | SVG radial progress ring, percentage calculations, and quota telemetry. |
| `src/components/TerminalLog.test.tsx` | Streaming execution logs, auto-scrolling, and step indicators. |
| `src/components/SignalCard.test.tsx` | Grounded signal badges, tier chips, and external citation links. |
| `src/App.test.tsx` | Main application shell, persistent tab routing, and live status bar. |
