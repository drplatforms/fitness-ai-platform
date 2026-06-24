# Next milestone

Current active milestone:
Developer Mode Linux Latency Investigation v1

Current branch:
`feature/developer-mode-linux-latency-investigation-v1`

Current status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Goal:
Reduce Linux Developer tab open latency by measuring Developer Mode render sections and making expensive diagnostics/debug work lazy/action-driven.

Recommended next milestone after acceptance:
Weekly Coach Summary QA Date Range Debug v2 Acceptance Hardening

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
