# Coach Voice Bakeoff v1 Runtime QA Plan

Status: PLANNED / HARNESS IMPLEMENTED PENDING QA RUN

## Purpose

Run the same backend-approved context packs across local model candidates to compare premium coach voice, grounding, safety, specificity, brevity, actionability, validator compatibility, and runtime practicality.

## Required candidates

- qwen2.5:3b
- qwen3:8b
- qwen3:14b

Optional later candidates:

- qwen3:30b-a3b
- qwen3:32b

## Starter context IDs

- `user_101_recovery_limited`
- `user_102_daily_log_food`
- `user_105_data_quality_limited`

## Recommended first command

```powershell
python tools/coach_voice_bakeoff.py --model qwen2.5:3b --model qwen3:8b --model qwen3:14b
```

## Expected outputs

```text
artifacts/coach_voice_bakeoff_v1/results.json
artifacts/coach_voice_bakeoff_v1/report.md
```

These outputs are local QA artifacts and should not be committed unless Architecture explicitly requests an accepted summary artifact.

## QA checks

For each result, capture:

- model tested
- context tested
- parse status
- validation status
- forbidden claims found
- grounding score
- specificity score
- coach voice score
- latency
- overall decision
- representative safe excerpt
- representative rejection reason

## Acceptance reminder

Acceptance of this bakeoff does not promote any model to production.

Production use of daily coach narrative requires a separate milestone and Architecture approval.
