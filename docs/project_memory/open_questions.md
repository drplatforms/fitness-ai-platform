# Open Questions — Daily Coach Wide Context User-Facing Language Cleanup v2

## Active

1. Does provider-facing context now stop encouraging `approved option`, `approved options include`, and related backend approval wording?
2. Does first-pass wide-context copy reduce `remaining protein gap` / `close any remaining protein gap` phrasing in favor of `if protein is still short` or `if you still need more protein`?
3. Does the cleanup avoid `green-light day`, `planned session`, and `planned workout` defaults when more user-facing session wording is available?
4. Does `pasteback_report.md` include the full exact deterministic baseline, current narrow path, and best wide-context variant while keeping non-winning variants terminal-friendly?
5. Does the product-language scan surface the remaining v2 copy leaks without becoming a production approval gate?
6. After live QA, is `wide_context_practical_coach` still the best variant or does another prompt variant produce cleaner user-facing copy?

## Known baseline drift

- `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches on the supplied lineage.
- Example mismatch: expected `Read the day before adding more`; actual `Consider the full day`.
- Architecture decision: document this drift and do not patch it inside unrelated wide-context copy/readability work.
- Full-suite green must not be claimed if the drift remains.

## Closed/unchanged boundaries

- Wide-context user-facing language cleanup remains developer-only.
- Normal Today behavior is unchanged.
- Existing provider endpoint behavior is unchanged.
- Deterministic remains default.
- OpenAI/direct_ollama remain explicit opt-in/evaluation-only.
- Backend remains final authority for facts, approved context, artifact safety, and future approval decisions.
- Raw provider envelopes are not persisted in default artifacts.
- No public UI, Streamlit provider controls, RAG, embeddings, meal planning, workout generation, recovery-score, worker, scheduler, queue, or production provider promotion is included.
