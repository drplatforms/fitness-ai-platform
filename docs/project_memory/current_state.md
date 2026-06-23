# Current State

Latest accepted milestone:
Next Async Job Candidate Selection v1 + lstop Tooling Hotfix

Current milestone:
Weekly Coach Summary Async Contracts + Data Model v1

Current status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status:
WEEKLY_COACH_SUMMARY_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED

Current behavior:

- Weekly Coach Summary Async Job is the selected next async candidate.
- Weekly Coach Summary contracts/data model now exist in `models/weekly_coach_summary_models.py`.
- Contracts define lifecycle/status vocabulary, weekly period/context, candidate summary, approved/public-safe summary, sanitized runtime metadata, and a contract-only job record.
- This is deterministic-first and contract-only.
- No weekly summary generation is implemented.
- No persistence schema/migration is added.
- No API endpoint is added.
- No Streamlit UI is added.
- No provider runtime is added.
- No Ollama/CrewAI call is added.
- No worker/queue/scheduler/polling is added.
- No normal Today behavior changed.

Important docs:

- `docs/project_memory/patterns/async_job_delivery_pattern_v1.md`
- `docs/project_memory/milestones/weekly_coach_summary_async_contracts_data_model_v1.md`
- `docs/project_memory/reviews/weekly_coach_summary_async_contracts_data_model_v1.md`

Still not authorized:

- Weekly Coach Summary generation
- Weekly Coach Summary persistence schema/service
- Weekly Coach Summary Developer Mode UI
- Weekly Coach Summary provider runtime
- automatic weekly summary generation
- public/default weekly summary display
- worker / queue / scheduler / polling
- qwen3 bridge or promotion
- qwen3:32b promotion
