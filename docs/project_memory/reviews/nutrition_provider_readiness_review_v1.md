# Nutrition Provider Readiness Review v1

Status: PARTIAL_READY_NEEDS_BACKEND_GAPS

Date: 2026-06-18

Branch: `feature/training-evidence-claim-service`

Latest known commit: `18e41e9 Add lightweight project memory layer`

Review type: Design/review only. No nutrition provider implementation.

## Purpose

Review whether the accepted Nutrition Report Section Boundary v1 is strong enough to support a future opt-in nutrition provider path.

This is not provider implementation. This review does not promote qwen3, does not call `direct_ollama` from nutrition, and does not change runtime behavior.

## Files inspected

Nutrition report section boundary:

- `models/nutrition_report_section_models.py`
- `services/nutrition_report_section_service.py`
- `tests/test_nutrition_report_section_boundary.py`
- `docs/nutrition_report_section_boundary_v1.md`

Nutrition evidence and guidance:

- `models/nutrition_target_vs_actual_models.py`
- `services/nutrition_target_vs_actual_service.py`
- `models/nutrition_food_suggestion_models.py`
- `services/nutrition_food_suggestion_service.py`
- `models/nutrition_target_models.py`
- `models/nutrition_target_formula_models.py`
- `services/nutrition_target_formula_service.py`
- `services/nutrition_target_formula_validation_service.py`

Existing nutrition explanation/provider-adjacent work, inspected but not promoted:

- `models/ai_nutrition_explanation_models.py`
- `services/ai_nutrition_explanation_service.py`
- `services/ai_nutrition_explanation_validation_service.py`
- `docs/direct_ollama_nutrition_explanation_provider.md`

Full-report ownership/memory context:

- `services/full_report_section_registry_service.py`
- `docs/full_report_section_registry_v1.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/section_registry_summary.md`
- `docs/project_memory/ai_boundaries.md`
- `docs/project_memory/backend_truth_contract.md`

## Executive finding

Nutrition is ready for provider contract design, but not ready for provider implementation or promotion.

The current boundary has the right shape:

- backend-owned evidence context
- approved claim objects
- deterministic section rendering
- public section fields
- section validation
- safe fallback
- section registry ownership as Level 3

However, before a nutrition provider path should be implemented, the project still needs a stricter provider-specific parser/validator contract, exact supported-output schema, safe runtime metadata shape, and provider-runtime QA plan.

Recommended status:

`PARTIAL_READY_NEEDS_BACKEND_GAPS`

## Current nutrition boundary summary

The current Nutrition Report Section is distinct from Nutrition Target Display.

`nutrition_target_display` remains Level 2 and only displays backend-approved targets/display flags.

`nutrition_report_section` is Level 3 and owns a richer report-section boundary. It uses backend-owned target-vs-actual summaries, approved nutrition guidance, approved food suggestions, and approved nutrition claims.

It is not provider-integrated and does not call `direct_ollama`.

## Current backend-owned nutrition evidence

The current backend-owned evidence includes:

### Target-vs-actual summary

Owned by:

- `services.nutrition_target_vs_actual_service.build_target_vs_actual_nutrition_summary`
- `models.nutrition_target_vs_actual_models.TargetVsActualNutritionSummary`

Evidence fields include:

- `user_id`
- `date`
- `nutrition_actuals`
- `logging_summary`
- `comparisons`
- `logging_completeness`
- `confidence`
- `reason_codes`
- `limitations`

### Nutrition actuals

Owned by:

- `services.nutrition_target_vs_actual_service.build_nutrition_actuals`
- `models.nutrition_target_vs_actual_models.NutritionActuals`

Evidence fields include:

- logged calories
- logged protein
- logged carbohydrates
- logged fat
- logged fiber
- logged meal count
- entry count
- source count
- missing nutrient entry counts
- reason codes

Current limitation:

Missing nutrient values are not coerced to zero. This is correct and should remain true.

### Logging summary

Owned by:

- `services.nutrition_target_vs_actual_service._logging_summary_from_actuals`
- `models.nutrition_target_vs_actual_models.NutritionLoggingSummary`

Supported logging states include:

- `no_logs`
- `partial_day`
- `likely_incomplete`
- `reasonably_complete`
- `complete_enough`

The service derives confidence and limitations from entry count and missing nutrient fields.

### Target comparisons

Owned by:

- `services.nutrition_target_vs_actual_service._build_comparison`
- `models.nutrition_target_vs_actual_models.NutritionTargetComparison`

Supported nutrients:

- calories
- protein
- carbohydrates
- fat

Comparison evidence includes:

- actual value
- target min/max
- delta min/max
- percent of target
- target status
- comparison availability
- confidence
- reason codes
- limitations

### Approved nutrition guidance

Owned by:

- `services.nutrition_target_vs_actual_service.build_approved_nutrition_guidance`
- `models.nutrition_target_vs_actual_models.ApprovedNutritionGuidance`

Guidance fields include:

- `summary_message`
- `protein_guidance`
- `calorie_guidance`
- `macro_guidance`
- `logging_guidance`
- `confidence`
- `reason_codes`
- `limitations`

### Approved food suggestions

Owned by:

- `services.nutrition_food_suggestion_service.build_approved_nutrition_food_suggestions`
- `models.nutrition_food_suggestion_models.ApprovedNutritionFoodSuggestions`

Evidence includes canonical food suggestions derived from approved macro-gap and canonical food data.

Important boundary:

Food suggestions are canonical and bounded. The provider must not invent foods, servings, macros, or meal plans.

### Nutrition report evidence context

Owned by:

- `services.nutrition_report_section_service.build_nutrition_report_evidence_context`
- `models.nutrition_report_section_models.NutritionReportEvidenceContext`

The context composes:

- `target_vs_actual_summary`
- `approved_nutrition_guidance`
- `approved_food_suggestions`
- confidence
- reason codes
- limitations

## Current approved nutrition claims

Approved claim model:

- `models.nutrition_report_section_models.ApprovedNutritionClaim`

Claim derivation owner:

- `services.nutrition_report_section_service.derive_approved_nutrition_claims`

Current approved claim types:

- `target_available`
- `actuals_logged`
- `logging_complete_enough`
- `logging_incomplete`
- `protein_below_target`
- `protein_near_target`
- `calories_below_target`
- `calories_near_target`
- `calories_above_target`
- `food_suggestion_available`
- `confidence_limited_by_missing_logs`

Each claim carries:

- claim type
- public claim text
- evidence fields
- confidence
- reason codes
- limitations

## Current deterministic fallback behavior

Deterministic section builder:

- `services.nutrition_report_section_service.build_deterministic_nutrition_report_section`

Fallback source constant:

- `deterministic_nutrition_report_section_fallback`

The fallback creates an `ApprovedNutritionReportSection` from approved claims and deterministic helper rendering.

Fallback handles:

- no logs
- incomplete logs
- missing nutrition targets
- missing actuals
- limited confidence
- unavailable food suggestions
- validation failure

Validation failure fallback owner:

- `services.nutrition_report_section_service._safe_limited_section`

This is a good foundation for future provider fallback.

## Current public Nutrition Report Section fields

Candidate and Approved section fields currently match:

- `section_summary`
- `intake_snapshot`
- `target_alignment`
- `logging_quality`
- `practical_food_focus`
- `next_nutrition_action`
- `limitations_context`
- `confidence`
- `reason_codes`

Approved-only fields include:

- `section_id`
- `approved_claims`
- `source`

These are suitable as the first provider candidate schema, but the provider path should not receive permission to invent claims beyond the approved-claims list.

## Current validation rules

Nutrition report validation owner:

- `services.nutrition_report_section_service.validate_nutrition_report_section`

Current validation checks:

1. Forbids unsafe public nutrition language.
2. Rejects protein target-alignment language if protein comparison is unavailable.
3. Rejects calorie target-alignment language if calorie comparison is unavailable.
4. Delegates target-vs-actual guidance validation to `validate_target_vs_actual_nutrition_summary`.

Forbidden language includes:

- severe deficit language
- deficiency language
- metabolism damage language
- keto/intermittent fasting prescriptions
- supplement language
- fatigue-causation language
- weight-loss guarantees
- noncompliance/shame language
- bad-diet language
- meal skipping/compensation language
- medical diagnosis/advice language

## Validator readiness

Current validator is good enough for deterministic section safety and provider-readiness design.

It is not yet strict enough for provider implementation.

Before provider implementation, add provider-candidate validation for:

1. Required output keys only.
2. No extra provider keys.
3. Confidence must not exceed evidence confidence.
4. Provider text must reference only approved claim types or approved field values.
5. Food suggestion text must use only approved canonical suggestions and approved serving ranges.
6. Numeric values must be drawn only from approved evidence fields.
7. Provider cannot say target changes occurred.
8. Provider cannot create meal plans or prescribe diets.
9. Provider cannot make body-composition, medical, supplement, deficiency, fatigue-causation, adherence, compliance, or outcome-guarantee claims.
10. Provider cannot convert limited evidence into strong conclusions.
11. Provider cannot mention internal/debug terms, raw output, parser, validator, schema, or provider details.
12. Provider cannot use Nutrition Target Display hidden values to unlock blocked public targets.

## Safely supported nutrition claims today

Current backend can safely support these claims when evidence is present:

- Nutrition entries are logged for the date.
- Nutrition logging is complete enough for cautious target comparison.
- Nutrition logging is incomplete, so conclusions should stay limited.
- Target comparison is available for a nutrient.
- Protein appears below the approved target based on logged entries.
- Protein appears near the approved target based on logged entries.
- Calories appear below the approved range based on complete-enough logs.
- Calories appear near the approved range based on complete-enough logs.
- Calories appear above the approved range based on complete-enough logs.
- A canonical food suggestion is available for an approved nutrition gap.
- Nutrition confidence is limited by logging completeness or missing values.

## Unsupported nutrition claims today

Provider output must not claim:

- severe caloric deficit
- exact deficit magnitude unless approved evidence explicitly supports it
- nutrient deficiency
- medical diagnosis or treatment
- supplement need or supplement recommendation
- metabolism damage
- keto, intermittent fasting, or any diet prescription
- meal plan creation
- meal timing requirements
- fatigue causation
- body composition conclusions
- guaranteed weight loss
- adherence, compliance, discipline, or failure
- that targets were changed, calibrated, or updated
- that a food not in approved suggestions is recommended
- that a serving size not approved by backend is recommended
- that incomplete logs prove actual intake
- that calories/protein are high/low/near when the relevant comparison is unavailable

## Existing provider-adjacent nutrition work

There is existing `AI Nutrition Explanation` work, including direct Ollama documentation and validation services.

That work should be treated as separate from the full-report Nutrition Report Section until Architecture explicitly promotes or adapts it.

Important distinction:

- AI Nutrition Explanation is not the full-report Nutrition Report Section provider path.
- Existing nutrition explanation provider work should be mined for useful parser/validator lessons, not blindly reused as full-report section ownership.

## Future CandidateNutritionReportSection needs

The existing `CandidateNutritionReportSection` is close to the future provider output shape.

Future provider candidate should likely require exactly:

- `section_summary`
- `intake_snapshot`
- `target_alignment`
- `logging_quality`
- `practical_food_focus`
- `next_nutrition_action`
- `limitations_context`
- `confidence`
- `reason_codes`

Additional provider metadata should remain outside the public candidate object.

Provider candidate should not include:

- raw evidence context
- raw food entries
- raw target calculations
- raw provider output
- validation errors
- parser metadata
- model metadata
- hidden target values
- unapproved food suggestions
- meal plans

## Future parser/validator boundary needed

A future nutrition provider boundary should follow this shape:

1. Build `NutritionReportEvidenceContext`.
2. Derive `ApprovedNutritionClaim[]`.
3. Build a compressed provider-safe context containing only approved claims, allowed public fields, approved suggestions, confidence, and limitations.
4. Call opt-in provider only when explicitly configured.
5. Parse strict JSON into `CandidateNutritionReportSection`.
6. Reject markdown wrappers, missing keys, extra keys, malformed JSON, wrong types, invalid confidence, or empty fields.
7. Validate candidate against evidence and approved claims.
8. Approve into `ApprovedNutritionReportSection` only if all checks pass.
9. Otherwise use deterministic nutrition section fallback.
10. Expose provider details only through safe debug/runtime metadata, never public report text.

## Safe metadata for future provider path

Future safe metadata may include:

- `nutrition_section_source`
- `nutrition_provider_enabled`
- `nutrition_provider_attempted`
- `nutrition_selected_provider`
- `nutrition_selected_model`
- `nutrition_fallback_used`
- `nutrition_fallback_reason`
- `nutrition_validation_status`
- `nutrition_validation_errors_count`
- `nutrition_provider_latency_ms`
- `nutrition_claim_count`
- `nutrition_confidence`
- `nutrition_report_section_registry_maturity`

Do not persist:

- raw provider output
- raw prompt
- raw schema
- raw context
- raw food rows
- validation error details in public history
- provider payload
- parser traces
- stack traces
- raw exception text

## Runtime QA needed before provider promotion

Before any nutrition provider promotion, run at least:

### Deterministic/default QA

- Nutrition provider disabled/default.
- Full report generation still succeeds.
- Nutrition does not call `direct_ollama`.
- Training provider behavior unchanged.
- Report history persists safely.

### Provider opt-in QA

For seeded users/dates covering:

- no nutrition logs
- partial/incomplete logs
- complete-enough logs
- protein below target
- protein near target
- calorie below target
- calorie near target
- calorie above target
- unavailable targets
- unavailable food suggestions
- approved food suggestion available

Expected output fields:

- job status
- provider enabled/attempted
- selected provider/model
- nutrition section source
- fallback used/reason
- validation status
- validation error count
- claim count
- section confidence
- safe metadata keys
- raw/debug terms absent from public report
- raw/debug terms absent from persisted history
- forbidden nutrition terms absent
- non-training provider ownership unchanged unless Architecture explicitly approves nutrition provider integration

### Negative QA

Provider candidates should be force-tested against:

- invented calorie/protein target
- invented food
- invented serving size
- meal plan
- supplement advice
- medical/deficiency claim
- fatigue-causation claim
- weight-loss guarantee
- target-change claim
- compliance/shame language
- raw/debug metadata leakage
- confidence inflation
- unapproved numeric values

## Is qwen2.5:3b likely enough for strict nutrition section testing?

Likely yes for initial strict-contract testing, but not for final product voice judgment.

Rationale:

- qwen2.5:3b has already been practical for strict Training provider testing.
- Nutrition candidate fields are short and structured.
- A strict JSON parser and validator can safely reject failures.
- The goal of first provider tests should be boundary behavior, not premium voice quality.

Expected limitation:

qwen2.5:3b may sound generic or conservative. That is acceptable for boundary testing but not a final product voice win.

## Gaps before qwen3/product voice testing

Before qwen3 nutrition/product voice testing:

1. Add nutrition provider parser/validator contract.
2. Define provider-safe context compression.
3. Add exact approved-claim gating for each output field.
4. Add numeric-value validation against approved evidence.
5. Add approved-food and serving-size validation.
6. Add confidence ceiling validation.
7. Add public-safe nutrition metadata allowlist.
8. Add no-raw-output persistence tests.
9. Add provider failure/fallback tests.
10. Add runtime QA matrix for nutrition scenarios.
11. Add product-copy checks for generic, repetitive, or overly clinical nutrition language.
12. Keep qwen3 experimental until qwen2.5 boundary behavior is stable.

## Recommended next milestone

Recommended next milestone:

`Nutrition Provider Contract Design v1`

Scope:

- Design the provider-safe context shape.
- Design exact `CandidateNutritionReportSection` provider JSON schema.
- Design validator rules in detail.
- Design safe metadata allowlist.
- Design pytest/runtime QA matrix.
- Do not call Ollama yet.

Do not implement provider voice until Architecture accepts the provider contract design.

## Final readiness status

`PARTIAL_READY_NEEDS_BACKEND_GAPS`

Nutrition has a strong enough backend-owned boundary to proceed into provider contract design.

Nutrition is not ready for qwen/provider implementation yet.
