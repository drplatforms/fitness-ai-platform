# Developer Delivery Workflow Contract v1

Status: proposed workflow contract for AI Health Coach implementation handoffs.

Last updated: 2026-06-20

## Purpose

This document defines the standard implementation delivery workflow for AI Health Coach / `fitness-ai`.

It exists because repo workflow is part of project architecture. The project uses multiple chats, agents, branches, Windows development, Linux runtime checks, snapshots, and project-memory handoffs. If delivery mechanics drift, implementation quality drifts.

This contract is binding guidance for ChatGPT, Codex-style agents, patch helpers, QA, DevOps & Tooling, and future project-memory work.

This contract is extended by `docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md`, which adds hard-stop gates for generated scripts and post-merge ancestry verification.

## Core rule

Patch-first delivery is the default.

Snapshot restore is a fallback only.

When Dustin provides a snapshot filename, the next assistant response must provide the Linux pull command first, before handoff or next-step discussion.

Generated scripts must also follow the script-safety addendum. In particular, merge scripts must prove that the accepted final feature commit is an ancestor of `main` after merge:

```text
git merge-base --is-ancestor <accepted-final-feature-commit> main
```

A clean working tree is not proof that the correct milestone was merged.

## Environment assumptions

### Windows source repo

Windows is the source-of-truth development environment for normal implementation work:

```text
C:\projects\fitness_ai
```

Use Windows PowerShell commands for:

- patch application
- source edits
- validation
- staging
- commits
- pushes
- snapshot creation
- Windows-local FastAPI/Ollama runtime tests

### Linux mirror repo

Linux is the mirror/staging/runtime QA environment:

```text
~/projects/fitness-ai-platform
```

Use Linux commands for:

- pull/sync after Windows push
- Linux import/startup validation
- Linux FastAPI/Streamlit runtime smoke when that runtime is being tested
- Linux-to-Windows Ollama provider tests when explicitly needed

Do not commit from Linux unless a milestone explicitly changes the workflow.

### Ollama location

Ollama runs on the Windows machine, not Linux, unless Dustin explicitly says otherwise.

Windows-local Ollama URL:

```text
http://127.0.0.1:11434
```

Linux-to-Windows Ollama URL:

```text
http://192.168.1.104:11434
```

When Linux FastAPI needs to call Windows Ollama, set:

```bash
export OLLAMA_BASE_URL="http://192.168.1.104:11434"
```

Do not default to Linux-local Ollama commands for provider runtime work.

## Normal delivery path: patch-first

Use this path for normal implementation milestones.

1. Assistant provides one patch file as the primary artifact.
2. User downloads the patch to the project root:

   ```text
   C:\projects\fitness_ai
   ```

3. Commands assume project root unless explicitly stated.
4. Commands verify the expected branch before applying changes.
5. Commands run `git apply --check <patch>` before `git apply <patch>`.
6. Commands apply the patch.
7. Commands validate.
8. Commands stage only expected files.
9. Commands show staged files with `git diff --cached --name-only`.
10. Commands commit.
11. Commands push.
12. Commands create the standard snapshot.
13. User provides the snapshot filename.
14. Assistant immediately provides Linux pull.
15. Handoff comes after Linux pull.

This is the preferred implementation loop.

## Standard patch command pattern

A patch handoff should normally include a PowerShell block like this:

```powershell
cd C:\projects\fitness_ai

$expectedBranch = "feature/example-branch"
$currentBranch = git branch --show-current
if ($currentBranch -ne $expectedBranch) {
    throw "Wrong branch. Expected $expectedBranch but got $currentBranch"
}

git status --short
git apply --check .\example.patch
git apply .\example.patch
git status --short
```

For a new branch from accepted main:

```powershell
cd C:\projects\fitness_ai

git fetch origin
git switch main
git pull --ff-only origin main

git switch -c feature/example-branch

git apply --check .\example.patch
git apply .\example.patch
```

## Validation before commit

Validation depends on milestone scope, but commands should usually include:

```powershell
cd C:\projects\fitness_ai

git diff --check
scripts/dev_commit_check.ps1 -Mode code

python -m py_compile <changed-python-files>
python -m pytest <focused-tests> -q
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
```

Docs-only milestones may use docs/tooling-focused validation, but must still run project-memory checks.

Provider/UI/runtime milestones may require manual smoke tests. Runtime commands must match the real environment, especially the Windows Ollama assumption.

## Explicit staging and commit

Do not use broad staging unless Architecture explicitly allows it.

Stage expected files explicitly:

```powershell
git add docs\project_memory\developer_delivery_workflow_contract.md
git add AGENTS.md
git add docs\project_memory\README.md

git diff --cached --name-only

git commit -m "Add developer delivery workflow contract"
git push -u origin feature/developer-delivery-workflow-contract-v1
```

Before commit, verify no local artifacts are staged.

Never stage or commit:

- `*.zip` snapshots
- `*.patch` files
- `qa_artifacts/`
- `artifacts/`
- local DB files
- secrets
- runtime logs
- helper apply scripts unless the milestone explicitly adds a reusable repo tool
- downloaded fallback snapshots

## Standard snapshot command

After commit and push, create the standard snapshot from Windows:

```powershell
cd C:\projects\fitness_ai

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

## Linux pull-after-snapshot hard rule

When Dustin provides a snapshot filename, the assistant must respond with Linux pull first.

Standard Linux pull pattern:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

git fetch origin
git switch <branch> || git switch --track origin/<branch>
git pull --ff-only origin <branch>

git status -sb
git log --oneline -5
```

If a branch was intentionally force-replaced after a bad remote attempt, use this explicit form instead:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

git fetch origin
git switch <branch> || git switch --track origin/<branch>
git reset --hard origin/<branch>

git status -sb
git log --oneline -5
```

The assistant may provide optional Linux validation after the pull block, but the pull block comes first.

## Snapshot fallback path

Snapshot restore is a fallback, not the normal path.

Use snapshot fallback only when:

- patch application fails
- branch state is corrupted
- the working tree is half-applied
- tests and services are mismatched
- restoring a known-good set of files is safer than incremental repair

Fallback rules:

1. Provide a known-good snapshot ZIP only as backup.
2. Provide one inline restore block or one restore script.
3. Restore only necessary files from the snapshot.
4. Copy restored files into exact repo paths.
5. Verify the snapshot path before extraction.
6. Verify expected files exist inside the snapshot before copying.
7. Show proof checks after restore.
8. Clean helper artifacts before commit.
9. Do not make the user save multiple files to different locations unless unavoidable.
10. Do not let snapshot restore become the default implementation workflow.

Preferred fallback restore behavior:

```text
snapshot ZIP -> temporary qa_artifacts extraction folder -> copy only required files -> validate -> commit
```

Do not blindly overwrite unrelated files.

## Project memory update requirement

Project memory updates are part of Definition of Done.

Any meaningful commit or milestone that changes behavior, architecture boundaries, provider behavior, persistence, routes, UI, tests, project scope, accepted status, roadmap direction, or known limitations must update relevant project memory docs in the same branch.

A milestone is not done if project memory still describes older project truth.

## Runtime/provider workflow notes

For model/provider work, choose the runtime that matches the question being tested.

If the goal is model characterization and Ollama runs on Windows, prefer Windows FastAPI + Windows Ollama:

```powershell
cd C:\projects\fitness_ai
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

If the goal is Linux runtime or Linux-to-Windows provider path validation, use Linux FastAPI with Windows Ollama:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate
export PYTHONPATH="$PWD"
export OLLAMA_BASE_URL="http://192.168.1.104:11434"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Do not conflate model QA with network-path QA.

## Anti-patterns to avoid

Do not:

- make snapshot ZIP restore the default path
- require multiple downloads unless fallback is truly needed
- assume the user is on the expected branch without checking
- assume helper scripts exist in the repo
- assume downloaded files are in the correct path without checking
- tell the user to run a local script that has not been saved locally
- give Linux Ollama runtime commands when Ollama runs on Windows
- skip Linux pull after snapshot
- mix old remote branch state into a clean rebuilt branch
- ask the user to manually edit functions/blocks when a patch can do it
- leave helper scripts untracked in the repo root
- commit `qa_artifacts`, snapshots, DB files, secrets, or runtime outputs
- widen provider/model behavior during a workflow fix
- bury workflow changes only in chat memory

## Required handoff behavior

Implementation handoffs should include:

- source branch
- new branch
- patch artifact name
- branch verification commands
- `git apply --check`
- validation commands
- explicit staging commands
- commit command
- push command
- snapshot command
- instruction that Linux pull follows immediately after the user provides the snapshot filename

Final Architecture handoffs should confirm:

- whether patch-first delivery was used
- whether snapshot fallback was needed
- validation results
- files changed
- no forbidden artifacts committed
- docs/project memory updated

## Status of this contract

This document records workflow discipline only.

It does not authorize runtime behavior changes, provider behavior changes, UI changes, schema changes, persistence changes, same-session approval, model promotion, RAG/vector/MoE/MCP implementation, frontend rewrite, or deployment changes.


## Repo-owned command menu support

Local workflow helper commands are maintained in `scripts/fitness_commands.ps1` and documented in `docs/project_memory/local_developer_command_menu.md`.

The command menu exists to encode this contract in reusable local commands. Relevant helpers include `fbranch` for clean feature branch creation, `fsnap` for standard snapshots, `fsweep` for artifact contamination checks, `fmem` for project-memory checks, and `fpull`/`lpull` for Windows/Linux sync.

The PowerShell profile should only dot-source the repo script; project command logic should not live only in hidden local profile state.
