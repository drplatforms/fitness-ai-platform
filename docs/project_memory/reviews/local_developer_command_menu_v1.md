# Local Developer Command Menu Audit + Repo-Owned Commands v1 Review

Status: `LOCAL_DEVELOPER_COMMAND_MENU_V1_HOTFIXED_READY_FOR_ARCHITECTURE_REVIEW`

Proposed final status: `LOCAL_DEVELOPER_COMMAND_MENU_V1_ACCEPTED`

## Review summary

The local command menu is now repo-owned in `scripts/fitness_commands.ps1` with optional profile installation through `scripts/install_fitness_commands_profile.ps1`.

The profile is expected to become a thin loader only. Command behavior should be maintained through git instead of hidden local profile edits.

## Commands implemented

Preserved/fixed:

- `fitness`
- `cdf`
- `gsync`
- `gstate`
- `gcheck`
- `gacp`
- `app`
- `lupdate`
- `lstatus`
- `lsetup`
- `lrestart`
- `lstop`
- `lsh`

Added:

- `fsnap`
- `fpull`
- `fbranch`
- `fmerge`
- `fsweep`
- `fmem`
- `fports`
- `fkill`
- `fdoctor`
- `lpull`
- `lvalidate`
- `lollama`

## Safety checks

- `gacp` refuses to commit when nothing is staged and does not auto-stage all files.
- `gacp` refuses `main` by default.
- `fbranch` starts from clean `origin/main` and refuses dirty working trees.
- `fmerge` requires `git merge-base --is-ancestor <accepted-final-feature-commit> main` after merge.
- `app` uses Windows Ollama at `http://127.0.0.1:11434` and Windows Streamlit port `8510`.
- Linux commands use `OLLAMA_BASE_URL=http://192.168.1.104:11434` and do not assume Linux Ollama.
- Profile installer backs up the profile and avoids duplicate dot-source blocks.


## Hotfix review note

Manual command smoke found three pre-acceptance issues and the hotfix addresses them:

- `lstatus` now avoids fragile escaped Bash parentheses for DB file discovery.
- `lpull` now uses `git log -5 --oneline --decorate`.
- `lollama` now uses `printf` lines and does not emit a literal `\n`.

This hotfix is limited to scripts/docs/tests and does not change application runtime/provider/UI behavior.

## Validation expectation

- `git diff --check`
- `scripts/dev_commit_check.ps1 -Mode code`
- `pytest tests/test_local_developer_command_menu_v1.py -q`
- `pytest tests/test_project_memory_check.py -q`
- PowerShell load smoke: `powershell -NoProfile -ExecutionPolicy Bypass -Command ". .\scripts\fitness_commands.ps1; fitness"`
- Linux command smoke: `lstatus`, `lpull`, and `lollama`
- `python tools/dev_assistant.py memory-check`
- `python tools/dev_assistant.py stale-doc-check`
- artifact sweep clean

## Boundary confirmation

- Docs/tooling/local command changes only.
- No runtime behavior changed.
- No provider behavior changed.
- No Streamlit app behavior changed.
- No FastAPI route changes.
- No database/schema changes.
- No persistence/report changes.
- No model/provider default changes.
- No same-session bridge behavior changes.
- No qwen model eligibility changes.
- No qa_artifacts committed.
- No snapshots committed.
- No secrets committed.
