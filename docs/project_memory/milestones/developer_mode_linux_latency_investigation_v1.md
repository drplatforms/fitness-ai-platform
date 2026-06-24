# Developer Mode Linux Latency Investigation v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Branch: `feature/developer-mode-linux-latency-investigation-v1`

## Goal

Reduce Linux Developer tab open latency without removing Linux from the validation workflow.

## Implementation summary

- Added Developer Mode render timing for the main Developer tab sections.
- Made Runtime / DB Source Verification lazy/action-driven so opening the Developer tab does not query the active database automatically.
- Preserved explicit refresh behavior for Runtime / DB diagnostics.
- Preserved Weekly Coach Summary Developer Mode preview behavior.
- Kept normal/default UI and Today behavior unchanged.

## Boundaries

- No provider runtime added.
- No Ollama/CrewAI/qwen calls added.
- No worker/queue/scheduler/polling added.
- No public/default Weekly Coach Summary display added.
- No raw rows, secrets, prompts, context, or scratchpad displayed.

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
