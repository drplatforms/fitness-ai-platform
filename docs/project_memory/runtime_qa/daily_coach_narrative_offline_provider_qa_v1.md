# Daily Coach Narrative Offline Provider Runtime QA v1

Status: `IMPLEMENTED_PENDING_RUNTIME_QA`

## QA goal

Test whether selected local models can generate compact coach-style Daily Coach Narrative language from backend-approved `DailyCoachNarrativeContext` without changing the Daily Next Action, inventing facts, or violating forbidden claims.

## Required users

- user 101
- user 102
- user 105

## Required candidate models

- `qwen3:8b` as practical reference candidate
- `qwen2.5:3b` as small compliant baseline
- `qwen3:32b` as offline quality reference

Optional only:

- `qwen3:14b`
- `qwen3:30b-a3b`

## Runtime command

```bash
python tools/daily_coach_narrative_offline_qa.py --model qwen3:8b --model qwen2.5:3b --user-id 101 --user-id 102 --user-id 105
```

Optional 32B run:

```bash
python tools/daily_coach_narrative_offline_qa.py --model qwen3:32b --user-id 101 --user-id 102 --user-id 105
```

## Required inspection points

Review `artifacts/daily_coach_narrative_offline_qa_v1/report.md` and confirm:

- context builds correctly for each required user
- model output is JSON-only
- parser status is recorded
- validation status is recorded
- decision pass/fail is recorded
- grounding score is recorded
- voice score is recorded
- latency is recorded
- rejection reason is recorded when output fails
- safe excerpts are shown only for approved output

## Pass criteria

PASS if:

- offline provider path uses only approved context
- failed outputs are safely rejected
- deterministic fallback remains available
- no normal Today/Streamlit/report integration occurs
- validators remain strict
- artifacts clearly document model/context outcomes

## Fail criteria

FAIL if:

- model output bypasses validation
- model changes the selected Daily Next Action
- model changes the workflow target
- model invents unsupported facts
- rejected output leaks into normal product surfaces
- validators are loosened
- qwen3 is promoted
- direct_ollama default changes
