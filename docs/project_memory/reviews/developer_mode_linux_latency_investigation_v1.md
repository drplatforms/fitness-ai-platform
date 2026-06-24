# Developer Mode Linux Latency Investigation v1 review

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Branch: `feature/developer-mode-linux-latency-investigation-v1`

Commit: `<pending commit>`

## Review notes

This milestone investigates and reduces Linux Developer tab latency by removing eager Runtime / DB diagnostic execution from Developer tab open and adding safe Developer Mode timing instrumentation.

## Manual Linux smoke required

- Pull feature branch on Linux.
- Restart Streamlit/FastAPI because Streamlit behavior changed.
- Open Developer tab and measure approximate open time.
- Refresh Runtime / DB diagnostics.
- Confirm QA/debug controls still work.
- Confirm no raw rows, secrets, stack traces, provider output, prompts, context, or scratchpad are displayed.

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
