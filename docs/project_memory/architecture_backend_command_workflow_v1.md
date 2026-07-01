# Architecture + Backend Command Workflow v1

**Status:** Active workflow memory
**Baseline:** `fc7ed70 main_merge-post-north-star-state-reconciliation-v1`
**Purpose:** Preserve the phase-separated command workflow used by Architecture and Backend Development so future chats do not blur responsibilities or invent unsafe Git shortcuts.

This file records the standing command patterns. Concrete milestone values such as commit hashes, branch names, patch names, snapshot names, and expected test files must still be supplied in the milestone-specific handoff.

## Hard Machine Boundary

Windows is the only source-of-truth Git write machine:

- commits
- merges
- pushes
- accepted snapshots

Linux is pull/validate/runtime QA only:

- pull the exact feature branch after every Windows feature commit/push
- pull `main` after every Windows merge/push
- run Linux validation, runtime smoke, FastAPI/Streamlit checks, and provider QA as scoped
- never commit from Linux
- never merge from Linux
- never push from Linux

Every command block must use concrete branch names, patch names, and expected commit values. Do not leave placeholders such as `<feature-branch-name>` in user copy/paste commands.

If Architecture is creating a docs-only patch, the latest post-merge snapshot is required before patch generation. If the latest snapshot is missing, stop and request it instead of patching against stale repo state.

## Lane Ownership

Architecture may produce or route docs-only project-memory patches when the change is limited to documentation, milestone state, workflow memory, handoffs, ADRs, reviews, or architecture plans.

Backend Development owns implementation patches: Python services, models, API routes, Streamlit runtime behavior, schema/persistence logic, tests, tooling behavior, provider behavior, and any code that changes runtime output.

Architecture must not quietly cross into Backend implementation. If a proposed Architecture patch touches runtime/code files, route it to Backend Development instead.

## Docs-Only Architecture Patch Rules

Allowed for Architecture docs-only patches:

- `AGENTS.md`
- `readme.md`
- `docs/project_memory/**`
- other explicit documentation files, if the milestone says so

Not allowed in Architecture docs-only patches:

- `services/**`
- `models/**`
- `api/**`
- `ui/**`
- `tests/**`, unless Architecture explicitly scopes a docs/test-metadata-only change
- database/schema/runtime/provider files
- dependency/config changes that affect application behavior

Docs-only validation should not use broad mutating formatters. Prefer project-memory checks, `git diff --check`, and `scripts/dev_commit_check.ps1 -Mode docs-only`.

## Backend Patch Workflow Template

Use this when Backend or a routed docs-only patch is applied from Windows. Store temporary artifacts outside the repo, normally in `C:\projects`.

### Phase 1 — Preflight / branch only

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

$ErrorActionPreference = "Stop"

git fetch origin --prune
git switch main
git pull --ff-only origin main

$currentHead = git rev-parse --short HEAD
Write-Host "CURRENT_HEAD=$currentHead"

if ($currentHead -ne "<expected_base_commit>") {
    git log --oneline --decorate -10
    throw "STOP: Expected main at <expected_base_commit> before applying this patch."
}

$dirty = git status --porcelain
if ($dirty) {
    git status --short
    throw "STOP: working tree is dirty before applying patch."
}

git switch -c feature/<milestone-branch>

git status -sb
git log --oneline --decorate -8
```

### Phase 2 — Apply patch only

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

$ErrorActionPreference = "Stop"

git apply --check --ignore-whitespace ..\<patch_name>.patch
git apply --ignore-whitespace ..\<patch_name>.patch

git status --short
```

Use `--ignore-whitespace` when the sandbox-generated patch was validated that way or when Windows line endings would otherwise block a docs-only patch. Do not use it to hide semantic conflicts.

### Phase 3 — Validation only

Docs-only baseline:

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

$ErrorActionPreference = "Stop"

git diff --check

python -m pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief

scripts/dev_commit_check.ps1 -Mode docs-only

git status --short
```

Code milestones require the focused tests named in the handoff plus broader regression checks when Architecture or QA requires them.

### Phase 4 — Review diff only

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

$ErrorActionPreference = "Stop"

git diff --check
git diff --stat
git diff
```

### Phase 5 — Stage only

Do not use `git add .`.

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

$ErrorActionPreference = "Stop"

git add <explicit-file-1>
git add <explicit-file-2>
# Continue with every expected touched file from the handoff.

git status --short
git diff --cached --name-only
```

The handoff must state the expected staged file count and list.

### Phase 6 — Commit only

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

$ErrorActionPreference = "Stop"

git commit -m "<milestone commit message>"

git status -sb
git log --oneline --decorate -8
```

### Phase 7 — Push from Windows

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

$ErrorActionPreference = "Stop"

git push -u origin feature/<milestone-branch>

git status -sb
git log --oneline --decorate -8
```

### Phase 8 — Linux pull / validation only

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

git fetch origin --prune
git switch feature/<milestone-branch>
git pull --ff-only origin feature/<milestone-branch>

git status -sb
git log --oneline --decorate -8

git diff --check HEAD~1..HEAD
```

Run the Linux validation commands named in the milestone handoff. Linux must not commit, merge, or push. For docs-only work, project-memory checks are usually enough. For runtime work, include FastAPI/Streamlit/manual smoke checks as scoped by QA or Architecture.

## Architecture Acceptance / Main Merge Workflow Template

Use this only after QA and Architecture have accepted a feature branch for merge.

### Phase 1 — Preflight accepted feature branch

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

$ErrorActionPreference = "Stop"

git fetch origin --prune

git switch feature/<accepted-feature-branch>
git pull --ff-only origin feature/<accepted-feature-branch>

$commit = git rev-parse --short HEAD
$subject = git log -1 --pretty=%s
$branch = git branch --show-current

Write-Host "Branch: $branch"
Write-Host "Commit: $commit"
Write-Host "Subject: $subject"

if ($commit -ne "<accepted_feature_commit>") {
    Write-Host "STOP: Expected <accepted_feature_commit>."
    exit 1
}

$status = git status --porcelain
if ($status) {
    git status -sb
    Write-Host "STOP: Feature branch is dirty."
    exit 1
}

git status -sb
git log --oneline --decorate -8
```

### Phase 2 — Merge to main

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

$ErrorActionPreference = "Stop"

git switch main
git pull --ff-only origin main

$status = git status --porcelain
if ($status) {
    git status -sb
    Write-Host "STOP: Main is dirty."
    exit 1
}

git merge --no-ff feature/<accepted-feature-branch> -m "<merge commit message>"

if ($LASTEXITCODE -ne 0) {
    git status -sb
    Write-Host "STOP: Merge failed."
    exit $LASTEXITCODE
}

if (-not (git merge-base --is-ancestor <accepted_feature_commit> HEAD)) {
    Write-Host "STOP: Accepted feature commit is not an ancestor of main."
    exit 1
}

git status -sb
git log --oneline --decorate -8
```

### Phase 3 — Post-merge validation

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

$ErrorActionPreference = "Stop"

$branch = git branch --show-current
if ($branch -ne "main") {
    Write-Host "STOP: Not on main."
    exit 1
}

# Run the focused post-merge validation commands from the Architecture acceptance handoff.
# Example docs-only baseline:
git diff --check
python -m pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief

git status -sb
```

### Phase 4 — Push main

```powershell
cd C:\projects\fitness_ai

$ErrorActionPreference = "Stop"

$status = git status --porcelain
if ($status) {
    git status -sb
    Write-Host "STOP: Main is dirty."
    exit 1
}

git push origin main

git status -sb
git log --oneline --decorate -5
```

### Phase 5 — Accepted post-merge snapshot

```powershell
cd C:\projects\fitness_ai

$ErrorActionPreference = "Stop"

$branch = git branch --show-current
if ($branch -ne "main") {
    Write-Host "STOP: Not on main."
    exit 1
}

$status = git status --porcelain
if ($status) {
    git status -sb
    Write-Host "STOP: Working tree is dirty."
    exit 1
}

$commit = git rev-parse --short HEAD
$subject = git log -1 --pretty=%s
$date = Get-Date -Format "yyyy-MM-dd"

Write-Host "Branch: $branch"
Write-Host "Commit: $commit"
Write-Host "Subject: $subject"

$snapshotName = "fitness_ai_snapshot_${date}_${commit}_<accepted-main-milestone-slug>.zip"
$snapshotPath = Join-Path "C:\projects" $snapshotName

git archive --format=zip --output="$snapshotPath" HEAD

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($snapshotPath)

try {
    $entries = $zip.Entries | Select-Object -ExpandProperty FullName

    Write-Host "Total entries:" $entries.Count
    Write-Host ".env included:" ($entries -contains ".env")
    Write-Host ".venv included:" (($entries | Where-Object { $_ -like ".venv/*" }).Count -gt 0)
    Write-Host ".git included:" (($entries | Where-Object { $_ -like ".git/*" }).Count -gt 0)
    Write-Host "qa-runs included:" (($entries | Where-Object { $_ -like "qa-runs/*" }).Count -gt 0)
    Write-Host "fitness_ai_provider_trials included:" (($entries | Where-Object { $_ -like "fitness_ai_provider_trials/*" }).Count -gt 0)
}
finally {
    $zip.Dispose()
}

Write-Host ""
Write-Host "Accepted snapshot:"
Write-Host $snapshotName
```

After the snapshot filename is provided, the next assistant response must provide Linux pull/sync commands before moving on to new architecture scope.


### Required Linux pull after main push

After Windows pushes a merge commit to `main`, provide a concrete Linux pull/validation block for `main` immediately. Do not move to new scope until Linux has pulled and validated the pushed `main` state.
