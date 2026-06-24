# Current handoff - Developer Mode Linux Latency Investigation v1

Project: AI Health Coach / fitness_ai

Branch: `feature/developer-mode-linux-latency-investigation-v1`

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Summary:
Developer Mode Linux Latency Investigation v1 adds safe Developer Mode timing and makes Runtime / DB Source Verification lazy/action-driven. Opening the Developer tab should render controls without automatically querying the database. Runtime diagnostics remain available through the explicit refresh button.

Validation focus:
- Developer tab open latency on Linux is measured before/after.
- Runtime / DB diagnostics refresh still works.
- QA seed CLI still works.
- Weekly Coach Summary Developer Mode preview still works.
- Normal/default UI remains unchanged.
- No provider/Ollama/CrewAI/qwen calls are added.

## Windows-local helper addendum

Added/hardened `wapp` as a Windows-local FastAPI + Streamlit launcher for latency comparison against the Linux canonical runtime.

- Uses repo `.venv\Scripts\python.exe` by default.
- Starts FastAPI on `127.0.0.1`.
- Starts Streamlit on `127.0.0.1`.
- Avoids SSH and Linux helper paths.
- Adds `wstatus` and `wstop` wrappers for Windows-local status/stop.
- Keeps `app` as the Linux canonical runtime launcher.

## Windows-local helper addendum repair

Repaired the Windows-local helper addendum so `wapp`, `wstatus`, and `wstop` are actually defined and listed by the command menu.

- `wapp` uses repo `.venv\Scripts\python.exe` by default.
- `wapp` starts FastAPI on `127.0.0.1`.
- `wapp` starts Streamlit on `127.0.0.1`.
- `wapp` avoids SSH and Linux helper paths.
- `wstatus` delegates to `fports`.
- `wstop` delegates to `fkill`.
- `app` remains the Linux canonical runtime launcher.
