# Next Milestone — Daily Coach Wide Context User-Facing Language Cleanup v2

Owner: Backend Development with Architecture, QA, and Agent Engineering review.

Baseline: `main` at `490d2ae Merge daily coach wide context copy cleanup qa readability v1`.

Baseline snapshot: `fitness_ai_snapshot_2026-06-28_490d2ae_main_merge-daily-coach-wide-context-copy-cleanup-qa-readability-v1.zip`.

Recommended branch: `feature/daily-coach-wide-context-user-facing-language-cleanup-v2`.

Goal: keep the wide-context approach, but make the best first-pass GPT-5.5 output sound more user-facing and coach-like by removing remaining backend-shaped language from provider-facing context and prompt packaging.

Required outputs:

- remove writer-facing `approved option` / `approved options include` wording;
- reduce default `remaining protein gap` / `close any remaining protein gap` wording;
- avoid `green-light day` unless explicitly approved later;
- reduce generic `planned session` / `planned workout` phrasing when actual session wording is available;
- preserve exact first-pass draft capture in `first_pass_drafts.md`;
- update `pasteback_report.md` so full exact deterministic baseline, current narrow path, and best wide-context variant are included;
- expand product-language diagnostic scan with the v2 phrases;
- keep existing QA readability flags and artifacts;
- targeted tests for prompt/context cleanup, scan behavior, pasteback full-best-variant behavior, CLI compatibility, and unchanged boundaries;
- project memory updates.

Boundaries:

- no normal Today behavior changes;
- no Streamlit changes;
- no API route changes;
- no full report behavior changes;
- deterministic remains default;
- OpenAI remains opt-in/evaluation-only;
- no provider promotion;
- no raw provider envelope persistence;
- no secrets, raw DB rows, or public UI exposure;
- no parser relaxation;
- no Product Voice Audit rewrite;
- no meal planning, workout generation, nutrition target mutation, recovery score mutation, RAG, embeddings, or multi-agent runtime.

Known baseline drift to document, not patch here:

- `tests/test_daily_narrative_rich_day_service.py` copy-expectation mismatches on the supplied baseline lineage.
- Example: expected `Read the day before adding more`; actual `Consider the full day`.
- Full-suite green must not be claimed if this remains.

Requested final status: `DAILY_COACH_WIDE_CONTEXT_USER_FACING_LANGUAGE_CLEANUP_V2_IMPLEMENTATION_COMPLETE`.
