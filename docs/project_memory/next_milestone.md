# Next Milestone

Current milestone in progress: Exercise Eligibility Matrix v1.

Recommended branch: `feature/exercise-eligibility-matrix-v1`.

Source branch: `main`.

Required source main commit: `37d210f`.

Milestone type: backend quality gate / diagnostic / explicit generator-facing eligibility matrix.

Current feature checkpoint: `05d319e` (`Add exercise eligibility matrix quality gate`).

Current checkpoint snapshot: `fitness_ai_snapshot_2026-06-26_05d319e_add-exercise-eligibility-matrix-quality-gate.zip`.

## Acceptance is blocked until

- Diagnostic-first process is documented and preserved.
- `tools/exercise_eligibility_matrix_diagnostic.py` remains a developer-only diagnostic.
- `services/exercise_eligibility_matrix_service.py` provides explicit generator-facing eligibility profiles.
- `tests/test_exercise_eligibility_matrix_v1.py` proves known primary, specialized/accessory, core, carry/conditioning, equipment-excluded, and metadata/exclusion behavior.
- The diagnostic baseline is recorded in project memory.
- Known current limitation is recorded: many generator-eligible exercises remain not selected in a 10-variation deterministic sweep.
- The failed optional diagnostic-service refactor is recorded as intentionally deferred rather than stacked blindly.
- Quick / Standard / Full sizing remains stable.
- Immediate preview refresh anti-repeat remains stable.
- Selected workout persistence remains stable.
- Active Workout persistence remains stable.
- Today workout de-dup remains stable.
- No provider/AI workout generation path is introduced.
- Windows validation is green.
- Linux validation is green.
- Browser/manual workout smoke is green before final Architecture acceptance.
- Feature snapshot is created only after final green validation/smoke.

## Diagnostic baseline to include in final handoff

- total active catalog exercises: 240
- total equipment-compatible exercises: 237
- total exercises with usable metadata: 240
- total specialized/accessory movements: 135
- total generator-eligible exercises: 232
- total selected in deterministic 10-variation sweep: 54
- total not reachable in deterministic sweep: 186
- top exclusion reason: `not_supported_by_current_generator_candidate_pools` (170)
- weak movement families: arms_biceps, arms_triceps, mobility

## Required validation before final acceptance

```powershell
git diff --check
pytest tests/test_exercise_eligibility_matrix_v1.py -q -s
pytest tests/test_exercise_catalog_utilization_specialized_movement_coverage_v1.py -q
pytest tests/test_exercise_catalog_service.py -q
pytest tests/test_workout_plan_service.py -q
pytest tests/test_workout_plan_selection_service.py -q
pytest tests/test_workout_plan_persistence_service.py -q
pytest tests/test_streamlit_workout_plan_selection.py -q
pytest tests/test_streamlit_today_workout_dedup.py -q
pytest tests/test_workout_daily_state_lifecycle_v1.py -q
pytest tests/test_workout_exercise_count_preference_v1.py -q
pytest tests/test_workout_generation_sizing_persistence_stabilization_v1.py -q
pytest tests/test_workout_preview_full_slot_rotation_v1.py -q
pytest tests/test_workout_preview_full_slot_rotation_quality_gate_v1.py -q -s
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
scripts/dev_commit_check.ps1 -Mode code
python -m py_compile services/exercise_catalog_service.py
python -m py_compile services/exercise_eligibility_matrix_service.py
python -m py_compile services/workout_exercise_count_service.py
python -m py_compile services/workout_plan_service.py
python -m py_compile tools/exercise_eligibility_matrix_diagnostic.py
python -m py_compile ui/streamlit_app.py
```

## Manual smoke before final acceptance

Workout page:

- Generate Quick and confirm 3-4 exercises.
- Click Show different exercises and confirm immediate refresh remains meaningfully different.
- Generate Standard and confirm 4-5 exercises.
- Click Show different exercises and confirm immediate refresh remains meaningfully different.
- Generate Full and confirm 6-7 exercises.
- Click Show different exercises and confirm immediate refresh remains meaningfully different.
- Confirm no obvious invalid equipment appears.
- Confirm no exact duplicate exercise names appear.
- Select a visible preview and confirm selected workout persists unchanged across refresh/rerun.
- Confirm Active Workout exactly matches selected workout.
- Confirm Today does not duplicate full workout selection flow and does not regenerate selected/active workout.
- Confirm Developer Mode does not expose raw rows/secrets/tracebacks and no provider/AI workout path was introduced.

## Recommended next milestones after acceptance

- Nutrition Deterministic Food Suggestions v1.
- Nutrition AI Meal/Snack Candidate Contract v1.
- Catalog Reachability Audit v2.
- Workout Preview Rolling Exposure Rotation v2.
- Recovery engine improvements later.

## Deferred / not authorized by this milestone

- rolling multi-refresh novelty
- persistent exercise exposure tracking
- forcing all catalog exercises into generated workouts
- giant movement taxonomy engine
- workout engine rewrite
- exercise catalog rewrite
- database migration
- exercise substitution UI
- selected-workout replacement
- workout periodization
- nutrition features
- recovery features
- Daily Narrative changes
- Weekly Summary changes
- AI/Ollama/CrewAI/OpenAI workout generation
- worker/queue/scheduler/polling
- Streamlit latency optimization

## Historical project-memory requirements still present

Some older project-memory tooling still checks for retained phrases related to prior Daily Coach async work:

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- feature/daily-coach-async-persistence-contracts-schema-v1
- schema/contracts
- NOT_AUTHORIZED_YET

These are historical continuity markers only. They do not authorize old async/provider implementation work.
