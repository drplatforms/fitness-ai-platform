# Project Continuity Bootstrap

Current milestone:
Weekly Coach Summary Async Service Shell / No Worker v1

Status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Start here:

1. Read `docs/project_memory/project_state.json`.
2. Read `docs/project_memory/current_state.md`.
3. Read `docs/project_memory/next_milestone.md`.
4. Read `docs/project_memory/patterns/async_job_delivery_pattern_v1.md`.
5. Read `models/weekly_coach_summary_models.py`.
6. Read `services/weekly_coach_summary_service.py`.
7. Run or inspect `tools/dev_weekly_coach_summary_preview.py`.
8. Read `docs/project_memory/milestones/weekly_coach_summary_async_service_shell_no_worker_v1.md`.
9. Read `docs/project_memory/reviews/weekly_coach_summary_async_service_shell_no_worker_v1.md`.

Current boundary:

- Weekly Coach Summary is the selected next async job candidate.
- Contracts/data model are accepted foundation.
- Deterministic service shell now generates a readable `ApprovedWeeklyCoachSummary` from bounded fixture inputs.
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
