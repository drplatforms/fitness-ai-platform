# Local Developer Command Menu

Status: `LOCAL_COMMAND_MENU_APP_LINUX_RUNTIME_CORRECTION_V1_ACCEPTED`

AI Health Coach helper commands are repo-owned developer tooling.

Command definitions live in:

`C:\projects\fitness_ai\scripts\fitness_commands.ps1`

Repo-relative path: `scripts/fitness_commands.ps1`

The PowerShell profile should only dot-source the repo script. Project command logic should not live only in a hidden user profile.

## Install or reload

Manual reload:

```powershell
. "C:\projects\fitness_ai\scripts\fitness_commands.ps1"
fitness
```

Optional profile installer:

```powershell
cd C:\projects\fitness_ai
.\scripts\install_fitness_commands_profile.ps1
. $PROFILE
fitness
```

The installer backs up the current PowerShell profile, appends a guarded dot-source block if missing, and does not overwrite existing profile content.

Expected profile block:

```powershell
# AI Health Coach command menu
$fitnessCommands = "C:\projects\fitness_ai\scripts\fitness_commands.ps1"
if (Test-Path $fitnessCommands) {
    . $fitnessCommands
}
```

## Configuration defaults

Defaults match current project usage:

- Windows source repo: `C:\projects\fitness_ai`
- Linux mirror repo: `~/projects/fitness-ai-platform`
- Linux SSH target: `dusty@itsAlwaysDNS`
- Canonical app runtime: Linux FastAPI + Streamlit launched over SSH with `app` / `lrestart`
- Windows-local FastAPI escape hatch: `http://127.0.0.1:8000` through `wapp`
- Windows-local Streamlit escape hatch: `http://127.0.0.1:8510` through `wapp`
- Windows Ollama: `http://127.0.0.1:11434`
- Linux runtime reaches Windows Ollama with `OLLAMA_BASE_URL=http://192.168.1.104:11434`
- Linux Streamlit URL opened by Windows command menu: `FITNESS_LINUX_STREAMLIT_URL` override or default host parsed from `FITNESS_LINUX_SSH` with Linux Streamlit port `8501`

Supported environment variable overrides:

- `FITNESS_WINDOWS_REPO`
- `FITNESS_LINUX_REPO`
- `FITNESS_LINUX_SSH`
- `FITNESS_WINDOWS_OLLAMA_URL`
- `FITNESS_LINUX_OLLAMA_URL`
- `FITNESS_FASTAPI_PORT`
- `FITNESS_STREAMLIT_PORT`
- `FITNESS_LINUX_STREAMLIT_PORT`
- `FITNESS_LINUX_STREAMLIT_URL`

## Command list

Daily commands preserved:

- `fitness` — show the AI Health Coach command menu.
- `cdf` — go to the Windows project root.
- `gsync` / `fpull` — fetch, switch to `main`, fast-forward pull, show status/log.
- `gstate` — show branch, status, latest commit, tracking, and untracked files.
- `gcheck` — run common validation including project-memory checks.
- `gacp` — commit already-staged files and push the current branch; does not auto-stage and refuses `main` unless explicitly allowed.
- `app` — canonical app launcher; restarts Linux FastAPI + Streamlit through SSH and opens the Linux-hosted Streamlit URL from Windows.
- `wapp` — explicit Windows-local developer launcher; preserves the old local FastAPI/Streamlit behavior and is not the canonical runtime.

Windows workflow commands added:

- `fsnap` — create standard git archive snapshot outside the repo.
- `fbranch <branch>` — create a feature branch from clean `origin/main`.
- `fmerge <branch> <accepted-final-commit>` — merge with `git merge-base --is-ancestor` safety verification.
- `fsweep` — run artifact/citation contamination sweep.
- `fmem` — run project-memory checks.
- `fports` — show Windows-side listeners for ports `8000`, `8501`, `8510`, and `11434` only; use `lstatus` for Linux app health.
- `fkill` — stop local FastAPI/Streamlit project processes tied to this repo or configured ports.
- `fdoctor` — run local environment sanity checks.

Linux commands preserved and refreshed:

- `lstatus` — show Linux repo, app, port, and DB status.
- `lsetup` — pull Linux `main` and install requirements.
- `lpull` — pull Linux `main` only, no restart.
- `lvalidate` — run Linux project-memory validation.
- `lollama` — verify Linux can reach Windows Ollama; does not start Linux Ollama.

Linux command hotfix note: `lstatus`, `lpull`, and `lollama` were smoke-tested after the initial repo-owned command-menu patch exposed fragile Bash payload formatting. `lstatus` now uses safe `printf` labels and DB file checks without escaped Bash parentheses; `lpull` uses `git log -5 --oneline --decorate`; `lollama` uses `printf` instead of a literal `\n` suffix.
- `lstop` — stop project FastAPI/Streamlit processes only.
- `lrestart` — restart canonical Linux FastAPI/Streamlit runtime with Windows Ollama URL.
- `lupdate` — pull Linux `main` and restart the app.
- `lsh` — SSH into Linux project with `.venv` active.

## Local Command Menu App Runtime Correction v1

`app` is now the canonical Linux runtime launcher.

Accepted runtime split:

- Windows owns source-of-truth repo control and hosts Ollama.
- Linux is the canonical FastAPI + Streamlit app runtime.
- Linux runtime uses Windows Ollama through `OLLAMA_BASE_URL=http://192.168.1.104:11434`.
- Windows-local app startup remains available only through the explicit `wapp` escape hatch.

Command semantics:

- `app` calls the Linux restart path and opens the Linux-hosted Streamlit URL from Windows.
- `app` must not launch Windows-local `uvicorn` or Windows-local Streamlit shells.
- `wapp` is explicitly labeled Windows-local and may launch local Windows FastAPI/Streamlit for developer-only escape-hatch use.
- `fports` reports Windows-side ports only.
- `lstatus` reports Linux-side Git/app/process/port status.

## Safety boundaries

- Commands are developer tooling only.
- Commands do not change FastAPI, Streamlit, provider, database, persistence, report, nutrition, workout, catalog, or model behavior.
- `app` is Linux-canonical; `wapp` is the explicit Windows-local escape hatch.
- `gacp` does not auto-stage files.
- `fbranch` refuses a dirty working tree.
- `fmerge` must verify the accepted final feature commit is an ancestor of `main` before push/snapshot/Linux pull.
- `fsnap` creates snapshots outside the repo and does not stage them.
- Linux commands use Windows Ollama by default and do not assume Ollama runs on Linux.
- Profile installation is additive and backed up; it must not overwrite user profile content.

## Linux tmux runtime correction

The canonical Linux runtime launcher follows `docs/fitness_ai_dev_cheatsheet.md` section `Linux Runtime With tmux`.

Runtime process ownership:

- `lrestart` starts `fitness-api` and `fitness-ui` tmux sessions on Linux.
- `lstop` kills those tmux sessions and project FastAPI/Streamlit processes.
- Linux FastAPI listens on port `8000`.
- Linux Streamlit listens on port `8501` by default.
- Windows-local Streamlit remains on port `8510` through `wapp` only.
- `app` opens the Linux-hosted Streamlit URL, defaulting to `http://<linux-host>:8501`.

Do not replace the Linux tmux runtime with Windows-local shells or Linux `nohup` background processes unless a future DevOps milestone explicitly changes the runtime architecture.
