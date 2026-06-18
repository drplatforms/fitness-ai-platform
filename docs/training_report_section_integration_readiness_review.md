# Training Report Section Integration Readiness Review v1

## Status

Architecture review milestone for the Direct Ollama training report section path after Bounded Coaching Claims v1.1.

Decision: **conditionally ready for conservative integration planning, not automatic full-report wiring in this milestone.**

## Reviewed baseline

Current accepted baseline:

- `Direct Ollama Training Report Section Provider v1`
- `Bounded Coaching Claims v1`
- `Bounded Coaching Claims v1.1`
- `Training Evidence Claim Service v1`
- `Training Evidence Claim Runtime QA v1`

Runtime QA showed:

- `qwen2.5:3b` can produce approved, bounded, usable training-section copy.
- `qwen2.5:3b` preserved exact required anchors after TrainingEvidenceClaim extraction in the known-good seeded scenario.
- `qwen3:8b` remains experimental/product-voice probe only.
- The validator correctly rejects provider output when it turns single-session evidence into broader effort, consistency, recovery, or trend claims.
- Deterministic fallback remains mandatory.

## Current implementation shape

The provider service already exists behind configuration:

```text
TRAINING_REPORT_SECTION_PROVIDER=deterministic|direct_ollama
TRAINING_REPORT_SECTION_MODEL=ollama/qwen2.5:3b
TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=60
```

The current service boundary is:

```text
backend-approved training context
→ configured provider selection
→ deterministic or direct_ollama candidate
→ strict parser/validator
→ ApprovedTrainingReportSection
→ TrainingReportSectionRuntimeMetadata
```

The accepted evidence-layer boundary is:

```text
approved workout/training facts
→ TrainingEvidenceContext
→ ApprovedTrainingClaim[]
→ model-facing quote context
→ strict section validator
```

The current full report path does **not** consume `ApprovedTrainingReportSection` yet. Full reports currently include:

```text
Profile Context
→ Grounded Recommendation
→ Nutrition Target Display
→ UnifiedHealthReport sections 1-4
```

## Readiness verdict

The training report section is **ready for a narrow integration design**.

It is **not** ready to become default live report behavior without a separate implementation milestone and QA pass.

Approved readiness position:

- Deterministic must remain default.
- `direct_ollama` must remain opt-in.
- `qwen2.5:3b` is the only supported Direct Ollama model for this section.
- `qwen3:8b` remains experimental/product-voice probe only.
- Raw model output must not be public.
- Raw model output must not be persisted.
- Sanitized runtime metadata may be exposed only in developer/debug surfaces.
- Failed or rejected candidates must fall back deterministically.

## Integration recommendation

Recommended next implementation milestone:

```text
Expanded Training Evidence Runtime QA Matrix v1
```

After that passes, route:

```text
Training Report Section Full Report Integration Design v1
```

This should be a design-first milestone unless Architecture explicitly approves implementation.

If Architecture approves implementation after design, the first integration should be conservative:

```text
render_unified_health_report(...)
→ Profile Context
→ Grounded Recommendation
→ Nutrition Target Display
→ Training Review section from ApprovedTrainingReportSection
→ UnifiedHealthReport sections 1-4
```

The training section should appear as a distinct **Training Review** block, not be blended into the existing `UnifiedHealthReport` fields. This keeps the approved section contract isolated and makes fallback/debug behavior easier to inspect.

## Proposed public rendering shape

Public report rendering may include:

```text
**Training Review**

Summary: <approved_section.section_summary>

Key observations:
- <approved key observation>
- <approved key observation>

Performance interpretation: <approved bounded interpretation>

Fatigue/recovery context: <approved bounded context>

Suggested focus: <approved suggested focus>

Limitations: <approved limitations context>

Confidence: <approved confidence>
```

This section should render only `ApprovedTrainingReportSection` fields.

It should not render:

- raw model output
- prompt payloads
- model-facing quote context
- validation errors
- provider names in normal user mode
- runtime metadata in normal user mode

## Metadata policy

Sanitized provider metadata may be used for developer diagnostics only.

Developer/debug metadata may include:

- configured_provider
- selected_provider
- configured_model
- selected_model
- provider_attempted
- fallback_used
- fallback_reason
- candidate_valid
- validation_errors
- candidate_parse_status
- candidate_validation_status
- validation_status
- final_section_source
- elapsed_seconds
- required_anchor_count
- missing_required_anchor_count

Developer/debug metadata must not expose raw output by default.

If raw diagnostics are needed for local QA, they should remain CLI/debug-only and never appear in normal Streamlit user-facing report output.

## Persistence policy

Do not persist raw provider output.

If report persistence later stores training-section metadata, persist only:

- approved section text that was actually rendered
- source/fallback state if needed for debugging
- sanitized provider/model metadata if explicitly approved
- timestamp/report id association

Do not persist:

- raw model output
- prompt payload
- model-facing quote context
- unapproved candidate text
- full validation internals in user-facing report records

## Service boundary status

Training Evidence Claim Service v1 has now been implemented and accepted as the backend evidence-layer baseline. Bounded claim derivation no longer lives as provider-owned logic.

The current accepted shape is:

```text
approved workout/training facts
→ TrainingEvidenceContext
→ ApprovedTrainingClaim[]
→ model-facing training context
→ section validator
```

The Direct Ollama provider consumes service-derived `ApprovedTrainingClaim[]` while exact required anchors remain the higher-priority validation contract.

Runtime QA after claim extraction validated the known-good qwen2.5:3b path for user 102 on 2026-06-06.

Recommended follow-up before full report integration:

```text
Expanded Training Evidence Runtime QA Matrix v1
```

## TrainingExecutionSummary relationship

Do not force TrainingExecutionSummary integration inside the first full-report integration milestone.

The cleaner long-term direction is:

```text
TrainingExecutionSummary
→ TrainingEvidenceContext
→ ApprovedTrainingClaim[]
→ ApprovedTrainingReportSection
```

But this should be a separate milestone because TrainingExecutionSummary is broader than the current single-section provider context.

Recommended follow-up milestone:

```text
TrainingExecutionSummary to Training Evidence Claims Design v1
```

## Supported model policy

Supported:

- `ollama/qwen2.5:3b`

Experimental:

- `ollama/qwen3:8b`

Model policy:

- Do not make qwen3 default.
- Do not loosen validation to make qwen3 pass.
- Do not treat qwen3 safe rejection as an architecture failure.
- Use qwen3 only as a product-voice probe and validator stress test.

## Integration acceptance criteria

Before implementation is accepted, tests should prove:

1. Deterministic provider remains default.
2. `direct_ollama` remains opt-in.
3. Full report rendering works when training section provider is deterministic.
4. Full report rendering works when mocked direct_ollama returns an approved section.
5. Rejected direct_ollama output falls back to deterministic section.
6. Report output includes the public Training Review section only when integration is enabled.
7. Normal report output does not expose raw provider output.
8. Normal report output does not expose runtime metadata.
9. Developer/debug mode may expose sanitized metadata only.
10. qwen2.5-style approved section renders correctly.
11. qwen3-style unsafe over-inference remains rejected.
12. Existing Grounded Recommendation and Nutrition Target Display remain unchanged.
13. Existing UnifiedHealthReport sections remain stable.
14. Existing report language validation still passes.
15. Existing report history/latest behavior remains stable.
16. Existing pytest suite passes without live Ollama/CrewAI calls.

## Non-goals

Do not:

- wire the provider into full reports in this review milestone
- make `direct_ollama` default
- make qwen3 supported/default
- loosen validation
- expose raw output in the UI
- persist raw model output
- let AI create training facts
- merge the section into existing report fields prematurely
- rewrite full report architecture
- connect to TrainingExecutionSummary in the same milestone
- add Streamlit controls unless explicitly approved
- call live Ollama in pytest

## Final architecture position

Training Evidence Claim Service v1 is accepted as the backend evidence-layer baseline.

Training Evidence Claim Runtime QA v1 is accepted as FULL PASS for the known-good qwen2.5:3b seeded scenario.

The direct-Ollama training section is ready for **expanded runtime QA matrix**, then conservative integration planning, not default production behavior.

The safest path is:

1. Keep current provider baseline.
2. Keep deterministic default and direct_ollama opt-in.
3. Run Expanded Training Evidence Runtime QA Matrix v1.
4. Design full-report integration as a distinct Training Review section.
5. Store/render only approved section fields.
6. Keep metadata debug-only and sanitized.
7. Later connect TrainingExecutionSummary to the TrainingEvidenceContext layer.

Backend owns truth.
AI explains approved truth.
Validator enforces reality.
The coach must sound right and be right.
