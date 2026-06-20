# Development Workflow

Last updated: 2026-06-19

## Purpose

This document defines the local development, validation, restart, sync, and snapshot workflow for the AI Health Coach repo.

It exists to reduce noisy commits, accidental staging, stale context, and runtime confusion while preserving the backend-truth-first architecture.

## Default Windows project path

Windows is the source-of-truth development machine.

```powershell
cd C:\projects\fitness_ai
```

Patch and snapshot files are normally downloaded to this project root.

## Windows vs Linux responsibility split

Windows owns source-of-truth repo work:

- `git status`
- patch apply
- source edits
- docs edits
- local validation
- `git add`, `git commit`, and `git push`
- post-merge snapshots with `git archive`

Linux owns runtime/staging QA:

- FastAPI runtime smoke tests
- Streamlit runtime QA
- SQLite persisted-history inspection
- Ollama-connected provider-lane QA

Do not commit separately from Linux unless that workflow is explicitly planned.

GitHub remains the shared source of truth.

## Local artifact clutter

Patch, snapshot, and temporary review artifacts should not be staged.

Recommended local-only ignores belong in:

```text
.git/info/exclude
```

Recommended local entries:

```text
# Local AI handoff / patch artifacts
*.patch
*.zip
artifacts/
qa_artifacts/
_backup_before_*/
_patched_*/
patch_check_output.txt
```

Do not add a broad `handoffs/` ignore that hides `docs/project_memory/handoffs/`.
Those project-memory handoff files are intentionally tracked.

## Before applying a patch

```powershell
cd C:\projects\fitness_ai

git status --short
git log --oneline -5
```

Clean unrelated drift before applying feature work.
Do not stage patch files, zip files, temporary artifacts, local DB copies, or runtime outputs.

## Applying a patch from project root

Most project patches should apply from project root with:

```powershell
cd C:\projects\fitness_ai

git apply --check .\some_patch.patch
git apply .\some_patch.patch
```

If a patch was generated with `/mnt/data/...` paths, use the strip level provided with that patch.
Do not guess. Run `Get-Content .\some_patch.patch -TotalCount 8` and inspect the paths before applying.

## Commit validation helper

Use the Windows helper:

```powershell
cd C:\projects\fitness_ai

powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode docs-only
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode full
```

### Mode: docs-only

Use for project-memory, handoff, ADR, review, and documentation-only milestones.

Runs:

- `git diff --check`
- required `docs/project_memory` file checks
- `git status --short`

Does not run Ruff, Black, or Pytest.

### Mode: code

Use for normal code/tooling milestones.

Runs:

- `git diff --check`
- Ruff on changed Python files only, when possible
- Black on changed Python files only, when possible
- focused safety tests
- `git status --short`

This mode intentionally avoids `black .` by default to prevent unrelated reformatting.

### Mode: full

Use for larger milestones, release-style checks, or when Architecture/QA asks for full validation.

Runs:

- `git diff --check`
- `ruff check . --fix`
- `black .`
- `pytest -q`
- `git status --short`

Use this intentionally. Clean drift first.

## Project-memory checks

Use Dev Assistant commands:

```powershell
.\.venv\Scripts\python.exe tools\dev_assistant.py memory-check
.\.venv\Scripts\python.exe tools\dev_assistant.py stale-doc-check
```

The checks are read-only. They verify required project-memory docs and flag obvious stale/conflicting workflow statements.

## Session brief command

Use Dev Assistant to generate a clean UTF-8 uploadable handoff brief without PowerShell transcript or Tee-Object encoding issues.

```powershell
cd C:\projects\fitness_ai

python tools/dev_assistant.py session-brief --out qa_artifacts/session_brief.txt
```

Optional milestone label:

```powershell
python tools/dev_assistant.py session-brief --out qa_artifacts/session_brief.txt --milestone "<milestone>"
```

The generated brief includes:

- project name and generated timestamp
- current branch and latest commit
- git status --short
- recent commits
- Dev Assistant status summary
- memory-check output
- stale-doc-check output
- suggested next action
- snapshot command
- Linux sync reminder

The output belongs under `qa_artifacts/` and must not be committed.

Do not use session briefs as source of truth. They are uploadable convenience context only. Project memory docs and git history remain source of truth.


## Catalog import staging workflow

Use deterministic catalog import tools for local candidate data review. These tools create staged artifacts only and do not mutate canonical catalogs.

Food candidate import:

```powershell
python tools/import_food_catalog.py --input path\to\food.csv --out-dir qa_artifacts\catalog_import_v1\food
```

Exercise candidate import:

```powershell
python tools/import_exercise_catalog.py --input path\to\exercises.csv --out-dir qa_artifacts\catalog_import_v1\exercise
```

Expected outputs include staged CSV rows, a Markdown report, and JSON findings. Generated artifacts belong under `qa_artifacts/` and must not be committed.

Important boundaries:

- staged rows are candidates only
- no staged row is production-approved
- no importer automatically merges into canonical catalogs
- no scraping, external APIs, AI/provider calls, Aider, Headroom, or Claude workflow are required
- human review is required before any future canonical catalog merge

## Snapshot command

Use `git archive`, not `Compress-Archive`.

```powershell
$commit = git rev-parse --short HEAD
$date = Get-Date -Format "yyyy-MM-dd"
$commitMessage = git log -1 --pretty=%s

$safeMessage = $commitMessage -replace '[^a-zA-Z0-9]+', '-'
$safeMessage = $safeMessage.ToLower().Trim('-')

$zipName = "..\fitness_ai_snapshot_${date}_${commit}_${safeMessage}.zip"

git archive --format=zip --output=$zipName HEAD

Write-Host "Created snapshot:"
Write-Host $zipName

Get-Item $zipName
```

Immediately after snapshot, sync Linux:

```bash
cd ~/projects/fitness-ai-platform

git fetch origin
git switch main
git pull --ff-only origin main

git status -sb
git log --oneline -5
```

For feature branches, replace `main` with the feature branch name.

## Windows to Linux branch sync

Windows after commit/push:

```powershell
git push -u origin <branch-name>
```

Linux:

```bash
cd ~/projects/fitness-ai-platform

git fetch origin
git switch <branch-name> || git switch --track origin/<branch-name>
git pull --ff-only origin <branch-name>

git status -sb
git log --oneline -5
```

## Deterministic-safe FastAPI restart with Windows Ollama connectivity

FastAPI and Streamlit may run on Linux while Ollama runs on Windows.

Use `OLLAMA_BASE_URL` so manual Developer Mode provider lanes can reach Windows Ollama.
This does not enable provider behavior by default.

Deterministic-safe restart:

```bash
cd ~/projects/fitness-ai-platform

unset RECOMMENDATION_CANDIDATE_PROVIDER
unset NUTRITION_EXPLANATION_PROVIDER
export OLLAMA_BASE_URL=http://<WINDOWS_IP>:11434

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Provider-selection env vars should remain unset unless intentionally testing provider defaults.

Connectivity check from Linux:

```bash
curl -s http://<WINDOWS_IP>:11434/api/tags | head
```

Daily Coach Narrative provider-lane smoke test:

```bash
curl -s "http://127.0.0.1:8000/daily-coach/102/narrative-preview/debug?provider=direct_ollama&model=qwen3:8b&date=2026-06-19&timeout_seconds=180" | python -m json.tool
```

## Streamlit restart

If port 8501 is occupied, use 8502:

```bash
cd ~/projects/fitness-ai-platform

streamlit run ui/streamlit_app.py --server.address 0.0.0.0 --server.port 8502
```

## Current product safety reminders

- Backend owns truth.
- AI explains approved truth only.
- Validators enforce reality.
- Deterministic fallback remains default.
- Provider lanes remain manual/opt-in/debug unless explicitly promoted.
- `direct_ollama` remains opt-in/manual for Daily Coach Narrative developer preview lanes.
- qwen3 remains evaluation-only, not production-approved.
- Normal Today UI narrative integration remains separate future work.
- Do not add Claude-specific workflow files or commands.
