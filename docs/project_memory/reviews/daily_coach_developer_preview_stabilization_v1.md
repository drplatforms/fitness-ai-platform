# Daily Coach Developer Preview Stabilization v1 Review

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW.

Architecture requested a stabilization pass after the same-session approval branch became unstable during runtime smoke. This implementation starts from accepted `main` and does not include any same-session approval behavior.

Acceptance checks for Architecture / QA:

- `Coach’s Read for Today` / Daily Coach Synthesis remains in the Today UI before Daily Grounded Recommendation
- `/daily-coach/{user_id}/synthesis` route returns a deterministic safe wrapper
- Developer Preview diagnostics render without mixed-type PyArrow failures
- narrative preview debug route returns stable sanitized diagnostics under `daily_coach_narrative_preview.developer_diagnostics`
- normal Today Coach Note continues to use only `/daily-coach/{user_id}/today-card`
- no same-session approval controls exist
- normal Today UI does not show provider/model/debug internals
- provider preview remains manual and Developer Mode-only

Manual QA still required:

- Windows FastAPI startup smoke
- Windows Streamlit startup smoke
- Linux import/startup smoke
- QA 102 Today smoke
- Developer Mode narrative preview diagnostics smoke
- provider-preview route manual smoke if Ollama is available

Boundary confirmation:

- no same-session approval
- no provider call on normal Today load
- no provider/model promotion
- no provider defaults changed
- no persistence/schema/report changes
- no Daily Next Action changes
- no nutrition/workout/catalog changes
- no raw/rejected provider output in normal UI
