# Architecture Handoff — Weekly Coach Summary Persistence Latency Investigation v1

Recipient: Architecture

Project: AI Health Coach / fitness_ai

Milestone: Weekly Coach Summary Persistence Latency Investigation v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: WEEKLY_COACH_SUMMARY_PERSISTENCE_LATENCY_INVESTIGATION_V1_ACCEPTED

Summary:
The Weekly Coach Summary Developer Mode persistence latency was strongly narrowed to Streamlit full-app rerun behavior. The Developer Mode panel now uses Streamlit fragment reruns when available, adds Developer Mode-only timing diagnostics, and includes a CLI latency probe for the backend deterministic path.

Boundaries:
- Developer Mode-only behavior preserved
- normal/default UI unchanged
- normal Today unchanged
- no public/default display
- no provider runtime
- no Ollama/CrewAI/qwen call
- no automatic generation
- no worker/queue/scheduler/polling
- no persistence safety weakening
