# Next Milestone

Current milestone in progress: Workout Preview Full-Slot Rotation v1.

Acceptance is blocked until:

- Refreshed previews attempt to change every exercise slot when safe alternatives exist.
- If a slot repeats, there is a legitimate movement/equipment/safety constraint reason.
- Quick remains 3-4 exercises when valid.
- Standard remains 4-5 exercises when valid.
- Full remains 6-7 exercises when valid.
- Standard and Full do not silently collapse to the same 4-exercise output.
- `Show different exercises` changes only unselected previews and preserves size intent.
- Selected workout persists the exact visible exercise list after refresh/rerun.
- Active Workout loads the persisted selected/active workout exactly after refresh/rerun.
- Today does not duplicate the full workout selection flow.
- Linux smoke is green.
- Browser smoke is green.
- Feature snapshot is created only after final smoke is green.

After acceptance, recommended next milestones:

- Exercise Catalog Utilization / Specialized Movement Coverage v2, rebuilt cleanly after preview rotation and persistence are stable.
- Streamlit Workout Save/Selection Latency Investigation v2, measured separately from preview rotation work.
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
