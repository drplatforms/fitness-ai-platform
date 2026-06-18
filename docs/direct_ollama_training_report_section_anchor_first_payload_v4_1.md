# Direct Ollama Training Report Section Anchor-First Payload v4.1

## Status

Implemented as a spike-only refinement after Fact-Anchored Output v4.

Runtime QA for v4 showed that qwen2.5 and hermes3 were no longer broadly hallucinating user/date/adherence/trend/skipped-exercise copy, but neither model reliably used enough exact required fact anchors. Hermes also echoed model-facing meta-language such as "approved facts." This confirmed that the next issue was anchor priority and forbidden-term echo, not missing context.

## Decision

Keep quote-only context isolation and required fact anchors, but make required anchors the first and dominant evidence block in the prompt.

Do not expose forbidden meta terms to the model. Keep those terms backend-side for validation only.

Do not promote the provider yet.

## Model-facing payload behavior

`TrainingReportSectionModelQuoteContext` still exposes a small isolated payload for debug/runtime inspection, but it no longer includes `forbidden_meta_terms`.

The payload includes:

- `required_quote_name`
- `required_anchor_count`
- `required_fact_anchors`
- `approved_workout_names`
- `approved_exercise_names`
- `approved_training_numbers`
- `supporting_training_details`
- `coaching_intent`
- `tone_guidance`
- `section_contract_reminder`

`supporting_training_details` replaces the model-facing `approved_quote_facts` label so the model is less likely to echo phrases that the validator rejects.

## Prompt behavior

The prompt no longer dumps the full model-facing JSON payload. Instead, it presents separate blocks in priority order:

1. Required training details
2. Required detail placement rules
3. Required quote name
4. Allowed workout names
5. Allowed exercise names
6. Allowed supporting training details
7. Allowed numbers
8. Output contract and safety rules

The prompt instructs:

- `key_observations[0]` must be exactly one required training detail.
- `key_observations[1]` must be exactly one different required training detail when at least two are available.
- The full response must include at least `required_anchor_count` exact required training details.
- The model may use the remaining narrative fields for coach-like interpretation.

The prompt does not include a forbidden meta-language list, because prior runtime QA showed models may echo terms that appear in the prompt.

## Validation behavior

Existing v4 validation remains, with stricter placement:

- If one anchor is required, `key_observations[0]` must exactly match a required training detail.
- If two anchors are required, `key_observations[0]` and `key_observations[1]` must exactly match two different required training details.
- Exact matching remains character-for-character.
- Fuzzy paraphrase does not satisfy required anchors.
- Planned/supporting details do not satisfy the requirement unless they were selected as required anchors.
- Meta-copy remains rejected.
- Unsupported completion/adherence/trend/skipped/recovery/fatigue/progression claims remain rejected.
- Unapproved names and numbers remain rejected.
- Deterministic fallback remains unchanged.

## Runtime diagnostics

Spike output now includes:

- `matched_required_fact_anchors`
- `required_anchor_count`
- `missing_required_anchor_count`

This makes runtime QA easier by showing whether the model missed anchors entirely, matched only one anchor, placed anchors in the wrong fields, or passed anchor count but failed another rule.

## Scope preserved

No production provider was added. No full report assembly wiring was added. No Streamlit behavior changed. No report persistence changed. No workout generation changed. No CrewAI behavior changed. No live Ollama calls occur in pytest.

## Runtime QA expectation

After v4.1, a provider-approved result should have:

- `candidate_parse_status: success`
- `candidate_validation_status: success`
- `fallback_used: false`
- `final_section_source: provider_approved`
- at least two matched required fact anchors when two are required
- first two `key_observations` equal to exact required training details

If the model still fails, `matched_required_fact_anchors` and the key-observation placement errors should identify the next failure mode without loosening validation.
