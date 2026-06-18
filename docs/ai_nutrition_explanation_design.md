# AI Nutrition Explanation Design v1

## Project
AI Health Coach

## Milestone
AI Nutrition Explanation Design v1

## Status
Design-only proposal for Architecture / Backend review.

## Goal
Design a bounded AI explanation layer that can explain approved nutrition facts, macro gaps, food suggestions, trend context, and calibration readiness without inventing targets, actuals, foods, servings, macros, or target changes.

## Core Principle
Backend computes and validates facts. AI may generate explanatory copy only from approved backend context.

AI must not:

- determine nutrition targets
- determine nutrition actuals
- invent foods
- invent serving amounts
- invent nutrient values
- invent macro gaps
- invent target changes
- imply calibration has been applied
- provide meal plans in this layer

Backend validation must approve AI output before display. If validation fails, the system must return deterministic fallback copy or no AI explanation.

## Current Approved Backend Inputs
The nutrition explanation layer may only consume approved, public-safe projections from existing deterministic systems.

Allowed context sources:

- `ApprovedMacroTargets`
- `TargetVsActualNutritionSummary`
- `ApprovedNutritionGuidance`
- `ApprovedNutritionFoodSuggestions`
- `NutritionTrendWindow` summary/projection
- `NutritionTargetCalibrationResult` summary/projection
- known `reason_codes`
- known `limitations`
- confidence values
- display flags

The explanation layer should not receive raw database rows, raw food entries, raw source payloads, SQL/debug payloads, private runtime internals, or unvalidated model outputs.

## Proposed Future Flow

```text
Approved nutrition context
→ structured AI explanation context
→ AI candidate explanation
→ parser / validator
→ approved explanation or deterministic fallback
→ public-safe response
```

## Recommended Placement
Design v1 should remain backend-only.

Future implementation should start with a preview/debug endpoint before normal UI exposure.

Recommended future endpoint options:

```text
GET /nutrition/{user_id}/explanation?date=YYYY-MM-DD
```

or, preferably for first implementation:

```text
GET /nutrition/{user_id}/explanation/debug?date=YYYY-MM-DD
```

The debug/preview version allows QA to inspect raw provider metadata and validation decisions without exposing unstable AI text in normal UI.

## Should This Change DailyCoachSynthesis?
Not in design v1.

Recommendation:

- Keep AI nutrition explanation separate from DailyCoachSynthesis until the output contract is accepted.
- Do not enrich DailyCoachSynthesis with AI-generated nutrition explanation in the first implementation.
- DailyCoachSynthesis may continue to consume deterministic approved context, but AI explanation should have its own contract and validator first.

## Provider Strategy
The design should support optional AI providers, but no provider should be required.

Recommended provider behavior:

- deterministic fallback is always available
- AI provider is runtime-configurable
- invalid/missing provider configuration falls back to deterministic copy
- failed AI generation falls back to deterministic copy
- invalid AI output is rejected and replaced with deterministic fallback
- provider metadata is debug-only

Potential future providers:

- deterministic fallback
- CrewAI/Ollama local generation
- other future provider behind the same candidate/validator contract

## Proposed Model Contracts

### NutritionExplanationContext
Public-safe, backend-approved input context for explanation generation.

Suggested fields:

- `user_id`
- `explanation_date`
- `approved_macro_targets`
- `target_vs_actual_summary`
- `approved_nutrition_guidance`
- `approved_food_suggestions`
- `trend_summary`
- `calibration_summary`
- `confidence`
- `reason_codes`
- `limitations`
- `display_flags`

Rules:

- contains only approved backend context
- excludes raw logs and raw rows
- excludes raw source payloads
- excludes unapproved target values
- excludes private/debug metadata in normal mode

### CandidateNutritionExplanation
AI-generated candidate text before validation.

Suggested fields:

- `summary`
- `target_vs_actual_explanation`
- `food_suggestion_explanation`
- `trend_explanation`
- `calibration_explanation`
- `limitations`
- `confidence`

Rules:

- not public-safe until validated
- must not be persisted as approved output before validation
- must be rejected if it invents values or violates safety language

### ApprovedNutritionExplanation
Validated, public-safe explanation.

Suggested fields:

- `summary`
- `nutrition_context`
- `food_suggestion_context`
- `trend_context`
- `calibration_context`
- `limitations`
- `confidence`
- `reason_codes`
- `source`
  - `deterministic_fallback`
  - `ai_validated`

Rules:

- contains only validated wording
- contains no raw internals
- contains no AI/provider metadata in public response
- preserves backend-approved facts exactly

### NutritionExplanationRuntimeMetadata
Debug-only provider/runtime metadata.

Suggested fields:

- `configured_provider`
- `selected_provider`
- `ai_attempted`
- `fallback_used`
- `fallback_reason`
- `candidate_parse_status`
- `candidate_validation_status`
- `validation_errors`
- `raw_output_length`
- `raw_output_preview_truncated`

Rules:

- debug-only
- not included in normal public response
- must not include sensitive raw logs or raw database rows

## Allowed AI Outputs
AI may produce concise explanatory copy such as:

- why a macro appears below, near, or above target
- why comparisons are limited
- why food suggestions are available or limited
- why calibration is or is not ready
- plain-English explanation of target-vs-actual context
- supportive coaching tone using approved facts

Allowed example language:

- “Based on today’s logged meals, protein is below target.”
- “The Nutrition tab has approved food suggestions that may help close the gap.”
- “Calories can be compared because logging is complete enough for guidance.”
- “Food suggestions are limited because logging appears incomplete.”
- “Calibration is not ready yet because more consistent logs or weigh-ins are needed.”
- “Targets are still formula-derived.”
- “The current trend window may support future target refinement.”

## Forbidden AI Outputs
AI must never produce:

- new macro targets
- changed targets
- target mutations
- active calibrated-target claims
- exact maintenance-calorie claims
- foods not present in approved canonical suggestions
- serving sizes not approved by backend
- nutrient estimates not approved by backend
- meal plans
- medical advice
- supplement claims
- fat-loss guarantees
- eating-disorder-style restriction language
- exact physiological certainty
- unsupported causality between one meal/day and performance

Forbidden phrases and patterns include:

- “your true maintenance is exactly X calories”
- “your targets have been changed”
- “calibration has been applied”
- “calibration was applied”
- “targets have been calibrated”
- “calibrated targets are active”
- “you failed”
- “you must cut calories”
- “burn this off”
- “compensate tomorrow”
- “skip meals”
- “your metabolism is damaged”

## Validation Requirements
Any AI-generated candidate explanation must be validated before public display.

Validator should reject output if it:

- includes forbidden phrases
- includes unapproved numeric targets
- includes unapproved serving sizes
- includes food names not present in approved suggestions
- implies target mutation
- implies calibration has been applied
- claims exact maintenance calories
- creates medical/disease claims
- creates supplement recommendations
- creates meal plans
- uses shame/restriction language
- contradicts approved confidence or limitations
- ignores blocked or limited targets

Validator should also verify that:

- numeric values in explanation match approved context
- macro names map to approved display flags
- food suggestions reference approved suggestions only
- trend/calibration wording matches readiness and confidence
- low/limited confidence produces cautious language
- incomplete logging produces limitation language

## Deterministic Fallback
Every explanation path must have a deterministic fallback.

Fallback examples:

### Protein gap
“Based on today’s logged meals, protein is below target. The Nutrition tab has approved food suggestions that may help close the gap.”

### Incomplete logging
“Nutrition guidance is limited because logging appears incomplete for this date.”

### Calibration not ready
“Targets are still formula-derived. Calibration is not ready yet because more consistent logs or weigh-ins are needed.”

### No supported suggestion gap
“No food suggestions are available yet because no approved supported gap is available.”

Fallback copy must use the same validator rules as AI output.

## Confidence Rules
High or Moderate confidence may support concise explanatory text.

Low or Limited confidence should produce cautious explanation and limitations only.

Examples:

- High/Moderate: “Protein is below target based on logged meals.”
- Low/Limited: “Protein guidance is limited because logging appears incomplete.”

Incomplete logging must avoid hard calorie or macro certainty even when actuals are visible.

## Calibration Explanation Rules
AI may explain calibration readiness only.

It must not imply:

- targets changed
- calibrated targets are active
- calibration has been applied
- the app knows exact maintenance calories
- future target refinement is guaranteed

Allowed examples:

- “Targets are still formula-derived.”
- “Trend evidence is improving.”
- “This trend window may support future target refinement.”
- “Calibration is not ready yet because more consistent logs or weigh-ins are needed.”

## Food Suggestion Explanation Rules
AI may explain approved food suggestions only.

It may say:

- food suggestions are available
- suggestions are based on approved macro gaps
- suggestions are optional
- suggestions are limited when logging/targets are limited

It must not:

- invent foods
- invent servings
- invent macros
- create a meal plan
- make suggestions sound mandatory
- add supplement claims beyond generic canonical food entries

## Target-vs-Actual Explanation Rules
AI may explain approved target-vs-actual summaries only.

It may say:

- a macro is below, near, or above target when comparison is approved
- actuals are visible but comparisons are limited
- incomplete logging limits certainty

It must not:

- convert partial-day logs into hard conclusions
- shame the user
- imply failure
- make compensation recommendations

## Public Response Shape Recommendation
No existing response shape should change in design v1.

Future implementation should add a separate endpoint first. Do not insert AI explanations into existing Nutrition tab, DailyCoachSynthesis, or report flows until the explanation contract is accepted.

Recommended public response for future endpoint:

```json
{
  "success": true,
  "user_id": 1,
  "explanation_date": "YYYY-MM-DD",
  "approved_explanation": {
    "summary": "...",
    "nutrition_context": "...",
    "food_suggestion_context": "...",
    "trend_context": "...",
    "calibration_context": "...",
    "limitations": [],
    "confidence": "Moderate",
    "reason_codes": [],
    "source": "deterministic_fallback"
  }
}
```

Debug response may include runtime metadata, but only behind a debug endpoint.

## Recommended Implementation Sequence
1. AI Nutrition Explanation Design v1
2. Nutrition Explanation Models v1
3. Nutrition Explanation Validator v1
4. Deterministic Nutrition Explanation Fallback v1
5. Nutrition Explanation Debug API v1
6. Optional CrewAI/Ollama Provider v1
7. Nutrition Explanation QA v1
8. Streamlit preview only after validation acceptance
9. DailyCoachSynthesis/report integration only after separate Architecture approval

## Test Expectations for Future Implementation
Future implementation should test:

- approved context is accepted
- missing/limited context produces fallback or limitation text
- AI candidate with invented target is rejected
- AI candidate with invented serving is rejected
- AI candidate with unapproved food is rejected
- AI candidate saying calibration has been applied is rejected
- AI candidate saying targets changed is rejected
- AI candidate with exact maintenance calorie claim is rejected
- deterministic fallback is used when AI fails
- provider metadata is debug-only
- no raw logs/source payloads appear in public response
- DailyCoachSynthesis remains stable if not integrated
- full pytest passes

## Non-goals
- no implementation yet
- no Streamlit changes
- no target mutation
- no applying calibrated targets
- no meal planning
- no barcode scanning
- no external food import
- no report changes
- no workout changes
- no RAG implementation yet
- no required CrewAI/Ollama runtime path yet

## Architecture Recommendation
Accept a separate, validation-gated AI nutrition explanation layer only after deterministic nutrition facts, suggestions, trends, and calibration context are already approved.

The first implementation should be preview/debug only, with deterministic fallback and strict validator enforcement before any normal UI exposure.
