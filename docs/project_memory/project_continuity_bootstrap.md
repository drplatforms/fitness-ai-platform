# Project Continuity Bootstrap

Current milestone:
Weekly Coach Summary Persistence Latency Investigation v1

Status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Start here:

1. Read `docs/project_memory/project_state.json`.
2. Read `docs/project_memory/current_state.md`.
3. Read `docs/project_memory/next_milestone.md`.
4. Read `ui/streamlit_app.py` weekly coach summary Developer Mode panel.
5. Read `tools/dev_weekly_coach_summary_latency_probe.py`.
6. Read `services/weekly_coach_summary_persistence_service.py`.
7. Run `python tools/dev_weekly_coach_summary_latency_probe.py`.

Current boundary:

- Weekly Coach Summary persistence is Developer Mode-only.
- Approved/public-safe summaries and deterministic fallback summaries can be saved and loaded.
- Latency was narrowed to Streamlit full-app rerun behavior.
- The Developer Mode panel uses Streamlit fragment reruns when available.
- Timing diagnostics remain Developer Mode-only.
- No provider runtime, public/default display, normal Today integration, automatic generation, worker, queue, scheduler, or polling is authorized.

Workflow reminder:

- Use chat-driven apply scripts by default.
- Do not use Codex unless the user explicitly opts in.
- Temporary apply scripts live outside the repo under `C:\projects`.
- Run apply scripts from repo root as `python ..\<script>.py`.
- Never use `git add .`.
