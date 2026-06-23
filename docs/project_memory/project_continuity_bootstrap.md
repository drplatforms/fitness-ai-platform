# Project Continuity Bootstrap

Current milestone:
Daily Coach Async Approved Preview Bridge QA v1

Status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Start here:

1. Read `docs/project_memory/project_state.json`.
2. Read `docs/project_memory/current_state.md`.
3. Read `docs/project_memory/next_milestone.md`.
4. Read `docs/project_memory/designs/daily_coach_async_approved_preview_bridge_design_v1.md`.
5. Read `docs/project_memory/milestones/daily_coach_async_approved_preview_bridge_implementation_v1.md`.
6. Read `docs/project_memory/milestones/daily_coach_async_approved_preview_bridge_qa_v1.md`.

Current boundary:

- Feature flag defaults disabled.
- Normal Today remains unchanged when disabled.
- Preview reads only approved persisted async narratives.
- Preview appears only when all gates pass.
- QA hardening tests cover disabled/enabled/gated behavior.
- No provider call occurs from Today render.
- No provider call occurs on page load.
- No async job is created from Today.
- Deterministic Daily Next Action remains primary.
- No public/default async narrative display is authorized.
- No worker / queue / scheduler / polling is authorized.
- qwen3 and qwen3:32b remain unauthorized for bridge use.

Workflow reminder:

- Use chat-driven apply scripts by default.
- Do not use Codex unless user explicitly opts in.
- Temporary apply scripts live outside the repo under `C:\projects`.
- Run apply scripts from repo root as `python ..\<script>.py`.
- Never use `git add .`.
