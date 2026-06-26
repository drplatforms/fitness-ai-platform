# Next Milestone

Current milestone in progress: Workout Generation Sizing + Persistence Stabilization v1.

Acceptance is blocked until:

- Quick returns 3-4 exercises when valid.
- Standard returns 4-5 exercises when valid.
- Full returns 6-7 exercises when valid.
- Standard and Full do not silently collapse to the same 4-exercise output.
- `Show different exercises` changes only unselected previews and preserves size intent.
- Selected workout persists the exact visible exercise list after refresh/rerun.
- Active Workout loads the persisted selected/active workout exactly after refresh/rerun.
- Today does not duplicate the full workout selection flow.
- Linux smoke is green.
- Browser smoke is green.
- Feature snapshot is created only after final smoke is green.

After acceptance, recommended next milestones:

- Exercise Catalog Utilization / Specialized Movement Coverage v1, rebuilt cleanly after sizing and persistence are stable.
- Streamlit Workout Save/Selection Latency Investigation v2, measured separately from this stabilization work.
- Workout Selected Replacement Flow Design v1, only if an explicit user-approved replacement flow is desired.
- Provider Data Access Audit / Cross-Domain Context Map v1, before broader provider voice work.

Still deferred:

- broad catalog utilization across all 200+ exercises
- AI/provider workout generation
- CrewAI/Ollama/OpenAI/PydanticAI/LangGraph workout generation
- worker / queue / scheduler / polling
- Daily Narrative behavior changes
- Weekly Summary behavior changes
- Streamlit latency optimization
