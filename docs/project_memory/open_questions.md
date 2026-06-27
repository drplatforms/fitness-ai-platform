# Open Questions — Daily Coach Narrative Value-Aware Provider Comparison v1

Current milestone: Daily Coach Narrative Value-Aware Provider Comparison v1.

Status: backend implementation complete / ready for Architecture review.

## Current Architecture question

Should Architecture accept the value-aware Daily Coach narrative provider-comparison path as the first user-facing narrative candidate contract over `DailyCoachSynthesis`?

Requested final status:

`DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED`.

## Resolved implementation choices

1. Deterministic remains default.
2. `direct_ollama` and `openai` are opt-in only.
3. The provider receives compact backend-approved value context.
4. The provider may quote approved values only when they are present in context.
5. Normal endpoint hides runtime metadata.
6. Debug endpoint exposes public-safe runtime metadata and provider-context summary.
7. Existing Daily Coach Narrative preview/async developer paths are preserved.

## Future questions preserved

These remain future scoping questions and are not authorized by this milestone:

1. Should this value-aware narrative eventually replace or supplement the Today card?
2. Should Streamlit Developer Mode render the debug endpoint first?
3. Should OpenAI provider runtime QA become a separate Agent Engineering milestone?
4. Should direct Ollama model trials use qwen3:8b or a smaller structured-output baseline?
5. Should DailyCoachSynthesis receive deeper actuals confidence/provenance summaries before normal UI exposure?
6. Should provider comparison output be persisted later through the existing Daily Coach async persistence architecture?
7. Should this pattern be generalized for weekly coach summaries and full report sections?

## Current answer boundary

This milestone adds a backend/API provider-comparison path only.

It does not authorize normal Streamlit display, persistence, report integration, or provider default changes.

## Historical continuity anchors — reference-only

- Daily Coach Async Provider Runtime Design v1
- qwen3:32b is research / future premium async candidate only
- deterministic fallback remains mandatory
- backend owns truth
- AI explains backend-approved truth
