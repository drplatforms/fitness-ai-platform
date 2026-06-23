# Project Continuity Bootstrap

Current milestone:
Weekly Coach Summary Async Contracts + Data Model v1

Status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Start here:

1. Read `docs/project_memory/project_state.json`.
2. Read `docs/project_memory/current_state.md`.
3. Read `docs/project_memory/next_milestone.md`.
4. Read `docs/project_memory/patterns/async_job_delivery_pattern_v1.md`.
5. Read `models/weekly_coach_summary_models.py`.
6. Read `docs/project_memory/milestones/weekly_coach_summary_async_contracts_data_model_v1.md`.
7. Read `docs/project_memory/reviews/weekly_coach_summary_async_contracts_data_model_v1.md`.

Current boundary:

- Weekly Coach Summary is the selected next async job candidate.
- This milestone defines contracts/data model only.
- Deterministic-first posture is required.
- Provider runtime is deferred.
- Persistence schema/service is deferred.
- Developer Mode inspection is a later required stage before normal UI exposure.
- No normal Today behavior changed.
- No Streamlit UI changed.
- No provider behavior changed.

Workflow reminder:

- Use chat-driven apply scripts by default.
- Do not use Codex unless user explicitly opts in.
- Temporary apply scripts live outside the repo under `C:\projects`.
- Run apply scripts from repo root as `python ..\<script>.py`.
- Never use `git add .`.
