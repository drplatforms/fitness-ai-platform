# Coach Voice Bakeoff v1 Runtime QA Closeout

Status: ACCEPTED / CLOSEOUT COMPLETE

Final status: `BOUNDED_COACH_VOICE_BAKEOFF_V1_ACCEPTED_WITH_MODEL_FINDINGS`

Closeout status: `BOUNDED_COACH_VOICE_BAKEOFF_V1_CLOSEOUT_COMPLETE_PENDING_MERGE`

## Purpose

Bounded Coach Voice Bakeoff v1 evaluated local model candidates against fixed backend-approved coaching context packs to determine whether a local model can produce premium coach language while staying inside approved truth boundaries.

This was an offline/backend-controlled evaluation milestone only.

No model is promoted by this result.

## Harness result

The harness successfully proved that local model candidates can be evaluated with:

- strict JSON parsing
- backend-selected focus preservation
- approved fact matching
- forbidden claim rejection
- invented number rejection
- compact coach-note validation
- structured scoring
- local artifact output only

The harness output remains local under:

```text
artifacts/coach_voice_bakeoff_v1/
```

Those artifacts are ignored by Git and should not be committed unless Architecture explicitly requests an accepted artifact snapshot.

## Required starter contexts

Accepted starter contexts:

- `user_101_recovery_limited`
- `user_102_daily_log_food`
- `user_105_data_quality_limited`

These contexts cover recovery-limited coaching, nutrition logging/completeness action, and data-quality-limited coaching.

## Required model findings

### qwen3:8b

Result: PASS on all 3 required starter contexts.

Architecture interpretation:

- best practical bounded coach voice evaluation candidate
- good grounding
- good coach voice
- latency roughly 31-40 seconds per context
- promising for future contract-tightened coach voice work
- not production-approved

### qwen2.5:3b

Result: failed current output contract.

Architecture interpretation:

- still useful as a speed/safety baseline
- current prompt/schema packaging is not compatible enough to judge it permanently unsuitable
- should be retried after Coach Voice Contract Tightening v1
- not promoted

### qwen3:14b

Result: failed current output contract.

Architecture interpretation:

- failure appears contract/schema-packaging related rather than a final model-quality conclusion
- should be retried after Coach Voice Contract Tightening v1
- not promoted

## Exploratory addendum

### qwen3:32b

Result: PASS on all 3 required starter contexts.

Architecture interpretation:

- best offline / chores-mode quality signal so far
- grounding score: 5
- voice score: 4
- latency roughly 2.6-3.1 minutes per context
- too slow for tight Today UI
- promising for offline report/reflection experiments
- not production-approved

## Model status

Allowed claim:

- The offline bakeoff identified `qwen3:8b` as the best practical bounded coach voice candidate and `qwen3:32b` as a promising offline large-model quality candidate.

Do not claim:

- qwen3 is approved
- qwen3:8b is production-ready
- qwen3:32b is production-ready
- any model can write directly to Today
- any model can write directly to reports
- any model can choose the next action
- any model can invent food, exercise, target, workout, recovery, or nutrition claims

## Safety position

Bounded Coach Voice Bakeoff v1 does not change production behavior.

Preserved boundaries:

- no Today integration
- no Streamlit integration
- no report integration
- no production provider path change
- no model promotion
- no qwen3 approval
- no direct_ollama default change
- no validator loosening
- no provider gate change
- no deterministic fallback change
- no food or exercise catalog change
- no nutrition formula change
- no workout generation change

## Next milestone

Recommended next milestone:

`Coach Voice Contract Tightening v1`

Goal:

Improve prompt/schema packaging so model candidates emit the required answer object more reliably before expanding evaluation to all five context packs.

Reference candidates:

- qwen3:8b
- qwen3:32b

Retry candidates:

- qwen2.5:3b
- qwen3:14b

Non-goals for the next milestone:

- no Today integration
- no report integration
- no model promotion
- no validator loosening
- no production provider path changes
- no qwen3 approval
- no direct_ollama default change
