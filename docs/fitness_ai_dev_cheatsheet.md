# Fitness AI Development Cheat Sheet

Use this as the copy/paste command center for the `fitness_ai` project. Keep it boring, current, and practical.

---

## 0. Project Defaults

```text
Windows repo: C:\projects\fitness_ai
Linux repo:   ~/projects/fitness-ai-platform
FastAPI:      http://127.0.0.1:8000
Streamlit:    http://127.0.0.1:8501
Ollama host:  http://192.168.1.104:11434
Linux host:   dusty@192.168.1.103
```

Current workflow pattern:

```text
main
→ feature/<milestone-branch>
→ validate
→ commit
→ push feature
→ optional runtime QA
→ docs closeout if needed
→ merge --no-ff to main
→ validate main
→ push main
→ snapshot with git archive
→ pull/sync Linux
```

Core project rules:

```text
Backend owns truth.
AI explains approved truth.
Validators enforce reality.
Deterministic remains default.
direct_ollama remains opt-in only.
qwen3 is not production-approved.
No model writes directly to Today, Streamlit, reports, or persistence without an approved milestone.
Use git archive for snapshots, not Compress-Archive.
```

Current model notes:

```text
qwen3:8b      Best practical evaluation-only Daily Coach Narrative candidate.
qwen2.5:3b   Small compliant baseline; watch for meta/process copy.
qwen3:32b    Offline quality reference; too slow/timeout-prone for tight loops.
qwen3:14b    Not reliable enough currently.
qwen3:30b    Not reliable enough currently.
```

---

## 1. Start of Workday

### Windows repo status

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

git status --short
git branch --show-current
git log --oneline -5
```

If starting a new milestone branch from main:

```powershell
cd C:\projects\fitness_ai

git fetch origin
git checkout main
git pull origin main

git checkout -b feature/<milestone-branch>
```

Example:

```powershell
git checkout -b feature/daily-coach-narrative-provider-contract-tightening-v1-1
```

---

## 2. Normal Validation Commands

### Fast docs-only validation

Use this for docs-only milestones and closeouts.

```powershell
cd C:\projects\fitness_ai

git diff --check
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode docs-only
```

### Normal code validation

Use this before committing code.

```powershell
cd C:\projects\fitness_ai

git diff --check
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code
```

### Common focused test block

```powershell
cd C:\projects\fitness_ai

.\.venv\Scripts\python.exe -m pytest tests\test_daily_next_action_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_report_persistence_boundary.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_full_report_section_registry.py -q
```

### Daily Coach Narrative focused tests

```powershell
cd C:\projects\fitness_ai

.\.venv\Scripts\python.exe -m pytest tests\test_daily_coach_narrative_context_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_daily_coach_narrative_provider_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_daily_coach_narrative_validation_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_coach_voice_bakeoff_service.py -q
```

### Full pytest when needed

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\python.exe -m pytest -q
```

### Compile checks

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\python.exe -m compileall api models services tests scripts tools ui
.\.venv\Scripts\python.exe -m py_compile ui\streamlit_app.py
```

---

## 3. Normal Commit Routine

```powershell
cd C:\projects\fitness_ai

git status --short
git diff --check

powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code

# Stage only expected files. Do not use git add . unless you are 100% sure.
git add path\to\changed_file.py
git add path\to\changed_test.py
git add docs\project_memory\current_state.md
git add docs\project_memory\open_questions.md

# Confirm staged files before commit
git diff --cached --name-only

git commit -m "Your commit message"
git push -u origin $(git branch --show-current)

git status --short
git log --oneline -5
```

If the branch already has upstream, plain push is fine:

```powershell
git push
```

---

## 4. Snapshot Creation

Run after commit/push, and after main merges.

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

Do **not** use this unless explicitly requested:

```powershell
Compress-Archive -Path * -DestinationPath snapshot.zip
```

Reason: `Compress-Archive` can include ignored/local junk. `git archive` snapshots exactly committed source.

---

## 5. Apply Patch Routine

```powershell
cd C:\projects\fitness_ai

git status --short

Test-Path .\<patch_name>.patch

git apply --check .\<patch_name>.patch
git apply .\<patch_name>.patch

git status --short
```

If `git apply --check` fails because docs drifted, use the snapshot-copy routine below.

---

## 6. Apply From Snapshot Zip When Patch Fails

Use this when a patch does not apply but there is a patched snapshot zip.

```powershell
cd C:\projects\fitness_ai

$snapshot = ".\<snapshot_name>.zip"
if (-not (Test-Path $snapshot)) {
    $snapshot = "..\<snapshot_name>.zip"
}

if (-not (Test-Path $snapshot)) {
    throw "Snapshot not found. Put the zip in repo root or one level above."
}

$tmp = "..\snapshot_apply_tmp"
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
Expand-Archive -Path $snapshot -DestinationPath $tmp -Force

$files = @(
    "docs/project_memory/current_state.md",
    "docs/project_memory/open_questions.md"
    # Add the exact files you want copied from the snapshot.
)

foreach ($file in $files) {
    $src = Join-Path $tmp $file
    $dst = Join-Path (Get-Location) $file

    if (-not (Test-Path $src)) {
        throw "Missing file in snapshot: $file"
    }

    New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
    Copy-Item $src $dst -Force
}

git status --short
```

Then validate and commit as normal.

---

## 7. Merge Feature Branch to Main

Use `--no-ff` for accepted milestones.

```powershell
cd C:\projects\fitness_ai

# Confirm feature branch is clean and pushed
git checkout feature/<milestone-branch>
git status --short
git log --oneline -5

# Final validation on feature branch
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code

# Merge to main
git fetch origin
git checkout main
git pull origin main

git merge --no-ff feature/<milestone-branch>
```

If Vim opens for the merge commit:

```text
Esc
:wq
Enter
```

Post-merge validation:

```powershell
git status --short
git log --oneline -5

powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code

# Run milestone focused tests here.

git push origin main

git status --short
git log --oneline -5
```

Then create a snapshot from main with the snapshot command above.

---

## 8. Linux Sync After Push or Merge

```bash
cd ~/projects/fitness-ai-platform

git status --short
git stash list

git fetch origin
git switch main
git pull --ff-only origin main

git status -sb
git log --oneline -5
```

Do not delete old Linux stashes unless intentionally cleaning them up.

Linux validation:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

python -m compileall api models services tests scripts tools ui

python -m pytest tests/test_daily_next_action_service.py -q
python -m pytest tests/test_report_persistence_boundary.py -q
python -m pytest tests/test_full_report_section_registry.py -q
```

Daily Coach Narrative Linux validation:

```bash
python -m pytest tests/test_daily_coach_narrative_context_service.py -q
python -m pytest tests/test_daily_coach_narrative_provider_service.py -q
python -m pytest tests/test_daily_coach_narrative_validation_service.py -q
python -m pytest tests/test_coach_voice_bakeoff_service.py -q
```

---

## 9. Start / Stop Windows Runtime

### Activate venv

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1
```

### Start FastAPI

```powershell
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Streamlit

```powershell
streamlit run ui\streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

### Kill FastAPI / Streamlit

```powershell
$pid8000 = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique
if ($pid8000) { $pid8000 | ForEach-Object { taskkill /PID $_ /F } }

$pid8501 = (Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique
if ($pid8501) { $pid8501 | ForEach-Object { taskkill /PID $_ /F } }
```

### Verify ports

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :8501
```

---

## 10. Linux Runtime With tmux

### SSH

```powershell
ssh dusty@192.168.1.103
```

### Kill Linux runtime services

```bash
tmux kill-session -t fitness-api 2>/dev/null || true
tmux kill-session -t fitness-ui 2>/dev/null || true

pkill -f "uvicorn api.main:app" || true
pkill -f "streamlit run" || true

sudo fuser -k 8000/tcp 2>/dev/null || true
sudo fuser -k 8501/tcp 2>/dev/null || true
```

### Start deterministic FastAPI

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

tmux kill-session -t fitness-api 2>/dev/null || true

tmux new -d -s fitness-api "cd ~/projects/fitness-ai-platform && source .venv/bin/activate && \
WORKOUT_CANDIDATE_PROVIDER=deterministic \
WORKOUT_EXPLANATION_PROVIDER=deterministic \
POST_WORKOUT_REVIEW_PROVIDER=deterministic \
RECOMMENDATION_CANDIDATE_PROVIDER=deterministic \
HEALTH_REPORT_PROVIDER=deterministic \
NUTRITION_EXPLANATION_PROVIDER=deterministic \
uvicorn api.main:app --host 0.0.0.0 --port 8000"
```

### Start Streamlit

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

tmux kill-session -t fitness-ui 2>/dev/null || true

tmux new -d -s fitness-ui "cd ~/projects/fitness-ai-platform && source .venv/bin/activate && \
streamlit run ui/streamlit_app.py --server.address 0.0.0.0 --server.port 8501"
```

### Verify services

```bash
tmux ls
ss -ltnp | grep -E ':8000|:8501'

curl http://127.0.0.1:8000/health
curl -I http://127.0.0.1:8501
```

### Logs

```bash
tmux attach -t fitness-api
tmux attach -t fitness-ui
```

Detach:

```text
Ctrl+b then d
```

---

## 11. Common API Smoke Calls

### Daily Coach Synthesis

```bash
curl http://127.0.0.1:8000/daily-coach/102/synthesis | jq
```

### Daily Recommendation

```bash
curl http://127.0.0.1:8000/recommendations/daily/102 | jq
```

### Recommendation Debug

```bash
curl http://127.0.0.1:8000/recommendations/daily/102/debug | jq
```

### Workout Plan Preview

```bash
curl http://127.0.0.1:8000/workout-plans/preview/102 | jq
```

### Nutrition Explanation Preview

```bash
curl "http://127.0.0.1:8000/nutrition/102/explanation/preview?date=2026-06-06" | jq
```

### Nutrition Explanation Debug

```bash
curl "http://127.0.0.1:8000/nutrition/102/explanation/debug?date=2026-06-06" | jq '.runtime_metadata'
```

### Start Report Job

```bash
curl -X POST "http://127.0.0.1:8000/reports/generate/102?date=2026-06-14" | jq
```

### Report Job Status

```bash
curl "http://127.0.0.1:8000/reports/status/<JOB_ID>" | jq
```

### Latest Report

```bash
curl "http://127.0.0.1:8000/reports/latest/102" | jq
```

---

## 12. Offline / Runtime QA Tools

### Coach Voice Bakeoff

```powershell
cd C:\projects\fitness_ai

python tools\coach_voice_bakeoff.py --all-contexts --model qwen2.5:3b --model qwen3:8b --model qwen3:14b --model qwen3:30b-a3b
```

Optional 32B reference:

```powershell
python tools\coach_voice_bakeoff.py --all-contexts --model qwen3:32b
```

Inspect report:

```powershell
Get-Content .\artifacts\coach_voice_bakeoff_v1\report.md | Select-Object -First 260
```

### Daily Coach Narrative Offline Provider QA

```powershell
cd C:\projects\fitness_ai

python tools\daily_coach_narrative_offline_qa.py --model qwen3:8b --model qwen2.5:3b --user-id 101 --user-id 102 --user-id 105
```

Optional 32B reference:

```powershell
python tools\daily_coach_narrative_offline_qa.py --model qwen3:32b --user-id 101 --user-id 102 --user-id 105
```

Inspect report:

```powershell
Get-Content .\artifacts\daily_coach_narrative_offline_qa_v1\report.md | Select-Object -First 260
```

### Direct Ollama Nutrition Explanation Spike

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

export OLLAMA_BASE_URL="http://192.168.1.104:11434"

python scripts/spike_direct_ollama_nutrition_explanation.py --model ollama/qwen2.5:3b --user-id 102 --date 2026-06-06
```

---

## 13. Provider Opt-In Modes

### Deterministic default

Unset experimental providers when you want safe/default behavior.

```bash
unset NUTRITION_EXPLANATION_PROVIDER
unset NUTRITION_EXPLANATION_MODEL
unset RECOMMENDATION_CANDIDATE_PROVIDER
unset TRAINING_REPORT_SECTION_PROVIDER
unset TRAINING_REPORT_SECTION_MODEL
unset AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED
```

### Nutrition explanation direct_ollama

```bash
export OLLAMA_BASE_URL="http://192.168.1.104:11434"
export NUTRITION_EXPLANATION_PROVIDER="direct_ollama"
export NUTRITION_EXPLANATION_MODEL="ollama/qwen2.5:3b"
export NUTRITION_EXPLANATION_DIRECT_OLLAMA_TIMEOUT_SECONDS="60"
```

Debug check:

```bash
curl -s "http://127.0.0.1:8000/nutrition/102/explanation/debug?date=2026-06-06" | jq '.runtime_metadata'
```

### Training report section direct_ollama

Use only for async/background report QA.

```bash
export OLLAMA_BASE_URL="http://192.168.1.104:11434"
export AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED="true"
export TRAINING_REPORT_SECTION_PROVIDER="direct_ollama"
export TRAINING_REPORT_SECTION_MODEL="ollama/qwen2.5:3b"
export TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS="300"
```

### Recommendation candidate CrewAI mode

Experimental/manual QA only.

```bash
export OLLAMA_BASE_URL="http://192.168.1.104:11434"
export RECOMMENDATION_CANDIDATE_PROVIDER="crewai"
export CREWAI_RECOMMENDATION_MODEL="ollama/qwen3:8b"
```

---

## 14. Async Report Job QA

### Deterministic smoke

Start API in deterministic mode, then run:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

API_BASE_URL="http://127.0.0.1:8000" \
USER_IDS="102" \
REPORT_DATE="2026-06-14" \
EXPECT_PROVIDER="deterministic" \
python artifacts/runtime_async_report_job_qa.py
```

### direct_ollama training section sweep

Start API with training section direct_ollama env vars, then run:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

API_BASE_URL="http://127.0.0.1:8000" \
USER_IDS="101,102,103,104,105" \
REPORT_DATE="2026-06-14" \
EXPECT_PROVIDER="direct_ollama" \
JOB_TIMEOUT_SECONDS="1200" \
python artifacts/runtime_async_report_job_qa.py
```

Expected safe path terms:

```text
job_status=completed
provider_attempted=True
selected_provider=direct_ollama
validation_status=approved
validation_errors_count=0
debug_terms_in_report=[]
```

---

## 15. Seed / Catalog Commands

### Seed QA scenarios

```powershell
cd C:\projects\fitness_ai
python scripts\seed_qa_scenarios.py
```

### Seed exercise catalog

```powershell
cd C:\projects\fitness_ai
python scripts\seed_exercise_catalog.py
```

### Seed canonical foods

```powershell
cd C:\projects\fitness_ai
python scripts\seed_canonical_foods.py
```

### Seed user profiles if script exists in branch

```powershell
cd C:\projects\fitness_ai
python scripts\seed_user_profiles.py
```

QA users we use often:

```text
101  recovery_limited / under-recovered lifter
102  aligned_managed / happy path baseline
103  nutrition_training_mismatch
104  improving_after_deload
105  data_quality_limited / messy logging
```

---

## 16. Artifact Cleanup / Do Not Stage

Do not stage these unless Architecture explicitly asks:

```text
artifacts/
qa_artifacts/
*.zip
*.db
*.sqlite
.env
runtime logs
temporary snapshot extraction folders
```

Clean common junk:

```powershell
cd C:\projects\fitness_ai
Remove-Item -Recurse -Force .\qa_artifacts -ErrorAction SilentlyContinue
```

Check before every commit:

```powershell
git status --short
git diff --cached --name-only
```

If artifacts appear as tracked/staged, stop and inspect before committing.

---

## 17. Common Git Fixes

### Undo unstaged changes to one file

```powershell
git restore path\to\file.py
```

### Unstage one file

```powershell
git restore --staged path\to\file.py
```

### See what changed

```powershell
git diff -- path\to\file.py
git diff --cached -- path\to\file.py
```

### Check local vs remote branch count

```powershell
git fetch origin
git rev-list --left-right --count HEAD...origin/$(git branch --show-current)
```

Expected when synced:

```text
0    0
```

### Fix trailing blank line / EOF whitespace issue

```powershell
$path = "path\to\file.py"
$text = Get-Content $path -Raw
$text = $text.TrimEnd("`r", "`n") + "`r`n"
[System.IO.File]::WriteAllText((Resolve-Path $path), $text, [System.Text.UTF8Encoding]::new($false))

git diff --check
```

### Intentional E402 after sys.path bootstrap

Use only when a script intentionally modifies `sys.path` before project imports.

```python
from services.some_service import something  # noqa: E402
```

---

## 18. Dev Assistant

```powershell
cd C:\projects\fitness_ai

.\.venv\Scripts\python.exe tools\dev_assistant.py status
.\.venv\Scripts\python.exe tools\dev_assistant.py handoff qa --milestone "Your milestone" --copy
.\.venv\Scripts\python.exe tools\dev_assistant.py pr --milestone "Your milestone" --copy
```

---

## 19. Handoff Template

```text
Recipient:
Architecture / QA / Backend Development

CC:
AI Provider Evaluation
Streamlit UI

Project:
AI Health Coach / fitness-ai

Branch:
<feature branch>

Latest commit:
<paste git log --oneline -1>

Snapshot:
<paste snapshot filename>

Milestone:
<milestone name>

Status:
IMPLEMENTED / LOCAL VALIDATION COMPLETE

Summary:
<what changed>

Files changed:
<short list>

Boundaries preserved:
- no model promotion
- no normal Today/Streamlit/report integration unless explicitly approved
- deterministic fallback preserved
- validators not loosened

Validation:
- git diff --check passed
- dev_commit_check passed
- focused tests passed
- runtime QA result if applicable

Request:
Please review for acceptance as:
<EXPECTED_STATUS>
```

---

## 20. Before Sending Anything to Architecture

```text
1. git status --short checked.
2. git diff --check passed.
3. dev_commit_check passed.
4. Focused tests passed.
5. Runtime QA completed if milestone requires it.
6. Artifacts/qa_artifacts not staged.
7. Commit pushed.
8. Snapshot created with git archive.
9. Linux pulled/synced if requested.
10. Handoff includes status, files, validation, boundaries, next step.
```
