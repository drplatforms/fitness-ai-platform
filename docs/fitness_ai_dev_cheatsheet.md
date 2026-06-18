# Fitness AI Development Cheat Sheet

Recommended home:

```text
C:\projects\fitness_ai\docs\dev_cheatsheet.md
```

Use Markdown as the main cheat sheet. It is easier to copy/paste from, searchable in VS Code, and versionable with Git. Use Word only later if you want a printable copy.

---

## Current Defaults

```text
Windows repo: C:\projects\fitness_ai
Linux repo:   ~/projects/fitness-ai-platform
Active branch: feature/training-evidence-claim-service
Linux host: dusty@192.168.1.103
Ollama host: http://192.168.1.104:11434
FastAPI: http://127.0.0.1:8000
Streamlit: http://127.0.0.1:8501
```

Core project rule:

```text
Backend owns truth.
AI explains approved truth.
Validator enforces reality.
Deterministic remains default.
direct_ollama remains opt-in only.
qwen2.5:3b is the practical opt-in model.
qwen3 remains experimental only.
```

---

# 1. Daily Git Workflow

## Windows source workflow

```powershell
cd C:\projects\fitness_ai
git switch feature/training-evidence-claim-service
git status
```

Run checks:

```powershell
ruff check . --fix
black .
pytest -q
```

Commit carefully:

```powershell
git status --short
git diff --name-only

git add path\to\file.py
git add path\to\test_file.py

git commit -m "Your commit message"
git push origin feature/training-evidence-claim-service
```

Confirm local/remote match:

```powershell
git fetch origin
git rev-list --left-right --count HEAD...origin/feature/training-evidence-claim-service
```

Expected:

```text
0    0
```

## Linux pull latest

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

git fetch origin
git switch feature/training-evidence-claim-service
git pull --ff-only origin feature/training-evidence-claim-service

git log --oneline -5
git status --short
pip install -r requirements.txt
```

---

# 2. PowerShell Shortcuts

```text
fitness        Show command menu
cdf            Go to project
gstate         Check Windows git
gsync          Pull latest on Windows
gcheck         Run checks
gacp "msg"     Commit + push
lstatus        Check Linux staging
lupdate        Update/restart Linux
app            Open app
```

---

# 3. Windows Commands

## Activate venv

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1
```

## Start FastAPI

```powershell
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Start Streamlit

```powershell
streamlit run ui\streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

## Kill FastAPI / Streamlit

```powershell
$pid8000 = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique
if ($pid8000) { $pid8000 | ForEach-Object { taskkill /PID $_ /F } }

$pid8501 = (Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique
if ($pid8501) { $pid8501 | ForEach-Object { taskkill /PID $_ /F } }
```

## Verify ports

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :8501
```

---

# 4. Linux SSH + Runtime

## SSH

```powershell
ssh dusty@192.168.1.103
```

## Activate Linux repo

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate
git status --short
```

## Kill runtime services

```bash
tmux kill-session -t fitness-api 2>/dev/null || true
tmux kill-session -t fitness-ui 2>/dev/null || true

pkill -f "uvicorn api.main:app" || true
pkill -f "streamlit run" || true

sudo fuser -k 8000/tcp 2>/dev/null || true
sudo fuser -k 8501/tcp 2>/dev/null || true
```

---

# 5. Linux FastAPI Start Modes

## Deterministic mode

```bash
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

## Nutrition explanation CrewAI mode

```bash
tmux kill-session -t fitness-api 2>/dev/null || true

tmux new -d -s fitness-api "cd ~/projects/fitness-ai-platform && source .venv/bin/activate && \
WORKOUT_CANDIDATE_PROVIDER=deterministic \
WORKOUT_EXPLANATION_PROVIDER=deterministic \
POST_WORKOUT_REVIEW_PROVIDER=deterministic \
RECOMMENDATION_CANDIDATE_PROVIDER=deterministic \
HEALTH_REPORT_PROVIDER=deterministic \
NUTRITION_EXPLANATION_PROVIDER=crewai \
NUTRITION_EXPLANATION_MODEL=ollama/qwen2.5:3b \
OLLAMA_BASE_URL=http://192.168.1.104:11434 \
uvicorn api.main:app --host 0.0.0.0 --port 8000"
```

## Full report direct Ollama opt-in mode

Use only for async/background report job QA, not normal page-load testing.

```bash
tmux kill-session -t fitness-api 2>/dev/null || true

tmux new -d -s fitness-api "cd ~/projects/fitness-ai-platform && source .venv/bin/activate && \
OLLAMA_BASE_URL=http://192.168.1.104:11434 \
AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED=true \
TRAINING_REPORT_SECTION_PROVIDER=direct_ollama \
TRAINING_REPORT_SECTION_MODEL=ollama/qwen2.5:3b \
TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=300 \
uvicorn api.main:app --host 0.0.0.0 --port 8000"
```

## Workout Candidate Debug — experimental only

```bash
tmux kill-session -t fitness-api 2>/dev/null || true

tmux new -d -s fitness-api "cd ~/projects/fitness-ai-platform && source .venv/bin/activate && \
WORKOUT_CANDIDATE_PROVIDER=crewai \
WORKOUT_EXPLANATION_PROVIDER=deterministic \
CREWAI_WORKOUT_MODEL=ollama/qwen3:8b \
OLLAMA_BASE_URL=http://192.168.1.104:11434 \
CREWAI_WORKOUT_DISABLE_THINKING=true \
CREWAI_WORKOUT_JSON_RESPONSE_FORMAT=true \
RECOMMENDATION_CANDIDATE_PROVIDER=deterministic \
HEALTH_REPORT_PROVIDER=deterministic \
uvicorn api.main:app --host 0.0.0.0 --port 8000"
```

---

# 6. Linux Streamlit

```bash
tmux kill-session -t fitness-ui 2>/dev/null || true

tmux new -d -s fitness-ui "cd ~/projects/fitness-ai-platform && source .venv/bin/activate && \
streamlit run ui/streamlit_app.py --server.address 0.0.0.0 --server.port 8501"
```

## Verify services

```bash
tmux ls
ss -ltnp | grep -E ':8000|:8501'

curl http://127.0.0.1:8000/daily-coach/102/synthesis
curl -I http://127.0.0.1:8501
```

## Logs

```bash
tmux attach -t fitness-api
tmux attach -t fitness-ui
```

Detach:

```text
Ctrl+b then d
```

---

# 7. Async Report Job QA

## Deterministic default smoke

Start API with provider vars unset:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

unset AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED
unset TRAINING_REPORT_SECTION_PROVIDER
unset TRAINING_REPORT_SECTION_MODEL
unset TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS

uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

In another terminal:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

API_BASE_URL="http://127.0.0.1:8000" \
USER_IDS="102" \
REPORT_DATE="2026-06-14" \
EXPECT_PROVIDER="deterministic" \
python artifacts/runtime_async_report_job_qa.py
```

Expected:

```text
job_status=completed
provider_attempted=False
selected_provider=deterministic
debug_terms_in_report=[]
```

## direct_ollama async job sweep

Start API in opt-in mode:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

export OLLAMA_BASE_URL="http://192.168.1.104:11434"
export AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED="true"
export TRAINING_REPORT_SECTION_PROVIDER="direct_ollama"
export TRAINING_REPORT_SECTION_MODEL="ollama/qwen2.5:3b"
export TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS="300"

uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

In another terminal:

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

Expected:

```text
job_status=completed
provider_enabled=True
provider_attempted=True
selected_provider=direct_ollama
selected_model=qwen2.5:3b
training_section_source=direct_ollama_approved
validation_status=approved
validation_errors_count=0
angle_brackets=False
forbidden_seed_terms=False
debug_terms_in_report=[]
```

---

# 8. Useful API Calls

## Daily coach

```bash
curl http://127.0.0.1:8000/daily-coach/102/synthesis
```

## Start report job

```bash
curl -X POST "http://127.0.0.1:8000/reports/generate/102?date=2026-06-14"
```

## Check report job status

```bash
curl "http://127.0.0.1:8000/reports/status/<JOB_ID>"
```

---

# 9. Dev Assistant

```powershell
cd C:\projects\fitness_ai

.\.venv\Scripts\python.exe tools\dev_assistant.py status
.\.venv\Scripts\python.exe tools\dev_assistant.py handoff qa --milestone "Your milestone" --copy
.\.venv\Scripts\python.exe tools\dev_assistant.py pr --milestone "Your milestone" --copy
```

---

# 10. Snapshot Creation

Run from Windows after committing.

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

---

# 11. Before Sending to Architecture

```text
1. Windows tests passed.
2. Commit succeeded.
3. Push succeeded.
4. Linux pull succeeded.
5. Runtime QA passed.
6. Runtime acceptance doc updated.
7. Runtime acceptance doc committed and pushed.
8. Snapshot created.
9. Handoff includes:
   - recipient
   - branch
   - milestone
   - status
   - files changed
   - tests run
   - runtime QA results
   - non-goals
   - recommended next step
```

---

# 12. Do Not Accidentally Stage

Do not stage these unless intentionally part of the milestone:

```text
artifacts/
runtime logs
SQLite DB files
local .env files
temporary snapshots
unrelated black/ruff formatting changes
```

Check before commit:

```powershell
git status --short
git diff --cached --name-only
```
