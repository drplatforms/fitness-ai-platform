# Development Workflow

Last updated: 2026-06-18

## Purpose

This document defines the local development and commit workflow for the AI Health Coach repo.
It exists to reduce noisy commits, accidental staging, and validation friction while preserving the backend-truth-first architecture.

## Default Windows project path

Windows is the source-of-truth development machine.
Assume project root:

```powershell
cd C:\projects\fitness_ai
```

Patch and snapshot files are normally downloaded to this same project root.

## Windows vs Linux responsibility split

Windows owns source-of-truth repo work:

- `git status`
- patch apply
- source edits
- docs edits
- local validation
- `git add`, `git commit`, and `git push`

Linux owns runtime/staging QA:

- API runtime smoke tests
- Ollama-connected runtime QA
- SQLite persisted-history inspection
- staging app validation

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
Do not stage patch files, zip files, temporary artifacts, or local runtime outputs.

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

Use for normal code milestones.

Runs:

- `git diff --check`
- Ruff on changed Python files only, when possible
- Black on changed Python files only, when possible
- focused safety tests
- `git status --short`

Important: this mode intentionally avoids `black .` by default.
That prevents unrelated files from being reformatted during ordinary commit prep.

### Mode: full

Use for larger milestones, release-style checks, or when Architecture/QA asks for full validation.

Runs:

- `git diff --check`
- `ruff check . --fix`
- `black .`
- `pytest -q`
- `git status --short`

This mode can touch unrelated files if local drift exists. Clean drift first.

## Manual docs-only validation

For docs-only changes, this is usually enough:

```powershell
cd C:\projects\fitness_ai

powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode docs-only

git diff --check
git status --short
```

Full pytest is not required for docs-only milestones unless runtime/code files changed.

## Manual code validation

For code changes, prefer:

```powershell
cd C:\projects\fitness_ai

powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code
```

Then run additional focused tests that match the milestone.

## Manual full validation

For full validation:

```powershell
cd C:\projects\fitness_ai

powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode full
```

Use this intentionally. It is not the default path for docs-only or small code commits.

## Handling unrelated Black/Ruff drift

If Black or pre-commit touches unrelated files, inspect first:

```powershell
git status --short
```

Restore unrelated files only when they are clearly not part of the milestone:

```powershell
git restore -- path\to\unrelated_file.py
```

Do not use broad destructive cleanup commands unless you have verified the intended files are staged or backed up.

## Commit hygiene

Before commit:

```powershell
git status --short
git diff --cached --name-only
```

Only intended files should be staged.

Patch files and snapshot zips should remain untracked/local-only.

## Current product safety reminders

- Deterministic remains default and fallback.
- `direct_ollama/qwen2.5:3b` remains opt-in for Training only.
- qwen3 remains experimental only.
- Training remains the only provider-integrated full-report section.
- Nutrition Report Section is backend-owned Level 3 and does not call provider.
- Backend owns truth.
- AI explains approved truth.
- Validator enforces reality.
- The product principle remains: sound right and be right.
