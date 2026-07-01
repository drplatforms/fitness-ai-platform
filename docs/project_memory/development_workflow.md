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

Temporary delivery artifacts are saved outside the repo, normally in `C:\projects`, and commands are run from the repo root. Do not place temporary patches, apply scripts, changed-files zips, or snapshots inside `C:\projects\fitness_ai` unless a milestone explicitly adds a reusable repo tool.


## Architecture vs Backend patch ownership

Architecture may produce docs-only project-memory patches when the milestone is strictly documentation, state reconciliation, workflow memory, architecture plans, ADRs, reviews, or handoffs. This is a process shortcut only; it is not permission for Architecture to edit runtime behavior.

Backend Development owns implementation patches and any change touching Python services, models, API routes, Streamlit behavior, tests, database/schema behavior, provider behavior, or application tooling behavior.

The standing phase-separated command templates for Backend patch application and Architecture acceptance/merge/snapshot live in:

```text
docs/project_memory/architecture_backend_command_workflow_v1.md
```

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

Never commit, merge, or push from Linux. Linux is pull/validate/runtime QA only. All commits, merges, pushes, and accepted snapshots happen from the Windows dev box.

GitHub remains the shared source of truth.

## Snapshot requirement before docs-only patches

Architecture docs-only patches must target the latest accepted post-merge snapshot. If the user forgets to provide the latest snapshot before requesting a docs/project-memory patch, stop and request a fresh snapshot before generating the patch.

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

## Applying a patch or apply script from project root

Run patch/application commands from the repo root, but store temporary delivery artifacts outside the repo.

Default artifact location:

```text
C:\projects
```

For raw patch files:

```powershell
cd C:\projects\fitness_ai

git apply --check ..\some_patch.patch
git apply ..\some_patch.patch
```

For generated apply scripts:

```powershell
cd C:\projects\fitness_ai

python ..\apply_some_milestone.py
Remove-Item ..\apply_some_milestone.py -Force
```

Do not save temporary apply scripts in the repo root when clean-tree guards are used. An untracked repo-root script makes the tree dirty and should correctly stop the apply phase.

If a patch was generated with `/mnt/data/...` paths, use the strip level provided with that patch.
Do not guess. Run `Get-Content ..\some_patch.patch -TotalCount 8` and inspect the paths before applying.

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

## Complex Feature Development Workflow

For complex backend or user-visible features, use this workflow:

```text
diagnostic
→ failing/coverage test
→ narrow implementation
→ targeted validation
→ prior-regression validation
→ original smoke reproduction
→ project memory update
→ Architecture acceptance
```

This workflow applies especially to state, scoring, selection, persistence, provider output, routing, nutrition targets, workout generation, recommendation logic, and user-visible workflow behavior.

### Risk-based process model

Low-risk changes, such as docs updates, typo fixes, isolated helpers, small test cleanup, and non-behavioral refactors, may use normal patch and focused validation.

Medium-risk changes, such as deterministic service behavior, simple backend contracts, small UI/backend integrations, report section behavior, and bounded data model expansion, should use light diagnostic, focused test, narrow patch, regression validation, and smoke if user-visible.

High-risk changes, such as workout generation, exercise catalog selection/scoring, persistence/state behavior, nutrition targets/suggestions, AI/provider output, recommendation logic, and cross-domain coaching synthesis, require diagnostic first, failing/coverage test, narrow patch, regression validation, original smoke reproduction, Linux/browser smoke, project memory update, and Architecture acceptance.

### Bigger bites rule

Bigger milestone is okay. Bigger single patch is not okay.

Large objectives may be authorized only when internally phased. Single patches stay narrow.

### Patch stacking stop conditions

Backend must stop and return to Architecture if the same bug survives two implementation patches, tests pass but browser smoke fails, Linux smoke fails after Windows green, candidate pools/data shape are unclear, implementation needs broader scope than approved, file-change budget is exceeded, persistence/state becomes unstable, patch drift blocks an obvious next step, the branch accumulates unrelated fixes, or implementation crosses into deferred v2 scope.

When this happens, do not reset blindly and do not continue blind patching. Produce a short diagnostic handoff and ask Architecture for a decision.

### Complex milestone Definition of Done

For complex milestones, Definition of Done includes diagnostic evidence, failing/coverage test where practical, narrow implementation, targeted tests green, prior milestone regressions green, original smoke path replayed, browser smoke green when user-visible, Linux smoke green when runtime-relevant, project memory updated, clean working tree, feature branch committed and pushed, feature snapshot after green smoke, Architecture acceptance before merge, main merge confirmed, and Linux main pull after merge when runtime-relevant.
