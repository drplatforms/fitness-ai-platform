# Coach Voice Contract Tightening v1 Runtime QA

Status: READY FOR RUNTIME QA

Implementation status: `COACH_VOICE_CONTRACT_TIGHTENING_V1_IMPLEMENTED_PENDING_QA`

## Purpose

This runtime QA validates whether the tightened coach voice contract improves model compliance across all five accepted context packs without loosening validators or integrating model output into production surfaces.

## Required context packs

Run all five accepted context packs:

1. `user_101_recovery_limited`
2. `user_102_daily_log_food`
3. `user_105_data_quality_limited`
4. `user_102_nutrition_target_status`
5. `user_102_workout_preview`

Starter-context-only evaluation is not enough for this milestone.

## Required model candidates

Run:

- `qwen2.5:3b`
- `qwen3:8b`
- `qwen3:14b`
- `qwen3:30b-a3b`
- `qwen3:32b`

Reference candidates:

- `qwen3:8b` is the practical evaluation-only reference.
- `qwen3:32b` is the offline / chores-mode quality reference.

Retry candidates:

- `qwen2.5:3b`
- `qwen3:14b`
- `qwen3:30b-a3b`

## Runtime command

Preferred full run:

```powershell
python tools\coach_voice_bakeoff.py --all-contexts --model qwen2.5:3b --model qwen3:8b --model qwen3:14b --model qwen3:30b-a3b --model qwen3:32b
```

If `qwen3:32b` runtime is too long, run it separately:

```powershell
python tools\coach_voice_bakeoff.py --all-contexts --model qwen3:32b
```

## Expected artifacts

Local-only artifacts:

```text
artifacts/coach_voice_bakeoff_v1/results.json
artifacts/coach_voice_bakeoff_v1/report.md
```

These artifacts should remain ignored by Git unless Architecture explicitly requests an accepted artifact snapshot.

## What QA should record

Record from the generated report:

- model/context matrix
- parse pass count
- validation pass count
- validation fail count
- average grounding
- average voice
- latency
- schema echo failures
- forbidden claim failures
- invented number failures
- generic filler failures
- best practical candidate
- best offline candidate
- whether 14B improved
- whether 30B-A3B improved
- whether 3B improved
- recommended next milestone

## Success criteria

Pass if:

- harness runs cleanly
- validators remain strict
- no production paths change
- qwen3:8b remains compatible or improves
- qwen3:32b remains compatible or improves
- at least one previously failing model improves, ideally qwen3:14b
- schema echoing is reduced
- report artifacts clearly show model outcomes
- no model is promoted

Partial pass if:

- qwen3:8b and qwen3:32b still pass
- failing models still fail
- failure reasons are clearer and the contract remains stable

Fail if:

- validators are loosened
- production paths change
- qwen3 is promoted
- output can pass with unsupported claims
- schema failures increase for previously passing models
- raw model output leaks into app surfaces

## Boundary reminders

No model is production-approved by this QA.

Do not claim:

- qwen3 is approved
- qwen3:8b is production-ready
- qwen3:32b is production-ready
- any model can write directly to Today
- any model can write directly to reports
- any model can choose the next action
- any model can invent food, exercise, target, workout, recovery, or nutrition claims

## Result placeholder

Runtime QA result: `PENDING`

Accepted model findings after tightening: `PENDING`
