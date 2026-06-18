# Direct Ollama Training Report Section Fact-Anchored Output v4

## Status

Implemented as a spike-only tightening pass after Quote-Only Context Isolation v3.

Runtime QA for v3 showed meaningful model-behavior improvement: the model-facing payload no longer appeared contaminated by user IDs, report dates, broad completion/adherence hints, skipped-exercise hints, or trend-like metadata. qwen2.5 began using the approved workout name, but the candidate still failed because the copy was too generic and introduced unsupported phrasing such as "completed as planned."

## Decision

Keep quote-only isolation and add fact-anchored output requirements.

The backend now derives a small prioritized list of `required_fact_anchors` from approved quote facts and sends those anchors in the model-facing quote-only payload. The model may still write natural coaching interpretation, but it must include enough exact anchors to prove the copy is grounded in backend-approved facts.

## Model-facing payload additions

`TrainingReportSectionModelQuoteContext` now includes:

- `required_quote_name`
- `required_anchor_count`
- `required_fact_anchors`
- `approved_workout_names`
- `approved_exercise_names`
- `approved_training_numbers`
- `approved_quote_facts`
- `forbidden_meta_terms`
- `coaching_intent`
- `tone_guidance`
- `section_contract_reminder`

The model-facing payload remains quote-only. It does not include user ID, report date, raw training summaries, raw execution rows, runtime/provider metadata, or broader backend context.

## Anchor selection

Required fact anchors are selected deterministically from approved quote facts:

1. Include `required_quote_name` first when available.
2. Prefer concrete exercise performance facts such as logged load/reps.
3. Prefer final-set RIR facts when available.
4. Use other logged facts and planned facts only after stronger anchors.
5. Avoid generic completion facts as required anchors when stronger facts exist.
6. Keep the list small, currently capped at five anchors.

`required_anchor_count` is:

- `0` when no anchors exist
- `1` when one anchor exists
- `2` when two or more anchors exist

## Prompt behavior

The prompt now tells the model:

- Use only the quote-only model-facing context.
- Include at least `required_anchor_count` exact anchors from `required_fact_anchors`.
- Use exact character-for-character anchors for the requirement.
- Do not merely list anchors; use them to write natural coaching interpretation.
- Do not use meta-language such as "approved quote facts," "bounded training summary," or "based on the provided facts."
- Do not mention user metadata, report dates, adherence, trends, skipped exercises, completion counts, progression, fatigue, or recovery unless exactly approved.

## Validation behavior

The validator now rejects candidates that:

- fail to include the required number of exact fact anchors
- use fuzzy paraphrases instead of exact anchors for the anchor requirement
- use meta-copy such as "approved quote facts," "approved facts," "bounded training summary," "quote context," "source facts," "provided facts," or "based on the provided facts"
- say "completed as planned" unless explicitly approved
- violate existing quote-only validation for metadata, unapproved numbers, trend/adherence/skipped claims, invented names, or generic copy

Deterministic fallback remains unchanged.

## Scope preserved

This remains spike-only.

No production training report provider was added. No full-report assembly wiring was added. No Streamlit behavior changed. No report persistence changed. No workout generation changed. No CrewAI behavior changed. No live Ollama calls occur in pytest.

## Runtime QA expectation

After v4, qwen2.5 should either:

- pass by using exact anchors such as `Gradual Progression Strength Session`, `Romanian Deadlift was logged at 135 lb for 7, 7, 7 reps.`, and `The final Romanian Deadlift set was logged at 1 RIR.`; or
- fail cleanly and fall back deterministically.

A provider-approved candidate must be specific, coach-like, and grounded in at least the required number of exact backend-approved fact anchors.
