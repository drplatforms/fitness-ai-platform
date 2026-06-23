# QA Handoff Current

Milestone: Weekly Coach Summary Async Service Shell / No Worker v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

QA focus:
- Verify service builds valid weekly context from bounded fixture data.
- Verify deterministic candidate summary generation.
- Verify safe candidate approval into `ApprovedWeeklyCoachSummary`.
- Verify low-data context returns deterministic fallback.
- Verify candidate is not automatically approved.
- Verify unsafe/internal language triggers fallback.
- Verify developer preview command runs and prints readable public-safe output.
- Verify no provider runtime, Ollama/CrewAI call, DB/persistence dependency, Streamlit dependency, API endpoint, normal Today behavior, worker/queue/scheduler, or polling was added.
