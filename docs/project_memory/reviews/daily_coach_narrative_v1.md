# Daily Coach Narrative v1 Planning Review

Status: PLANNED / PENDING ARCHITECTURE ACCEPTANCE

Planning status: `DAILY_COACH_NARRATIVE_V1_PLANNED_PENDING_ARCHITECTURE_ACCEPTANCE`

## Decision requested

Daily Coach Narrative v1 Planning is ready for Architecture review.

This is a docs-only planning milestone. It defines the future safe Daily Coach Narrative path and does not implement runtime generation, UI integration, report integration, provider changes, or model promotion.

## Scope reviewed

Files added:

- `docs/project_memory/milestones/daily_coach_narrative_v1.md`
- `docs/project_memory/reviews/daily_coach_narrative_v1.md`
- `docs/project_memory/architecture/daily_coach_narrative_context_v1.md`

Files updated:

- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`

No runtime code is changed.

## Planning questions answered

### 1. What is the Daily Coach Narrative allowed to say?

It may explain the backend-selected Daily Next Action, reflect approved recovery/nutrition/workout/data-quality state, acknowledge limited data, use compact coach language, and point back to the approved workflow target.

### 2. What is it forbidden to say?

It may not choose or change the action, invent facts, create food or exercise suggestions, invent targets, make unsupported fatigue/recovery/progression/consistency claims, provide meal plans, provide medical claims, or override backend confidence.

### 3. What backend-approved context does it receive?

A proposed `DailyCoachNarrativeContext` containing compact approved fields: user/date, next action, backend reason, workflow target, severity/priority, approved focus, approved facts, approved limitations, optional nutrition/recovery/workout summaries, forbidden claims, and confidence language.

### 4. What output schema does it use?

The proposed output contract reuses the tightened coach voice JSON object:

```json
{
  "coach_note": "string",
  "key_takeaway": "string",
  "recommended_focus": "string",
  "confidence_language": "string",
  "used_approved_facts": ["string"],
  "avoided_claims": ["string"]
}
```

### 5. What validators are required?

Strict JSON parsing, required-only keys, exact `recommended_focus` matching, exact approved fact matching, compact length checks, forbidden claim rejection, invented number rejection, changed action/workflow rejection, and no unsupported food/exercise/meal/medical/recovery/progression/consistency claims.

### 6. What deterministic fallback renders when narrative fails?

The existing deterministic Daily Next Action wording renders. Rejected model output and raw validation errors stay hidden from normal UI.

### 7. Which models are eligible for later runtime testing?

Eligible future candidates:

- `qwen3:8b` as primary practical candidate
- `qwen2.5:3b` as small compliant baseline
- `qwen3:32b` as offline quality reference

Not recommended for v1 runtime:

- `qwen3:14b`
- `qwen3:30b-a3b`

No model is production-approved.

### 8. Where would it eventually appear in the UI?

Inside the Daily Next Action Panel, under the deterministic title/reason. The deterministic action remains visible even if narrative fails.

### 9. What must remain deterministic?

Action selection, workflow target, approved focus, targets, actuals, recovery status, workout readiness, confidence ceilings, approved facts, forbidden claims, provider approval, and fallback rendering remain deterministic/backend-owned.

### 10. What is the first implementation slice after planning?

`Daily Coach Narrative Context Builder v1`: build the backend-approved context packet from existing Daily Next Action state without calling a model.

## Boundary review

Preserved boundaries:

- no model promotion
- qwen3 remains not approved
- no Today integration
- no Streamlit integration
- no report integration
- no production provider path change
- no direct_ollama default change
- no validator loosening
- no deterministic fallback change
- no provider gate change
- no catalog, workout generation, nutrition formula, Training Level 5, or Nutrition Level 5 behavior changes

## Recommended Architecture decision

Accept Daily Coach Narrative v1 Planning as:

`DAILY_COACH_NARRATIVE_V1_PLANNED_PENDING_CONTEXT_BUILDER`

Recommended next milestone:

`Daily Coach Narrative Context Builder v1`

Implementation should remain model-free and should only build the approved context packet for later offline QA.
