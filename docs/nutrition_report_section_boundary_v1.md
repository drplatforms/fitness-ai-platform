# Nutrition Report Section Boundary v1

Status: Implemented / local regression tested / pending Architecture review

Branch: `feature/training-evidence-claim-service`

## Purpose

Nutrition Report Section Boundary v1 creates the backend-owned boundary for a
future full-report Nutrition voice section. It does **not** implement a qwen,
direct-Ollama, CrewAI, or other provider path.

The boundary follows the project rule:

```text
Backend owns truth.
AI explains approved truth.
Validator enforces reality.
```

The Nutrition Report Section is distinct from the existing Nutrition Target
Display. Target Display is an input/display contract; it is not the final
nutrition voice section.

## Current section status

- `nutrition_target_display` remains Level 2 derived-evidence display.
- `nutrition_report_section` is registered as a distinct provider-integrated
  boundary after Nutrition Provider Level 5 Promotion v1.
- `training` remains a separate Level 5 provider-integrated full-report section.
- Nutrition still calls `direct_ollama` only through explicit opt-in gates.
- Nutrition provider-approved output is tracked separately from fallback or disabled-gate deterministic output.

## New model boundary

Added:

- `NutritionReportEvidenceContext`
- `ApprovedNutritionClaim`
- `CandidateNutritionReportSection`
- `ApprovedNutritionReportSection`
- `NutritionReportSectionValidationResult`

The approved public section fields are:

- `section_summary`
- `intake_snapshot`
- `target_alignment`
- `logging_quality`
- `practical_food_focus`
- `next_nutrition_action`
- `limitations_context`

## Evidence sources

The boundary reads backend-owned nutrition outputs only:

- `TargetVsActualNutritionSummary`
- `ApprovedNutritionGuidance`
- `ApprovedNutritionFoodSuggestions`

The boundary does not read raw food logs directly for public wording. Raw logged
food/source payloads remain below the approved target-vs-actual and canonical
food suggestion services.

## Approved claim types

V1 approved nutrition claim types:

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

Claims are derived only when the underlying approved target/actual/completeness
objects support them. For example, protein-below-target claims require an
available protein comparison, and calorie status claims require an available
calorie comparison.

## Deterministic fallback

The deterministic nutrition section fallback is safe when:

- no food logs exist for the date
- logs appear incomplete
- target comparisons are unavailable
- calories are blocked by confidence/completeness gates
- food suggestions are unavailable
- validation rejects unsupported wording

Fallback copy remains conservative and asks for better logging when confidence is
limited.

## Validation rules

The nutrition section validator rejects unsupported or unsafe nutrition language,
including:

- severe/critical deficit claims
- deficiency claims
- metabolism damage claims
- keto/intermittent-fasting prescriptions
- supplement recommendations or assumptions
- claims that nutrition explains fatigue
- weight-loss guarantees
- compliance/shame framing
- medical/disease claims
- unsupported protein target claims
- unsupported calorie target claims

Provider implementations in the future must pass this section validator before a
Nutrition Report Section can become approved and renderable.

## Relationship to future provider voice

The intended future path is:

```text
nutrition source logs
→ target-vs-actual summary
→ approved guidance
→ approved food suggestions
→ NutritionReportEvidenceContext
→ ApprovedNutritionClaim[]
→ provider candidate section, later only if approved
→ nutrition section validator
→ ApprovedNutritionReportSection
→ full report composition
```

Not:

```text
raw food logs
→ qwen writes nutrition advice
→ report renders it
```

## Non-goals preserved

This milestone did not:

- implement qwen provider for nutrition
- promote qwen3
- make `direct_ollama` default
- change Streamlit
- change food/catalog data
- change nutrition target formulas
- add meal planning
- change report persistence behavior broadly
- make Grounded Recommendation provider-owned
- make Nutrition Target Display the final voice section

## Runtime expectations

Runtime QA can remain light unless full report behavior changes materially.
Expected behavior:

- Training remains a provider-integrated full-report section.
- Nutrition Report Section is provider-integrated only when approved provider Nutrition content rendered for that report.
- Fallback and disabled-gate Nutrition reports do not imply provider-approved Nutrition content.
- Section registry metadata includes `nutrition_report_section`.
- No raw/debug/provider output is public or persisted publicly.
