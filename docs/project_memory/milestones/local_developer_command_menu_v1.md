# Local Developer Command Menu Audit + Repo-Owned Commands v1

Status: `IMPLEMENTED / READY FOR ARCHITECTURE REVIEW`

Branch: `feature/local-developer-command-menu-v1`

## Goal

Move the AI Health Coach local helper command menu from hidden PowerShell-profile logic into repo-owned, version-controlled tooling.

## Implemented

- Added `scripts/fitness_commands.ps1` as the repo-owned command menu.
- Added `scripts/install_fitness_commands_profile.ps1` as an optional guarded profile installer.
- Added `docs/project_memory/local_developer_command_menu.md` as the command source-of-truth doc.
- Preserved existing commands: `fitness`, `cdf`, `gsync`, `gstate`, `gcheck`, `gacp`, `app`, `lupdate`, `lstatus`, `lsetup`, `lrestart`, `lstop`, and `lsh`.
- Added safety/workflow commands: `fsnap`, `fpull`, `fbranch`, `fmerge`, `fsweep`, `fmem`, `fports`, `fkill`, `fdoctor`, `lpull`, `lvalidate`, and `lollama`.
- Encoded Windows repo, Linux mirror, Windows Ollama, Linux-to-Windows Ollama, FastAPI, Streamlit, and SSH defaults with environment variable overrides.
- Added static tests for command presence, required paths/URLs, menu content, install guidance, and artifact/secret avoidance.

## Boundaries

Docs/tooling/local command changes only.

Required phrase: docs/tooling/local command changes only.

Not changed:

- FastAPI runtime behavior
- Streamlit app behavior
- provider behavior
- database/schema
- persistence/report behavior
- Daily Next Action logic
- nutrition/workout/catalog logic
- same-session bridge behavior
- qwen model eligibility
- model/provider defaults
