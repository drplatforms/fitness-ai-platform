# Project Continuity Bootstrap

Current milestone:
Async Job Delivery Pattern / Playbook v1

Status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Start here:

1. Read `docs/project_memory/project_state.json`.
2. Read `docs/project_memory/current_state.md`.
3. Read `docs/project_memory/next_milestone.md`.
4. Read `docs/project_memory/patterns/async_job_delivery_pattern_v1.md`.
5. Read `docs/project_memory/milestones/async_job_delivery_pattern_playbook_v1.md`.
6. Read `docs/project_memory/reviews/async_job_delivery_pattern_playbook_v1.md`.

Current boundary:

- This is a docs/pattern milestone.
- No runtime behavior changed.
- No provider behavior changed.
- No normal Today behavior changed.
- No Streamlit behavior changed.
- No new async job implemented.
- The playbook should be used before scoping future async jobs.
- lstop/lrestart/app CRLF handling is backlog only.
- lstop/lrestart/app are Windows PowerShell helper commands that SSH into Linux; do not present them as Linux bash commands.

Workflow reminder:

- Use chat-driven apply scripts by default.
- Do not use Codex unless user explicitly opts in.
- Temporary apply scripts live outside the repo under `C:\projects`.
- Run apply scripts from repo root as `python ..\<script>.py`.
- Never use `git add .`.
