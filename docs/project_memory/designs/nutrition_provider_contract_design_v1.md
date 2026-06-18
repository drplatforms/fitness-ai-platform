# Nutrition Provider Contract Design v1

Status: DESIGN COMPLETE / NOT IMPLEMENTED

Date: 2026-06-18

Branch: `feature/training-evidence-claim-service`

Latest known commit before design: `e6b62c1 Add developer commit workflow helper`

Design type: Provider contract design only. No nutrition provider execution.

## Purpose

Define the provider-safe contract required before Nutrition Report Section can receive an opt-in AI/provider explanation path.

This design does not implement `direct_ollama`, does not call a model, does not promote qwen3, and does not mark Nutrition as provider-integrated.

The design follows the project doctrine:

- Backend owns truth.
- AI explains approved truth.
- Validator enforces reality.
- The coach must sound right and be right.

## Current readiness status

Nutrition is ready for provider contract design.

Nutrition is not ready for provider implementation or promotion until the parser, validator, metadata, tests, and runtime QA path described here are implemented.

Recommended current status:

`READY_FOR_CONTRACT_SCAFFOLDING_NOT_PROVIDER_EXECUTION`

## Current source boundary

The existing Nutrition Report Section boundary is Level 3.

Current owned files:

- `models/nutrition_report_section_models.py`
- `services/nutrition_report_section_service.py`
- `tests/test_nutrition_report_section_boundary.py`
- `docs/nutrition_report_section_boundary_v1.md`

Current provider-adjacent files inspected but not promoted:

- `models/ai_nutrition_explanation_models.py`
- `services/ai_nutrition_explanation_service.py`
- `services/ai_nutrition_explanation_validation_service.py`
- `docs/direct_ollama_nutrition_explanation_provider.md`

Full-report ownership files:

- `services/full_report_section_registry_service.py`
- `docs/full_report_section_registry_v1.md`

## Non-goals

Do not implement any of the following in this milestone:

- Nutrition provider execution.
- Nutrition `direct_ollama` calls.
- qwen3 nutrition testing.
- qwen3 promotion.
- Provider-integrated Nutrition registry status.
- Nutrition target formula changes.
- New foods.
- Meal planning.
- Streamlit changes.
- Persistence behavior changes.
- Report generation behavior changes.
- Training provider behavior changes.
- RAG, embeddings, or agent orchestration.

## Provider-safe nutrition context shape

A future provider should receive a compressed backend-owned context only.

Proposed context object name:

`NutritionProviderSafeContext`

Proposed schema version:

`nutrition_provider_context_v1`

### Context JSON shape

```json
{
  "schema_version": "nutrition_provider_context_v1",
  "section_id": "nutrition_report_section",
  "user_id": 102,
  "report_date": "2026-06-14",
  "confidence_ceiling": "Low",
  "logging": {
    "logging_completeness": "partial_day",
    "logged_meal_count": 1,
    "entry_count": 1,
    "source_count": 1,
    "missing_nutrient_fields": ["calories", "carbohydrates", "fat"]
  },
  "approved_actuals": {
    "calories": null,
    "protein_g": 35,
    "carbs_g": null,
    "fat_g": null,
    "fiber_g": null
  },
  "approved_comparisons": {
    "calories": {
      "comparison_available": false,
      "target_status": "unavailable",
      "actual": null,
      "target_min": null,
      "target_max": null,
      "confidence": "Low"
    },
    "protein": {
      "comparison_available": false,
      "target_status": "unavailable",
      "actual": 35,
      "target_min": null,
      "target_max": null,
      "confidence": "Low"
    }
  },
  "approved_guidance": {
    "summary_message": "Nutrition logging is incomplete, so conclusions should stay limited.",
    "protein_guidance": "Protein comparison is limited until approved protein targets and logged protein are available.",
    "calorie_guidance": "Nutrition logging is incomplete, so calorie conclusions should stay limited.",
    "macro_guidance": "Macro comparisons are limited until logging is more complete.",
    "logging_guidance": "Logged intake is incomplete, so avoid making bigger nutrition changes from this day alone."
  },
  "approved_claims": [
    {
      "claim_type": "logging_incomplete",
      "claim_text": "Nutrition logging is incomplete, so conclusions should stay limited.",
      "evidence_fields": ["logging_summary.logging_completeness"],
      "confidence": "Low",
      "reason_codes": ["nutrition_logging_incomplete"],
      "limitations": ["Nutrition logging appears partial for this date."]
    }
  ],
  "approved_food_suggestions": [],
  "limitations": ["Nutrition logging appears partial for this date."],
  "reason_codes": ["nutrition_report_section_evidence_context", "partial_nutrition_logging"],
  "forbidden_claims": [
    "deficiency",
    "medical_claim",
    "supplement_recommendation",
    "severe_deficit",
    "diet_diagnosis",
    "meal_plan",
    "guaranteed_weight_loss",
    "fatigue_causation",
    "adherence_or_compliance_judgment",
    "target_change_or_calibration_claim"
  ]
}
```

### Context rules

The context must include only backend-approved public-safe values.

Allowed:

- Report date.
- Section id.
- Confidence ceiling.
- Logging completeness.
- Logged meal count.
- Entry count.
- Source count.
- Missing nutrient fields.
- Approved actual values when known.
- Approved target comparison values when comparison is available.
- Approved guidance strings.
- Approved nutrition claims.
- Approved canonical food suggestions.
- Reason codes and limitations.

Forbidden:

- Raw food rows.
- Raw SQL.
- Raw source payloads.
- Provider debug payloads.
- Unapproved target values.
- Hidden targets blocked by display flags.
- Raw prompt text.
- Raw provider output.
- Internal validation errors.
- Any provider metadata not explicitly allowlisted.

## Exact CandidateNutritionReportSection JSON schema

A future provider must return exactly one JSON object.

No markdown fences.
No wrapper object.
No prose before or after JSON.
No extra keys.
No missing keys.

### Required JSON object

```json
{
  "section_summary": "string",
  "intake_snapshot": "string",
  "target_alignment": "string",
  "logging_quality": "string",
  "practical_food_focus": "string",
  "next_nutrition_action": "string",
  "limitations_context": "string",
  "confidence": "Limited|Low|Moderate|High",
  "reason_codes": ["string"]
}
```

### Required keys

- `section_summary`
- `intake_snapshot`
- `target_alignment`
- `logging_quality`
- `practical_food_focus`
- `next_nutrition_action`
- `limitations_context`
- `confidence`
- `reason_codes`

### Disallowed keys

The provider must not return:

- `approved_claims`
- `metadata`
- `raw_output`
- `debug`
- `prompt`
- `schema`
- `provider`
- `model`
- `user_id`
- `report_date`
- `nutrition_targets`
- `meal_plan`
- `supplements`
- `diagnosis`

The backend owns all approved claims, identity, date, metadata, source, and persistence fields.

## Parser rules

Parser status values should be explicit and safe:

- `not_attempted`
- `parsed`
- `missing_required_keys`
- `extra_keys_detected`
- `invalid_json`
- `wrapper_object_detected`
- `type_mismatch`
- `invalid_enum_value`
- `empty_or_placeholder_content`
- `markdown_or_prose_wrapper_detected`

### Parser requirements

The parser must reject:

1. Non-JSON output.
2. Markdown code fences.
3. Text before or after JSON.
4. Wrapper objects such as `{ "nutrition_report_section": { ... } }`.
5. Missing required keys.
6. Extra keys.
7. Non-string section fields.
8. Non-list `reason_codes`.
9. Non-string items in `reason_codes`.
10. Empty strings.
11. Placeholder strings such as `TBD`, `N/A`, `placeholder`, `lorem ipsum`, or `example`.
12. Invalid confidence enum values.

The parser must not try to repair unsafe output for public rendering.

If parsing fails, the section must use deterministic fallback.

## Validator rules

Validation status values should be explicit and safe:

- `not_attempted`
- `approved`
- `rejected`
- `fallback_used`

Validation error details may exist internally, but public/persisted metadata should store only `validation_errors_count` unless Architecture explicitly approves safe error codes.

### Global validator rules

The validator must reject provider output that:

- Mentions unsupported claims.
- Uses medical, supplement, deficiency, or disease language.
- Claims severe deficit or severe surplus.
- Claims fatigue causation.
- Claims guaranteed weight loss or body composition outcomes.
- Claims adherence, noncompliance, failure, shame, or moral judgment.
- Recommends keto, fasting, supplements, skipping meals, or compensation.
- Invents foods, servings, macros, targets, or target changes.
- Uses angle-bracket artifacts or test/placeholder copy.
- Exceeds the approved confidence ceiling.
- Includes raw/debug/internal terms.

## Field-level approved-claim gating

Each provider field must be gated by approved evidence and claims.

### `section_summary`

Allowed:

- High-level summary using approved logging status, approved target alignment, approved food suggestion availability, and limitations.

Requires at least one of:

- `actuals_logged`
- `logging_incomplete`
- `logging_complete_enough`
- `protein_below_target`
- `protein_near_target`
- `calories_below_target`
- `calories_near_target`
- `calories_above_target`
- `confidence_limited_by_missing_logs`

Reject if it summarizes unsupported body composition, medical, fatigue, or adherence conclusions.

### `intake_snapshot`

Allowed:

- Logged entry count.
- Logged meal count.
- Approved actual values when non-null and public-safe.
- Statement that logs are missing or incomplete.

Requires one of:

- `actuals_logged`
- `logging_incomplete`
- `confidence_limited_by_missing_logs`

Reject if it treats missing nutrient values as zero.

### `target_alignment`

Allowed:

- Protein or calorie comparison only when matching approved comparison claim exists.
- “Comparison is limited/unavailable” when no comparison claim exists.

Requires one or more of:

- `target_available`
- `protein_below_target`
- `protein_near_target`
- `calories_below_target`
- `calories_near_target`
- `calories_above_target`
- `confidence_limited_by_missing_logs`

Reject if it claims target alignment without comparison availability.

### `logging_quality`

Allowed:

- Logging complete enough, incomplete, partial, or missing.
- Confidence limitation language.

Requires one of:

- `logging_complete_enough`
- `logging_incomplete`
- `confidence_limited_by_missing_logs`

Reject shame/compliance language.

### `practical_food_focus`

Allowed:

- Canonical food suggestion when approved.
- “No specific food suggestion is approved yet” when not approved.

Requires:

- `food_suggestion_available` for naming a food.

Reject invented foods, invented serving sizes, meal plans, or supplement suggestions.

### `next_nutrition_action`

Allowed:

- Log a complete day.
- Keep conclusions limited.
- Use an approved canonical food suggestion.
- Keep targets unchanged.
- Continue collecting data.

Requires supporting claim or limitation.

Reject target changes, calorie cuts, meal plans, supplement recommendations, or guaranteed outcomes.

### `limitations_context`

Allowed:

- Approved limitations and confidence ceiling.
- Missing logs / incomplete logs / unavailable comparison language.

Requires:

- At least one context limitation or limited-confidence reason code when confidence is `Limited` or `Low`.

Reject vague “consult your doctor” boilerplate unless a medical safety policy explicitly requires it; this section should not make medical claims.

## Numeric-value validation

The validator should scan numeric values in provider output.

Allowed numeric values:

- Logged meal count.
- Entry count.
- Source count.
- Approved actual nutrient values when non-null.
- Approved target min/max only when comparison is available and display-approved.
- Approved food serving quantities only when sourced from canonical food suggestions.

Rules:

1. A number in provider output must match an allowed numeric value from context.
2. Units must match the evidence meaning.
3. Missing nutrient fields must not be rendered as `0`.
4. Delta claims must be rejected unless explicit delta fields are approved for provider display.
5. Percent-of-target claims must be rejected unless percent fields are approved for provider display.
6. “Severe deficit” or exact deficit magnitude must be rejected in v1.
7. Calorie/protein target claims must be rejected when comparison is unavailable.

## Logging-completeness confidence ceilings

Provider confidence cannot exceed backend evidence confidence.

Recommended ceilings:

| Logging state | Max provider confidence |
|---|---|
| `no_logs` | `Limited` |
| `partial_day` | `Low` |
| `likely_incomplete` | `Low` |
| `reasonably_complete` | `Moderate` |
| `complete_enough` | `High` if summary confidence is High, otherwise summary confidence |

If context confidence is lower than the table ceiling, context confidence wins.

## Canonical food validation

A provider may mention a food only if it appears in `approved_food_suggestions.suggestions`.

Required exact-match fields for food mentions should include, when available:

- canonical food display name
- serving description
- nutrient focus or macro gap
- reason code

Rules:

1. No invented food names.
2. No invented serving sizes.
3. No invented macros.
4. No meal-plan structure.
5. No supplement substitutions.
6. No claim that one food fixes the entire diet.
7. No claim that the user must eat the food.

## Unsupported claim rejection list

The provider validator must reject language that implies:

- Severe deficit.
- Critical deficit.
- Nutrient deficiency.
- Medical diagnosis.
- Medical treatment.
- Disease claim.
- Supplement recommendation.
- Metabolic damage.
- Required keto or fasting.
- Required meal timing.
- Meal planning.
- Fatigue causation.
- Weight-loss guarantee.
- Body-composition conclusion.
- Noncompliance.
- Adherence judgment.
- Shame or failure.
- Target changes.
- Calorie/protein prescriptions not already approved.
- Invented food, serving, macro, or target values.

## Safe metadata allowlist

A future provider result may produce internal debug metadata, but persisted public report metadata must be allowlisted.

Safe persisted nutrition provider metadata fields:

- `nutrition_section_provider_enabled`
- `nutrition_section_provider_attempted`
- `nutrition_section_selected_provider`
- `nutrition_section_selected_model`
- `nutrition_section_source`
- `nutrition_section_fallback_used`
- `nutrition_section_fallback_reason`
- `nutrition_section_validation_status`
- `nutrition_section_validation_errors_count`
- `nutrition_section_latency_ms`
- `nutrition_section_context_schema_version`
- `nutrition_section_candidate_schema_version`
- `nutrition_section_claim_count`
- `nutrition_section_confidence`
- `nutrition_section_provider_contract_version`

Do not persist publicly:

- raw provider output
- raw provider output preview
- prompt
- provider-safe context payload
- validation error text/list
- parser error text/list
- stack traces
- raw exception text
- provider request payload
- provider response payload

## Provider fallback design

Fallback should be deterministic and safe.

Fallback must trigger when:

- provider disabled
- provider not configured
- provider timeout
- provider exception
- invalid JSON
- parser rejection
- validator rejection
- confidence ceiling violation
- unsupported nutrition claim detected
- raw/debug leakage detected

Fallback output:

- Use `build_deterministic_nutrition_report_section(...)`.
- Preserve approved backend claims.
- Record safe fallback metadata only.
- Do not expose raw provider error text.
- Do not persist raw provider output.

## Pytest plan

Future implementation should add focused tests, likely:

`tests/test_nutrition_provider_contract.py`

Required test groups:

1. Provider-safe context contains only approved fields.
2. Provider-safe context excludes raw food rows/debug payloads/unapproved targets.
3. Candidate schema accepts exact required JSON object.
4. Parser rejects missing keys.
5. Parser rejects extra keys.
6. Parser rejects wrapper object.
7. Parser rejects markdown fenced JSON.
8. Parser rejects empty/placeholder fields.
9. Parser rejects invalid confidence enum.
10. Validator approves output that uses only approved claims.
11. Validator rejects protein/calorie claims without comparison availability.
12. Validator rejects unsupported medical/supplement/deficiency claims.
13. Validator rejects shame/compliance language.
14. Validator rejects invented foods/servings.
15. Validator rejects numeric values not present in approved context.
16. Validator enforces confidence ceiling.
17. Fallback used when parser fails.
18. Fallback used when validator fails.
19. Safe metadata allowlist excludes raw provider output.
20. Nutrition remains non-provider-integrated in full-report section registry.
21. Training remains the only Level 5 provider-integrated section.
22. No live Ollama calls occur in pytest.

## Future runtime QA matrix

Runtime QA should not run until provider execution is implemented in a later milestone.

When approved, minimum provider runtime QA should include:

| User/date case | Expected behavior |
|---|---|
| no nutrition logs | deterministic or provider-approved limited section; no target alignment claims |
| partial logs | limited/low confidence; no calorie/protein target claims unless comparisons available |
| complete-enough logs with protein gap | provider may explain approved protein gap only |
| complete-enough logs near calorie range | provider may explain approved calorie alignment only |
| canonical food suggestion available | provider may mention exact approved canonical suggestion only |
| provider invalid JSON | deterministic fallback, safe metadata |
| provider unsupported claim | deterministic fallback, safe metadata |
| provider timeout | deterministic fallback, safe metadata |

Required runtime output fields:

- job status
- nutrition provider enabled/attempted
- selected provider/model
- nutrition section source
- validation status
- validation error count
- fallback used/reason
- nutrition section metadata keys
- provider-integrated report sections
- raw/debug leakage scan
- persisted history scan
- report date
- decision PASS/FAIL

## qwen2.5 and qwen3 position

`qwen2.5:3b` is likely sufficient for initial strict-contract nutrition provider testing once parser/validator scaffolding exists.

`qwen3` remains experimental only.

Do not test qwen3 nutrition product voice until:

- qwen2.5 strict parser/validator behavior is stable,
- nutrition provider fallback behavior is proven,
- raw/debug persistence is safe,
- and Architecture approves product-voice testing.

## Recommended next milestone

Recommended next milestone:

`Nutrition Provider Contract Scaffolding v1`

Scope:

- Add provider-safe context model.
- Add candidate parser skeleton.
- Add validator skeleton.
- Add safe metadata model/allowlist.
- Add deterministic fallback result wrapper.
- Add tests for parser/validator/fallback.
- Do not call Ollama yet.

Alternative name:

`Nutrition Provider Parser Validator Scaffolding v1`

Do not implement provider execution until scaffolding is accepted.

## Acceptance criteria for this design

Accept Nutrition Provider Contract Design v1 if Architecture agrees that it defines:

- provider-safe nutrition context shape
- exact candidate JSON schema
- strict parser rules
- strict validator rules
- numeric validation policy
- logging confidence ceilings
- canonical food validation policy
- unsupported claim rejection categories
- safe metadata allowlist
- fallback design
- pytest plan
- future runtime QA matrix
- no provider execution
- no qwen3 promotion
