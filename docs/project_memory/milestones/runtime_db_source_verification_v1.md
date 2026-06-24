# Runtime / DB Source Verification v1

Status: IMPLEMENTED / READY FOR REVIEW

## Purpose

Add a Developer Mode-only runtime and database diagnostic so Windows, Linux, Streamlit, and FastAPI runtime identity can be verified before future QA data work resumes.

## Scope

- Added a safe runtime diagnostics service.
- Added a safe database source diagnostic.
- Added QA users 101-105 presence/count/date-bound diagnostics.
- Added a Developer Mode-only Streamlit panel named `Runtime / DB Source Verification`.
- Added an optional CLI: `python tools/dev_runtime_db_diagnostics.py`.

## Boundaries

- No Date-Range QA Debug panel reintroduced.
- No Streamlit mojibake cleanup.
- No seed data mutation.
- No provider runtime.
- No Ollama/CrewAI/qwen calls.
- No raw DB rows displayed.
- No secrets or environment dumps displayed.
