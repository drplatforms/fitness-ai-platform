
# Project Continuity Bootstrap

Current milestone:
Next Async Job Candidate Selection v1 + lstop Tooling Hotfix

Status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Start here:

1. Read `docs/project_memory/project_state.json`.
2. Read `docs/project_memory/current_state.md`.
3. Read `docs/project_memory/next_milestone.md`.
4. Read `docs/project_memory/patterns/async_job_delivery_pattern_v1.md`.
5. Read `docs/project_memory/reviews/next_async_job_candidate_selection_v1.md`.
6. Read `docs/project_memory/milestones/next_async_job_candidate_selection_v1.md`.

Current boundary:

- This is a tooling hotfix plus planning/project-memory milestone.
- `lstop` CRLF SSH command handling was fixed through LF-normalized command transport.
- `app` and `lrestart` remain Windows PowerShell helpers that SSH into Linux.
- Weekly Coach Summary Async Job is selected as the next candidate.
- No selected async job was implemented.
- No runtime product behavior changed.
- No provider behavior changed.
- No Streamlit behavior changed.
- No normal Today behavior changed.

Workflow reminder:

- Use chat-driven apply scripts by default.
- Do not use Codex unless user explicitly opts in.
- Temporary apply scripts live outside the repo under `C:\projects`.
- Run apply scripts from repo root as `python ..\<script>.py`.
- Never use `git add .`.
