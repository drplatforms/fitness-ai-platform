# Architecture Handoff Current

Updated: 2026-06-21
Current milestone: Local Command Menu App Runtime Correction v1
Owner: DevOps & Tooling / Backend Development
Status: Implemented / ready for Architecture review

## Architecture Review Target

This hotfix corrects repo-owned command menu runtime semantics.

`app` is now the canonical Linux runtime launcher. It restarts Linux FastAPI + Streamlit through SSH and opens the Linux-hosted Streamlit URL from Windows.

The previous Windows-local launcher behavior is preserved only under `wapp`.

## Accepted Runtime Split

- Windows is the source-of-truth development/control machine.
- Windows hosts Ollama.
- Linux is the canonical FastAPI + Streamlit app runtime.
- Linux runtime uses Windows Ollama through `OLLAMA_BASE_URL=http://192.168.1.104:11434`.

## Boundary

This hotfix changes command-wrapper behavior, docs, and tests only.

It does not change FastAPI routes, Streamlit UI behavior, provider behavior, database schema, async Daily Coach architecture/contracts, model policy, Ollama hosting, or Linux service architecture.

## Review Focus

- `app` does not launch Windows-local `uvicorn` or Streamlit shells.
- `app` uses Linux restart behavior.
- `wapp` exists as the explicit Windows-local escape hatch.
- `fitness` menu labels distinguish Linux canonical runtime from Windows-local runtime.
- `fports` is labeled Windows-side only.
- Docs/project memory reflect Linux as canonical app runtime.

## Proposed Acceptance

LOCAL_COMMAND_MENU_APP_LINUX_RUNTIME_HOTFIX_V1_ACCEPTED


## Linux tmux runtime correction

- `app` / `lrestart` use Linux tmux sessions `fitness-api` and `fitness-ui`.
- Linux FastAPI uses port `8000`.
- Linux Streamlit uses port `8501`.
- Windows-local Streamlit remains port `8510` through `wapp` only.
- Do not replace this with `nohup` or Windows-local app shells.
