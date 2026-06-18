# Longitudinal QA Seed Data v1 Runtime Acceptance

## Status

ACCEPTED

Branch: `feature/training-evidence-claim-service`

Runtime date: 2026-06-15
Seed end date: 2026-06-14
Seed users: 101, 102, 103, 104, 105

## Summary

Longitudinal QA Seed Data v1 has been implemented, tested, committed, pushed, pulled into Linux runtime, seeded into the runtime database, and inspected.

The seed creates deterministic multi-month QA data for users 101-105 across:

- user profile/setup data
- recovery check-ins
- nutrition logs
- planned workout instances
- planned workout exercises
- workout execution sessions
- actual set logs

The seed is now the accepted runtime foundation for provider/runtime QA.

## Runtime Seed Inspection

Users created:

- 101 — recovery_limited
- 102 — aligned_managed
- 103 — nutrition_training_mismatch
- 104 — improving_after_deload
- 105 — data_quality_limited

Runtime counts:

| User | Check-ins | Food Entries | Workout Plans | Planned Exercises | Execution Sessions | Actual Sets |
|---:|---:|---:|---:|---:|---:|---:|
| 101 | 180 | 540 | 77 | 308 | 77 | 815 |
| 102 | 180 | 990 | 103 | 412 | 103 | 1133 |
| 103 | 160 | 300 | 77 | 308 | 77 | 847 |
| 104 | 180 | 546 | 77 | 308 | 77 | 847 |
| 105 | 120 | 81 | 41 | 123 | 41 | 205 |

Date ranges:

- `daily_checkins.checkin_date`: through 2026-06-14
- `food_entries.entry_date`: through 2026-06-14 for users 101-104; through 2026-06-12 for user 105 due intentionally limited logging
- `workout_plan_instances.selected_at`: through 2026-06-14 for user 102; through 2026-06-12/13 for other scenario-specific schedules

Contamination checks:

- Forbidden provider-facing workout names: none
- `qa_legacy_execution_bridge` rows: 0

## Provider Runtime QA

### qwen2.5:3b longitudinal sweep

Status: PASS

| User | Status | Fallback | Validation Errors | Artifact Leaks |
|---:|---|---:|---|---|
| 101 | approved | false | none | none |
| 102 | approved | false | none | none |
| 103 | approved | false | none | none |
| 104 | approved | false | none | none |
| 105 | approved | false | none | none |

Result:

`qwen2.5:3b` is the practical opt-in runtime candidate for the direct Ollama training report section provider.

It is not promoted to default.

### qwen3:8b longitudinal sweep

Status: SAFE FALLBACK PASS / NOT PROMOTED

| User | Status | Fallback | Validation Errors |
|---:|---|---:|---|
| 101 | approved | false | none |
| 102 | rejected | true | section_summary did not satisfy primary_signal |
| 103 | rejected | true | section_summary did not satisfy primary_signal |
| 104 | rejected | true | unsupported effort/consistency claim; section_summary did not satisfy primary_signal |
| 105 | approved | false | none |

Raw inspection conclusion:

- User 102 rejection was valid: summary did not name the primary signal lifts.
- User 103 rejection was valid: summary did not name the primary signal lifts.
- User 104 rejection was valid: summary used unsupported "controlled effort" language and did not name the primary signal lifts.
- Deterministic fallback handled rejected qwen3 outputs safely.
- No validator patch is needed.

`qwen3:8b` remains experimental only.

## Model Position

| Model | Position |
|---|---|
| qwen2.5:3b | Practical opt-in candidate |
| qwen3:8b | Experimental, slower, safe fallback confirmed |
| qwen2.5:7b | Not promoted |
| hermes3:8b | Not promoted |

## Acceptance Criteria Result

Accepted because:

- users 101-105 are cleanly seeded
- seed data is longitudinal and scenario-specific
- seed does not touch real user 1
- seed avoids forbidden provider-facing workout names
- seed creates planned execution evidence, not ad-hoc bridge rows
- recovery/nutrition/workout data spans approximately six months
- data_quality_limited user remains intentionally lower-confidence
- backend services can inspect seeded data
- qwen2.5:3b passes all five seeded scenarios
- qwen3:8b rejects safely where it misses strict requirements
- deterministic fallback remains intact
- no live Ollama is used in automated pytest

## Final Decision

Longitudinal QA Seed Data v1 is accepted as the runtime QA foundation.

The direct Ollama training report provider remains opt-in.

The next backend milestone may proceed from this cleaner QA base.
