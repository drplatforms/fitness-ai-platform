# QA Handoff Current

Updated: 2026-06-21
Current milestone: Local Command Menu App Runtime Correction v1
QA role: Command menu runtime semantics validation

## QA Summary

This hotfix changes the repo-owned PowerShell command menu so `app` means Linux canonical app runtime, not Windows-local runtime.

## QA Focus

- `fitness` menu shows `app` as Linux FastAPI + Streamlit.
- `fitness` menu shows `wapp` as Windows-local FastAPI + Streamlit.
- `app` does not contain Windows `Start-Process powershell` launches for `uvicorn` or Streamlit.
- `wapp` preserves the explicit Windows-local launcher.
- `lrestart`, `lupdate`, `lstatus`, and `fports` still exist.
- `fports` is clearly Windows-side only.
- Linux runtime still uses Windows Ollama URL.
- No app runtime code, provider code, routes, Streamlit UI, DB schema, or async Daily Coach work changed.

## Expected Tests

- `pytest tests/test_local_developer_command_menu_v1.py -q`
- `pytest tests/test_project_memory_check.py -q`
- `python tools/dev_assistant.py memory-check`
- `python tools/dev_assistant.py stale-doc-check`
- `fsweep`

## Optional Manual Smoke

```powershell
. .\scripts\fitness_commands.ps1
fitness
app
lstatus
wapp
```


## Linux tmux runtime correction

- `app` / `lrestart` use Linux tmux sessions `fitness-api` and `fitness-ui`.
- Linux FastAPI uses port `8000`.
- Linux Streamlit uses port `8501`.
- Windows-local Streamlit remains port `8510` through `wapp` only.
- Do not replace this with `nohup` or Windows-local app shells.
