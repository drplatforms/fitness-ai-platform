# Open Questions — Daily Coach Narrative Approved Value Quote Validation v1

Current milestone: Daily Coach Narrative Approved Value Quote Validation v1.

Status: authorized for backend implementation.

## Current Architecture question

Should Architecture accept an explicit approved value registry plus quote/value validator as the safety fence for value-aware Daily Coach provider narratives?

Requested final status:

`DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED`.

## Resolved direction from handoff

1. AI may quote deterministic backend values only when those values are approved, public-safe, present in provider context, and validated before rendering.
2. `quoted_values_used` must declare every quoted value.
3. Narrative prose must also be scanned for undeclared value claims.
4. Unknown, display-blocked, or invented quoted values cause deterministic fallback.
5. Deterministic remains default; providers remain opt-in.
6. Normal endpoint remains public-safe and hides runtime/validation internals.
7. Debug endpoint may expose sanitized validation metadata.

## Future questions preserved

1. Should approved quote validation be generalized across weekly coach summaries and report sections?
2. Should value claims eventually use a shared platform-wide claim registry?
3. Should Daily Coach Developer Mode render quote validation details?
4. Should OpenAI/direct_ollama runtime QA happen after this validation fence is accepted?
5. Should provider output persistence wait until quote validation is proven through QA?

## Current answer boundary

This milestone adds backend quote/value validation only.

It does not authorize normal Streamlit display, persistence, provider default changes, report integration, meal planning, RAG, or multi-agent orchestration.


## Historical continuity anchors — reference-only

- Daily Coach Async Provider Runtime Design v1
- qwen3:32b is research / future premium async candidate only
- deterministic fallback remains mandatory
- backend owns truth
- AI explains backend-approved truth
