
# Developer Delivery Workflow Script Safety Addendum v1

Status: proposed script-safety addendum for AI Health Coach implementation handoffs.

Last updated: 2026-06-20

Extends: `docs/project_memory/developer_delivery_workflow_contract.md`

## Purpose

This addendum hardens the Developer Delivery Workflow Contract after a clean-but-wrong Git history sequencing issue.

A clean working tree does not prove the correct milestone landed on `main`. A branch can be clean, tests can pass, and `main` can still be missing the accepted final feature commit if scripts merge the wrong branch tip or an earlier commit in the same ancestry chain.

The core safety rule is therefore:

```text
git merge-base --is-ancestor <accepted-final-feature-commit> main
```

Every generated merge script must prove that the accepted final feature commit is an ancestor of `main` after the merge and before push, snapshot, or Linux pull.

A clean working tree is not proof that the correct milestone was merged. Scripts must stop before push, snapshot, or Linux pull when the accepted final feature commit ancestry check fails.

## Scope

This document is workflow guidance only.

It does not authorize runtime behavior changes, provider behavior changes, Streamlit UI changes, FastAPI route changes, database/schema changes, persistence changes, report behavior changes, same-session approval, model promotion, RAG/vector/MoE/MCP implementation, frontend rewrite, or deployment changes.

## Phase-separated script rule

Generated implementation scripts should be phase-separated. Prefer separate visible command blocks for:

1. preflight
2. apply patch
3. validate
4. stage
5. commit
6. push
7. Architecture review
8. merge after acceptance
9. snapshot
10. Linux pull

No single opaque script should do everything unless each phase has hard stop gates and prints what it is about to do.

## Mandatory preflight rules

Scripts that modify files or branches must:

- set `$ErrorActionPreference = "Stop"`
- print the current repo path
- verify the repo root
- print the current branch
- print `git status -sb`
- run `git fetch origin --prune`
- verify the intended base branch
- verify local `main` equals `origin/main` before creating a new feature branch
- stop if the working tree is dirty unless explicitly handling a known fallback
- stop if required patch/snapshot/script files are missing
- stop if branch assumptions are false

Recommended local-main equality check:

```powershell
git fetch origin --prune
git switch main
git pull --ff-only origin main

$localMain = git rev-parse main
$originMain = git rev-parse origin/main
if ($localMain -ne $originMain) {
    throw "Local main does not equal origin/main. Stop before creating a feature branch."
}
```

## Patch apply rules

Patch-based scripts must:

- assume the patch is downloaded to `C:\projects\fitness_ai` unless stated otherwise
- verify the patch file exists
- run `git apply --check <patch>` before `git apply <patch>`
- stop immediately if `git apply --check` fails
- apply the patch only after the check passes
- show changed files after the patch
- not stage automatically until validation passes

Recommended check pattern:

```powershell
$patch = "C:\projects\fitness_ai\example.patch"
if (-not (Test-Path $patch)) {
    throw "Missing patch: $patch"
}

git apply --check $patch
git apply $patch
git status --short
```

Use `--ignore-whitespace` only when explicitly justified, such as CRLF-heavy docs patches, and state why.

## Validation rules

Validation scripts must:

- run focused validation before commit
- include `git diff --check`
- include project-memory checks when docs changed
- include focused pytest files when tests/code changed
- include `py_compile` for changed Python tooling/modules when relevant
- stop on first failure

Docs/tooling validation should include:

```powershell
git diff --check
python -m py_compile tools/project_memory_check.py
python -m pytest tests/test_project_memory_check.py -q
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
```

## Staging and commit rules

Commit scripts must:

- stage explicit expected files only
- show `git diff --cached --name-only`
- verify no `qa_artifacts/` files are staged
- verify no snapshots are staged
- verify no local DB files are staged
- verify no secrets/local config files are staged
- verify no helper apply/restore scripts are staged unless intentionally added as reusable repo tooling
- commit only after the staged file list is reviewed

Recommended artifact guard:

```powershell
$staged = git diff --cached --name-only
$blocked = $staged | Where-Object {
    $_ -match '^qa_artifacts/' -or
    $_ -match '\.zip$' -or
    $_ -match '\.db$' -or
    $_ -match '\.sqlite$' -or
    $_ -match '^\.env$' -or
    $_ -match 'secret' -or
    $_ -match 'token'
}
if ($blocked) {
    $blocked | ForEach-Object { Write-Host "Blocked staged artifact: $_" }
    throw "Forbidden artifacts are staged."
}
```

## Merge safety rules

Merge scripts must run only after Architecture acceptance.

A safe merge script must:

1. fetch origin with prune
2. switch to `main`
3. pull `main` with `--ff-only`
4. verify local `main` equals `origin/main`
5. verify the accepted feature branch exists locally or on origin
6. verify the accepted final feature commit exists
7. merge the accepted branch with `--no-ff`
8. verify the accepted final feature commit is now an ancestor of `main`
9. stop if ancestry verification fails
10. run focused validation after merge
11. push `main` only after validation
12. create the snapshot only after push
13. wait for the user to provide the snapshot filename
14. provide Linux pull immediately after the snapshot filename

Required ancestry check:

```powershell
$acceptedCommit = "<accepted-final-feature-commit>"
git merge-base --is-ancestor $acceptedCommit main
if ($LASTEXITCODE -ne 0) {
    throw "Accepted final feature commit $acceptedCommit is not an ancestor of main. Stop: do not push, snapshot, or pull Linux."
}
```

This check would have caught the Provider Narrative QA Matrix sequencing issue where `main` was clean but did not contain the final accepted matrix results commit.

## Post-merge rules

After merge:

- run focused validation again
- run project-memory checks if docs changed
- push `main` only after validation passes
- create the snapshot after push
- the assistant must provide Linux pull immediately after the user provides the snapshot filename
- Linux mirror must switch to `main` and pull `origin/main`
- Linux log must show the same latest commit as Windows `main`

Standard Linux main pull after merge snapshot:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

git fetch origin
git switch main
git pull --ff-only origin main

git status -sb
git log --oneline -5
```

## Snapshot fallback safety rules

Snapshot ZIP restore remains fallback only.

Snapshot restore scripts must:

- verify the snapshot exists
- extract only necessary files
- copy files into exact repo paths
- avoid overwriting unrelated files
- show proof signatures or file existence checks
- remove helper extraction artifacts before commit
- never become the default delivery path

A fallback restore must not silently replace an entire working tree unless Architecture explicitly approves a full reset/restore strategy.

## Anti-patterns

Do not:

- combine restore, branch switch, commit, push, merge, and snapshot in one opaque script
- assume the current branch is correct
- assume local `main` is current
- assume a clean working tree means the correct milestone is merged
- assume a feature branch contains the final accepted commit
- merge without verifying the accepted final commit landed in `main`
- push after failed validation
- snapshot after failed merge verification
- use snapshot ZIP restore as the default implementation path
- leave helper scripts untracked in repo root
- commit `qa_artifacts/`, snapshots, DB files, secrets, or local runtime outputs
- hide workflow rules only in chat memory

## Required merge script checklist

Every generated merge script should require these explicit variables:

```powershell
$branch = "feature/example-milestone"
$acceptedCommit = "abc1234"
$expectedMergeMessage = "Merge feature/example-milestone"
```

The script should print:

- current branch before merge
- local `main` SHA
- `origin/main` SHA
- accepted final feature commit SHA
- staged/uncommitted status
- post-merge `main` SHA
- result of `git merge-base --is-ancestor <accepted-final-feature-commit> main`

## Status of this addendum

This addendum is binding project workflow guidance once accepted.

It exists to prevent clean-but-wrong Git history, incomplete milestone merges, and scripts that appear successful while omitting the accepted final feature commit.


## Command-menu safety helpers

`scripts/fitness_commands.ps1` includes `fmerge <branch-name> <accepted-final-commit>` as a local helper for accepted merge workflows.

The helper must preserve the required safety check:

```text
git merge-base --is-ancestor <accepted-final-feature-commit> main
```

If the accepted final feature commit is not an ancestor of `main`, the helper must stop before push, snapshot, or Linux pull.
