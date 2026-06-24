# Current implementation update - Developer Mode Linux Latency Investigation v1

Developer Mode Linux Latency Investigation v1 is implemented on `feature/developer-mode-linux-latency-investigation-v1`.

Runtime / DB Source Verification v1 and QA Seed Data Verification CLI v1 are accepted prerequisites. This milestone keeps Linux in the validation workflow while reducing Developer tab latency by avoiding eager diagnostic DB queries on tab open and adding safe Developer Mode timing instrumentation.

Normal/default UI and Today behavior are unchanged. Provider runtime, Ollama, CrewAI, qwen, worker/queue/scheduler/polling, automatic generation, public/default Weekly Coach Summary display, and raw debug leakage remain out of scope.

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

## Current implementation update - Top-Level Streamlit Lazy Navigation v1

Top-Level Streamlit Lazy Navigation v1 is implemented on `feature/top-level-streamlit-lazy-navigation-v1`.

This milestone addresses Linux runtime latency caused by Streamlit eager top-level tab rendering. Developer Mode itself remains fast; the top-level navigation now renders only the selected page body so Developer does not wait for Workout and History cold renders.

Weekly Coach Summary QA Date Range Debug v2 is paused until this prerequisite navigation fix is accepted. Provider runtime, Ollama, CrewAI, qwen, workers, queues, schedulers, automatic generation, schema changes, and public/raw debug leakage remain out of scope.
