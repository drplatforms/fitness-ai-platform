# Bounded Coach Voice Bakeoff v1 Review

Status: ACCEPTED / CLOSEOUT COMPLETE

Final status: `BOUNDED_COACH_VOICE_BAKEOFF_V1_ACCEPTED_WITH_MODEL_FINDINGS`

Closeout status: `BOUNDED_COACH_VOICE_BAKEOFF_V1_CLOSEOUT_COMPLETE_PENDING_MERGE`

## Decision

Bounded Coach Voice Bakeoff v1 is accepted as an offline/backend-controlled evaluation milestone.

The harness successfully evaluated local model candidates against backend-approved coaching contexts while preserving strict parsing, validation, local-only artifacts, and production isolation.

No model is promoted by this milestone.

## Implementation summary

The milestone added a local-only evaluation harness with:

- `models/coach_voice_bakeoff_models.py`
- `services/coach_voice_bakeoff_service.py`
- `tools/coach_voice_bakeoff.py`
- `tests/test_coach_voice_bakeoff_service.py`
- `docs/project_memory/runtime_qa/coach_voice_bakeoff_v1.md`

The harness compares model candidates on fixed backend-approved context packs and validates strict JSON output before scoring.

The CLI entrypoint was also patched so this command works from repo root without manual `PYTHONPATH`:

```powershell
python tools/coach_voice_bakeoff.py --model qwen2.5:3b
```

## Output contract

Each model must return exactly:

```json
{
  "coach_note": "string",
  "key_takeaway": "string",
  "recommended_focus": "string",
  "confidence_language": "string",
  "used_approved_facts": ["string"],
  "avoided_claims": ["string"]
}
```

The parser rejects markdown wrappers, missing keys, extra keys, and invalid field types.

## Validation behavior

The validator checks that:

- `recommended_focus` exactly matches an approved focus option
- `used_approved_facts` contains exact strings from the context pack
- forbidden claim fragments are not present in user-visible output
- invented numeric tokens are rejected unless supplied by approved facts
- output references approved context specifically
- generic filler language is rejected
- coach notes stay compact enough for future UI use

## Accepted model findings

### qwen3:8b

Accepted finding:

- passed all 3 required starter contexts
- best practical bounded coach voice evaluation candidate
- good grounding
- good coach voice
- latency roughly 31-40 seconds per context
- promising for future bounded coach voice work
- not production-approved

### qwen3:32b

Exploratory addendum finding:

- passed all 3 required starter contexts
- best offline / chores-mode quality signal
- grounding score: 5
- voice score: 4
- latency roughly 2.6-3.1 minutes per context
- too slow for tight Today UI
- promising for offline report/reflection experiments
- not production-approved

### qwen2.5:3b

Accepted finding:

- fast baseline
- failed current output contract
- should be retried after prompt/schema packaging is tightened
- not promoted

### qwen3:14b

Accepted finding:

- failed current output contract
- current result should not be treated as a permanent model-quality rejection
- should be retried after prompt/schema packaging is tightened
- not promoted

## Product interpretation

Bounded coach voice is viable, but it is not ready for production integration.

The result supports another contract-design milestone before Daily Coach Narrative v1.

The correct next step is not to ship model-written Today copy. The correct next step is to tighten the output contract so model voice becomes repeatable, portable, and safe enough to evaluate across all five context packs.

## Model status boundaries

Do not claim:

- qwen3 is approved
- qwen3:8b is production-ready
- qwen3:32b is production-ready
- any model can write directly to Today
- any model can write directly to reports
- any model can choose the next action
- any model can invent food, exercise, target, workout, recovery, or nutrition claims

Allowed claim:

- The offline bakeoff identified `qwen3:8b` as the best practical bounded coach voice candidate and `qwen3:32b` as a promising offline large-model quality candidate.

## Safety position

This is not production integration.

Preserved boundaries:

- no model promotion
- qwen3 remains not approved
- direct_ollama remains opt-in only
- no Today integration
- no Streamlit integration
- no report history integration
- no provider production path change
- no provider gate change
- no validator loosening
- no deterministic fallback change
- no food catalog change
- no exercise catalog change
- no nutrition target formula change
- no workout generation change

## Recommended next milestone

`Coach Voice Contract Tightening v1`

Focus:

- prevent schema echoing
- make the required output object clearer
- improve compatibility for qwen2.5:3b and qwen3:14b
- preserve strict validators
- keep qwen3:8b as the practical reference candidate
- keep qwen3:32b as the offline quality reference
- expand evaluation to all five context packs
- still avoid production integration
