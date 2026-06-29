# Open Questions — Daily Coach Wide Context Uncaged GPT-5.5 Ceiling Trial v1

## Active

1. Does GPT-5.5 produce a meaningfully better first-pass Daily Coach note with a wider backend-approved context packet?
2. Does wide context plus a minimal prompt outperform the current narrow Natural Draft path?
3. Which variant has the best balance of practical coaching feel, specificity, action clarity, and factual safety?
4. Does the wide-context packet give enough useful material without dumping raw DB rows or internal provider/runtime data?
5. Do token/cost telemetry fields provide enough visibility for future provider economics?
6. Should future provider architecture build around a stronger wide-context first pass if GPT-5.5 performs well?
7. If GPT-5.5 still sounds boxed-in with this setup, should Backend stop investing in narrow prompt/audit tweaks for Daily Coach copy?

## Known baseline drift

- `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches on the supplied `718c614` snapshot.
- Example mismatch: expected `Read the day before adding more`; actual `Consider the full day`.
- Architecture decision: document this drift and proceed with the ceiling trial.
- This milestone must not silently patch unrelated rich-day copy expectations.
- Full-suite green must not be claimed if the drift remains.

## Closed/unchanged boundaries

- Wide Context Ceiling Trial is developer-only.
- Normal Today behavior is unchanged.
- Existing provider endpoint behavior is unchanged.
- Deterministic remains default.
- OpenAI/direct_ollama remain explicit opt-in/evaluation-only.
- Backend remains final authority for facts, approved context, artifact safety, and future approval decisions.
- Raw provider envelopes are not persisted in default artifacts.
- No public UI, Streamlit provider controls, RAG, embeddings, meal planning, workout generation, recovery-score, worker, scheduler, queue, or production provider promotion is included.
