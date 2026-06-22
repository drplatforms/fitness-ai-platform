# Backend Handoff Current

Updated: 2026-06-21
Current milestone: Local Command Menu App Runtime Correction v1
Backend role: Command-wrapper hotfix / awaiting Architecture review

## Backend Summary

The repo-owned PowerShell command menu now launches the canonical app runtime on Linux by default.

Implemented behavior:

- `app` restarts Linux FastAPI + Streamlit through SSH.
- `app` opens the configured Linux-hosted Streamlit URL from Windows.
- `wapp` preserves explicit Windows-local FastAPI + Streamlit launcher behavior.
- `lrestart` remains the Linux restart path and exports the Linux runtime `OLLAMA_BASE_URL` pointing to Windows Ollama.
- `fports` is labeled Windows-side port visibility only.

## Boundary

No backend app runtime code changed.

This hotfix does not change FastAPI routes, Streamlit UI, provider behavior, database schema, async Daily Coach contracts, model policy, persistence, or Linux service architecture.

## Validation Focus

Run command-menu tests and project-memory checks. Manual smoke should confirm `fitness` menu wording and, if practical, `app`, `lstatus`, and `wapp` semantics.


## Linux tmux runtime correction

- `app` / `lrestart` use Linux tmux sessions `fitness-api` and `fitness-ui`.
- Linux FastAPI uses port `8000`.
- Linux Streamlit uses port `8501`.
- Windows-local Streamlit remains port `8510` through `wapp` only.
- Do not replace this with `nohup` or Windows-local app shells.
