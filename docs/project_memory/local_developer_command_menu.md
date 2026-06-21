# Local Developer Command Menu

Status: `LOCAL_DEVELOPER_COMMAND_MENU_V1_IMPLEMENTED_FOR_REVIEW`

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
- Windows FastAPI: `http://127.0.0.1:8000`
- Windows Streamlit: `http://127.0.0.1:8510`
- Windows Ollama: `http://127.0.0.1:11434`
- Linux runtime reaches Windows Ollama with `OLLAMA_BASE_URL=http://192.168.1.104:11434`

Supported environment variable overrides:

- `FITNESS_WINDOWS_REPO`
- `FITNESS_LINUX_REPO`
- `FITNESS_LINUX_SSH`
- `FITNESS_WINDOWS_OLLAMA_URL`
- `FITNESS_LINUX_OLLAMA_URL`
- `FITNESS_FASTAPI_PORT`
- `FITNESS_STREAMLIT_PORT`

## Command list

Daily commands preserved:

- `fitness` — show the AI Health Coach command menu.
- `cdf` — go to the Windows project root.
- `gsync` / `fpull` — fetch, switch to `main`, fast-forward pull, show status/log.
- `gstate` — show branch, status, latest commit, tracking, and untracked files.
- `gcheck` — run common validation including project-memory checks.
- `gacp` — commit already-staged files and push the current branch; does not auto-stage and refuses `main` unless explicitly allowed.
- `app` — start Windows FastAPI and Streamlit with Windows Ollama and Streamlit port `8510`.

Windows workflow commands added:

- `fsnap` — create standard git archive snapshot outside the repo.
- `fbranch <branch>` — create a feature branch from clean `origin/main`.
- `fmerge <branch> <accepted-final-commit>` — merge with `git merge-base --is-ancestor` safety verification.
- `fsweep` — run artifact/citation contamination sweep.
- `fmem` — run project-memory checks.
- `fports` — show Windows listeners for ports `8000`, `8501`, `8510`, and `11434`.
- `fkill` — stop local FastAPI/Streamlit project processes tied to this repo or configured ports.
- `fdoctor` — run local environment sanity checks.

Linux commands preserved and refreshed:

- `lstatus` — show Linux repo, app, port, and DB status.
- `lsetup` — pull Linux `main` and install requirements.
- `lpull` — pull Linux `main` only, no restart.
- `lvalidate` — run Linux project-memory validation.
- `lollama` — verify Linux can reach Windows Ollama; does not start Linux Ollama.
- `lstop` — stop project FastAPI/Streamlit processes only.
- `lrestart` — restart Linux FastAPI/Streamlit with Windows Ollama URL.
- `lupdate` — pull Linux `main` and restart the app.
- `lsh` — SSH into Linux project with `.venv` active.

## Safety boundaries

- Commands are developer tooling only.
- Commands do not change FastAPI, Streamlit, provider, database, persistence, report, nutrition, workout, catalog, or model behavior.
- `gacp` does not auto-stage files.
- `fbranch` refuses a dirty working tree.
- `fmerge` must verify the accepted final feature commit is an ancestor of `main` before push/snapshot/Linux pull.
- `fsnap` creates snapshots outside the repo and does not stage them.
- Linux commands use Windows Ollama by default and do not assume Ollama runs on Linux.
- Profile installation is additive and backed up; it must not overwrite user profile content.
