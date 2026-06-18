# AI Health Coach

AI Health Coach is an experimental health, recovery, nutrition, and training intelligence platform built with FastAPI, Streamlit, SQLite, deterministic recommendation services, and CrewAI-powered candidate generation.

The project is designed around a grounded AI architecture: the backend owns facts, calculations, constraints, validation, and persistence, while AI proposes structured candidate recommendations that must pass backend validation before anything becomes user-facing.

> **Disclaimer:** This project is for software engineering, experimentation, and personal productivity purposes. It is not medical advice, nutrition counseling, or a replacement for a qualified healthcare professional, registered dietitian, or certified coach.

---

## Project Goals

AI Health Coach is being built to explore how an AI coaching system can become more useful than a generic chatbot by grounding recommendations in structured user state and deterministic safety rules.

The long-term goal is a system that can:

- Track recovery, nutrition, and workout data over time.
- Build a factual `UserHealthState` from current and historical data.
- Calculate nutrition targets and training constraints deterministically.
- Use AI/CrewAI to generate candidate coaching recommendations within those constraints.
- Validate AI output before it becomes user-facing.
- Render approved recommendations into daily guidance and full health reports.
- Eventually support adaptive workout and meal planning based on health-state trends.

---

## Current Capabilities

### Core input workflows

- Recovery check-ins
- Nutrition logging
- Workout logging
- Exercise selection through API-backed exercise loading
- Health-state display
- AI health report generation
- Report latest/history views

### Grounded recommendation system

The current recommendation pipeline is:

```text
UserHealthState
→ NutritionTargets
→ TrainingConstraints
→ RecommendationContext
→ configured recommendation candidate provider
   - deterministic
   - CrewAI
→ CandidateActionPlan
→ parse/schema validation
→ recommendation validation
→ ApprovedActionPlan
→ deterministic rendering
→ Streamlit daily preview
→ Full AI Health Report Grounded Recommendation section
```

### Runtime safety and observability

The recommendation engine includes:

- Runtime provider toggle for deterministic vs CrewAI candidate generation
- Deterministic fallback when CrewAI output is invalid
- Strict `CandidateActionPlan` JSON contract
- Scenario-aware validation
- Confidence ceiling checks
- Internal/debug language rejection
- Developer debug route for runtime metadata
- Test suite that fakes CrewAI/Ollama so tests do not call the live model

---

## AI Design Philosophy

This project does **not** use AI as a simple copywriter.

The intended AI role is:

```text
AI proposes.
Backend constrains.
Backend validates.
Only approved plans render.
```

The backend remains responsible for:

- Factual health state
- Nutrition target display approval
- Training constraints
- Scenario classification
- Safety validation
- Persistence
- Fallback behavior

CrewAI/LLM output is treated as untrusted candidate output until it passes:

1. JSON parsing
2. Schema validation
3. Confidence validation
4. Recommendation validation
5. Scenario-specific safety checks

---

## Architecture Overview

### Main layers

```text
api/
  FastAPI routes for workouts, nutrition, recovery, reports, and recommendations

services/
  Business logic, health-state construction, recommendation generation, validation, and report orchestration

models/
  Dataclasses and structured domain models

agents/
  CrewAI agent definitions for recovery, nutrition, workout, and coordinator flows

ui/
  Streamlit interface for logging, viewing health state, recommendations, and reports

tests/
  Pytest regression, API smoke, recommendation engine, and report validation coverage
```

### Key backend concepts

- `UserHealthState` — factual state only
- `CoachingDecision` — deterministic scenario/strategy layer
- `NutritionTargets` — deterministic target calculation plus display approval flags
- `TrainingConstraints` — deterministic training boundaries
- `RecommendationContext` — structured context passed to the recommendation engine
- `CandidateActionPlan` — untrusted recommendation candidate
- `ApprovedActionPlan` — validated user-facing recommendation contract
- `RecommendationRuntimeMetadata` — debug/observability metadata kept separate from user-facing output

---

## API Highlights

### Health state

```http
GET /health-state/{user_id}
```

### Daily grounded recommendation

```http
GET /recommendations/daily/{user_id}
```

Returns the approved recommendation contract and rendered recommendation.

### Recommendation runtime debug view

```http
GET /recommendations/daily/{user_id}/debug
```

Returns developer-facing runtime metadata, including provider selection, CrewAI attempt status, fallback status, parse status, validation status, and raw output diagnostics.

### Reports

```http
POST /reports/generate/{user_id}
GET /reports/status/{job_id}
GET /reports/latest/{user_id}
GET /reports/history/{user_id}
```

### Workouts

```http
GET /exercises
GET /workouts/{user_id}
POST /workouts/create
```

### Nutrition

```http
GET /foods/search?query={query}
GET /nutrition/{user_id}/{entry_date}
POST /nutrition/log
```

### Recovery

```http
GET /recovery/metrics/{user_id}
POST /recovery/checkins
```

---

## Runtime Provider Configuration

By default, recommendation candidate generation uses the deterministic provider.

```env
RECOMMENDATION_CANDIDATE_PROVIDER=deterministic
```

Supported values:

```text
deterministic
crewai
```

To intentionally test CrewAI candidate generation:

```env
RECOMMENDATION_CANDIDATE_PROVIDER=crewai
CREWAI_RECOMMENDATION_MODEL=ollama/qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434
```

If CrewAI output is malformed, schema-invalid, unsafe, or fails validation, the system falls back to deterministic candidate generation.

---

## Local Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd fitness_ai
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create environment file

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Recommended local defaults:

```env
ENVIRONMENT=local
DATABASE_URL=sqlite:///./data/fitness_ai.db
RECOMMENDATION_CANDIDATE_PROVIDER=deterministic
```

### 5. Seed QA scenarios

```bash
python scripts/seed_qa_scenarios.py
```

This creates repeatable QA users:

```text
101 — Under-recovered lifter
102 — Well-recovered baseline
103 — Nutrition/training mismatch
104 — Improving after deload
105 — Messy/incomplete logging
```

### 6. Run checks

```bash
ruff check . --fix
black .
pytest
```

### 7. Start the FastAPI backend

```bash
uvicorn api.main:app --reload
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

### 8. Start the Streamlit UI

In another terminal:

```bash
streamlit run ui/streamlit_app.py
```

Streamlit usually opens at:

```text
http://localhost:8501
```

---

## QA and Testing

The project includes regression coverage for:

- User health-state construction
- Missing-data behavior
- Nutrition target display gating
- Training constraints
- Coaching scenario classification
- Candidate action plan parsing and validation
- CrewAI fallback behavior
- Recommendation runtime metadata
- API smoke tests
- Report status behavior
- Report language validation
- Seeded QA scenario coverage

Run all tests:

```bash
pytest
```

Run seeded QA script:

```bash
python scripts/seed_qa_scenarios.py
```

Then inspect:

```http
GET /recommendations/daily/101
GET /recommendations/daily/102
GET /recommendations/daily/103
GET /recommendations/daily/104
GET /recommendations/daily/105
```

For provider/fallback debugging:

```http
GET /recommendations/daily/105/debug
```

---

## Current Project Status

The project is in active development.

Recently completed architecture milestones include:

- Restored core input workflows
- Added health-state cognition signals
- Added deterministic `CoachingDecision` layer
- Added grounded recommendation engine scaffold
- Added daily recommendation preview endpoint
- Added backend-owned nutrition target display contract
- Integrated approved recommendations into full health reports
- Added CrewAI `CandidateActionPlan` JSON contract
- Wired CrewAI candidate generation behind backend validation
- Added runtime provider toggle
- Added recommendation runtime observability and debug endpoint

---

## Near-Term Roadmap

Planned next steps include:

- CrewAI runtime QA/tuning using the debug endpoint
- ApprovedActionPlan persistence design
- Scenario-specific claim contract extraction
- NutritionTargets v2 formula stack
- TrainingConstraints v2 with equipment, soreness, movement restrictions, and recent exercise history
- AI-generated workout candidate plans
- AI-generated meal/meal-plan candidate plans
- Local Ubuntu staging deployment
- Optional Raspberry Pi health-station/check-in client

---

## Tech Stack

- Python 3.11
- FastAPI
- Streamlit
- SQLite
- CrewAI
- Ollama-compatible local model runtime
- Pytest
- Ruff
- Black
- Pre-commit

---

## Development Notes

This project is intentionally structured around maintainable AI architecture rather than direct prompt-to-user output.

The core principle is:

```text
Facts and constraints first.
AI candidate generation second.
Validation before rendering.
Deterministic fallback always available.
```

That design keeps the system testable, safer, and easier to evolve as workout planning, meal planning, and longitudinal coaching become more advanced.
