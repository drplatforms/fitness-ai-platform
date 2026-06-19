# Coach Voice Contract Tightening v1

Status: IMPLEMENTED / PENDING QA

Implementation status: `COACH_VOICE_CONTRACT_TIGHTENING_V1_IMPLEMENTED_PENDING_QA`

## Purpose

Coach Voice Contract Tightening v1 improves the offline bakeoff prompt/schema packaging so local model candidates are less likely to echo schema metadata or miss the required answer object.

This milestone keeps the bakeoff offline and backend-controlled. It does not integrate model output into Today, Streamlit, reports, report history, or production provider paths.

## Background

Bounded Coach Voice Bakeoff v1 proved that bounded coach voice is viable, but several candidates failed the strict output contract:

- `qwen2.5:3b` failed the current output contract.
- `qwen3:14b` failed the current output contract.
- `qwen3:30b-a3b` failed the JSON-only contract in the optional addendum.
- `qwen3:8b` passed the starter contexts and remains the best practical evaluation-only reference.
- `qwen3:32b` passed the starter contexts and remains the best offline / chores-mode quality reference.

The likely issue is prompt/schema packaging, not a reason to loosen validators.

## Implemented changes

The bakeoff prompt now:

- separates instructions from approved context
- avoids exposing raw JSON Schema metadata to the model
- explicitly says not to return the schema
- explicitly forbids returning keys such as `type`, `properties`, `required`, `items`, or `additionalProperties`
- shows the required answer object as an example answer format instead of schema metadata
- labels the approved focus as one exact required string
- labels approved facts as exact strings that may be copied into `used_approved_facts`
- labels forbidden claims separately
- repeats that `recommended_focus` must exactly equal the backend-approved focus

The parser and validators remain strict.

## Preserved output contract

Models must still return exactly:

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

Required keys remain unchanged.

## Preserved validation rules

Still required:

- strict JSON-only output
- no markdown or prose wrapper
- no missing keys
- no extra keys
- exact `recommended_focus` match
- exact approved fact matching in `used_approved_facts`
- forbidden claim rejection
- invented numeric token rejection
- generic filler rejection
- compact coach-note validation
- approved-context specificity check

No validator was loosened.

## Report improvements

The generated markdown report now includes:

- model summary table
- context matrix table
- parse pass counts
- validation pass counts
- decision pass counts
- average grounding
- average coach voice
- average latency
- failure categories such as schema echo, parse/json, forbidden claim, invented number, generic filler, focus mismatch, or unapproved fact

This supports QA review across all five context packs.

## Required QA run

Run all five accepted context packs:

```powershell
python tools/coach_voice_bakeoff.py --all-contexts --model qwen2.5:3b --model qwen3:8b --model qwen3:14b --model qwen3:30b-a3b --model qwen3:32b
```

If `qwen3:32b` runtime is too long, run it separately:

```powershell
python tools/coach_voice_bakeoff.py --all-contexts --model qwen3:32b
```

## Non-goals preserved

This milestone does not:

- promote any model
- approve qwen3 for production
- integrate model output into Today
- integrate model output into Streamlit
- integrate model output into reports
- change production provider paths
- make direct_ollama default
- loosen validators
- remove deterministic fallback
- remove provider gates
- add RAG, embeddings, scraping, or agents
- add meal planning
- allow AI-generated food or exercise suggestions
- change food catalog
- change exercise catalog
- change workout generation
- change nutrition formulas
- change Level 5 Training semantics
- change Level 5 Nutrition semantics

## Expected QA status

`COACH_VOICE_CONTRACT_TIGHTENING_V1_IMPLEMENTED_PENDING_QA`

Acceptance of this milestone would accept the tightened bakeoff contract and scorecard improvements only. It would not approve any model for production.
