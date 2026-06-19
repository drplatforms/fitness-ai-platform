# Bounded Coach Voice Bakeoff v1 Review

Status: IMPLEMENTED / READY FOR QA REVIEW

## Implementation summary

Bounded Coach Voice Bakeoff v1 adds a local-only evaluation harness for coach voice experiments.

New files:

- `models/coach_voice_bakeoff_models.py`
- `services/coach_voice_bakeoff_service.py`
- `tools/coach_voice_bakeoff.py`
- `tests/test_coach_voice_bakeoff_service.py`
- `docs/project_memory/runtime_qa/coach_voice_bakeoff_v1.md`

The harness compares model candidates on fixed backend-approved context packs and validates strict JSON output before scoring.

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

## Scoring dimensions

The harness reports:

- grounding
- claim safety
- coach voice
- specificity
- brevity
- actionability
- validator compatibility
- runtime practicality

## CLI tool

Run example:

```powershell
python tools/coach_voice_bakeoff.py --model qwen2.5:3b --model qwen3:8b --model qwen3:14b
```

Default output location:

```text
artifacts/coach_voice_bakeoff_v1/results.json
artifacts/coach_voice_bakeoff_v1/report.md
```

Artifacts are local QA outputs and should not be committed unless explicitly approved.

## Safety position

This is not production integration. It is a bounded offline evaluation layer.

qwen3 remains experimental and not approved. Any production use of model-written daily coach language requires a later Architecture promotion decision.
