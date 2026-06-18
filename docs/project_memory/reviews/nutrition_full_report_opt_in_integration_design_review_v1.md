# Nutrition Full Report Opt-In Integration Design Review v1

Status: Implemented / docs-only design review complete

Branch: `feature/training-evidence-claim-service`

Review date: 2026-06-18

Related accepted milestone: `Nutrition Provider Opt-In Runtime QA v1`

## Readiness status

`READY_FOR_FULL_REPORT_OPT_IN_INTEGRATION_IMPLEMENTATION`

This means Nutrition is ready for a future implementation milestone that wires the proven section-only opt-in provider path into full-report generation behind explicit full-report gates.

This does **not** mean Nutrition is Level 5.

This does **not** mean Nutrition is already full-report provider-integrated.

This does **not** approve qwen3.

This does **not** approve broad report generation or persistence redesign.

## Executive summary

Nutrition Provider Opt-In Runtime QA proved the isolated section-only provider path can run safely with deterministic default behavior, explicit direct-Ollama opt-in behavior, strict parser/validator boundaries, safe fallback behavior, and no raw/debug/provider leakage outside explicit debug metadata.

The next safe step is a full-report integration implementation milestone, but only with an additional full-report integration gate and no automatic Level 5 promotion.

Recommended next milestone:

`Nutrition Full Report Opt-In Integration v1`

Alternative safer name:

`Nutrition Full Report Integration Implementation v1`

Expected status after that implementation milestone should be:

`READY_FOR_FULL_REPORT_RUNTIME_QA`

not Level 5.

## Files inspected

- `services/coordinator_service.py`
- `api/routes/reports.py`
- `services/report_service.py`
- `services/full_report_section_registry_service.py`
- `services/nutrition_report_section_provider_service.py`
- `services/nutrition_report_section_direct_ollama_provider.py`
- `services/nutrition_provider_candidate_parser.py`
- `services/nutrition_provider_validation_service.py`
- `services/nutrition_report_section_service.py`
- `models/nutrition_provider_contract_models.py`
- `models/nutrition_report_section_models.py`
- `tests/test_nutrition_report_section_provider_service.py`
- `tests/test_nutrition_report_section_direct_ollama_provider.py`
- `tests/test_nutrition_provider_contract_parser.py`
- `tests/test_nutrition_provider_contract_validation.py`
- `tests/test_nutrition_provider_contract_fallback.py`
- `tests/test_full_report_composition_boundary.py`
- `tests/test_report_persistence_boundary.py`
- `docs/project_memory/runtime_qa/nutrition_provider_opt_in_runtime_qa.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/section_registry_summary.md`
- `docs/project_memory/ai_boundaries.md`
- `docs/project_memory/backend_truth_contract.md`

## Current accepted state

### Training

- Level 5.
- Only full-report provider-integrated section.
- `direct_ollama/qwen2.5:3b` opt-in path.
- Async/background full-report path accepted.
- Persistence and composition boundaries accepted.

### Nutrition Target Display

- Level 2.
- Backend-approved display contract.
- Distinct from Nutrition Report Section.
- Should remain present after Nutrition Report Section integration.

### Nutrition Report Section

- Level 4.
- Backend-owned evidence/claims/fallback boundary.
- Provider contract design accepted.
- Parser/validator/fallback scaffolding accepted.
- Isolated opt-in provider implementation accepted.
- Section-only runtime QA accepted with `PASS_WITH_DEBUG_ENDPOINT_CLARIFICATION`.
- Not full-report integrated.
- Not Level 5.

### Provider-integrated full-report sections

`training` only.

## Design decision

Nutrition full-report integration should mirror the Training full-report integration pattern at the composition and metadata boundary level, while keeping Nutrition-specific provider execution, context, parsing, validation, and metadata names separate.

Do not replace the Training provider path.

Do not reuse Training metadata keys for Nutrition.

Do not allow Nutrition provider status to appear as `provider_integrated_report_sections` until Architecture explicitly accepts Level 5 promotion.

## Proposed implementation boundary

### Current provider boundary to reuse

The future full-report integration should call:

`services.nutrition_report_section_provider_service.build_configured_nutrition_report_section_with_metadata(...)`

This is the correct public internal boundary for Nutrition provider selection because it already owns:

- deterministic default behavior
- explicit provider opt-in behavior
- fake-provider test seam
- provider-safe context construction
- candidate parser call
- candidate validator call
- approved-section conversion
- deterministic fallback
- safe metadata construction

### Full-report composition boundary

The future implementation should add a Nutrition Report Section composition step in `services/coordinator_service.generate_health_report(...)`.

Recommended placement in the rendered report:

1. Overall score
2. Profile context
3. Grounded Recommendation
4. Nutrition Target Display
5. Nutrition Report Section
6. Training Report Section
7. Existing issue/cause/action/recommendation fields

Nutrition Target Display should remain distinct and should not be overwritten by the richer Nutrition Report Section.

### Async job boundary

The future implementation should update `api/routes/reports.py` only enough to expose safe Nutrition section job metadata for runtime QA, similar to how training metadata is exposed.

It should not expose raw output, prompt, schema, rejected candidate text, validation error list, or model-facing context.

### Persistence boundary

The future implementation may update `services/report_service.py` only to allowlist safe, summary-level Nutrition metadata in persisted report history.

This should be narrowly scoped and exact-key based.

No raw/debug/provider content may be persisted.

## Proposed config gates

Use a two-gate design to avoid section-only provider opt-in accidentally becoming full-report provider integration.

### Existing section provider gates

These already control isolated section provider execution:

```text
AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED=false
NUTRITION_REPORT_SECTION_PROVIDER=deterministic
NUTRITION_REPORT_SECTION_MODEL=ollama/qwen2.5:3b
NUTRITION_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=300
```

### New full-report integration gate

Recommended new gate:

```text
AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED=false
```

The full report should attempt Nutrition provider composition only when:

```text
AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED=true
AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED=true
NUTRITION_REPORT_SECTION_PROVIDER=direct_ollama
```

Default must remain deterministic with no Nutrition provider attempt.

## Proposed execution flow

```text
generate_health_report(...)
→ build NutritionReportEvidenceContext
→ render existing Nutrition Target Display
→ if full-report Nutrition integration gate disabled:
      render deterministic Nutrition Report Section or omit section per Architecture-approved implementation choice
      metadata: nutrition_full_report_integration_enabled=false
→ if full-report Nutrition integration gate enabled:
      call build_configured_nutrition_report_section_with_metadata(...)
      if approved provider section:
          render approved Nutrition Report Section
      if deterministic/fallback section:
          render deterministic fallback Nutrition Report Section
→ continue Training Report Section path unchanged
→ compose full report
→ validate public report text
→ persist report text and safe metadata
```

## Missing evidence behavior

If Nutrition evidence cannot be built or is too incomplete for provider value, the full-report integration should not fail the report.

Expected behavior:

- use deterministic Nutrition Report Section fallback
- set safe fallback reason such as `nutrition_evidence_unavailable`
- do not expose raw exception details
- do not expose model-facing context
- continue composing the full report

## Unavailable food suggestion behavior

Unavailable food suggestions should not block the full report.

Expected behavior:

- provider-safe context should communicate that no approved suggestion is available
- validator must reject invented foods or serving sizes
- deterministic fallback may say that no approved food suggestion is available
- safe metadata may include `approved_food_suggestion_count=0`

## Parser failure behavior

Parser failure should:

- fall back deterministically
- set `nutrition_parse_status=failed`
- set `nutrition_fallback_used=true`
- set `nutrition_fallback_reason=nutrition_provider_parse_failed`
- persist only `nutrition_validation_errors_count`, not raw validation errors
- never render rejected candidate text

## Validation failure behavior

Validation failure should:

- fall back deterministically
- set `nutrition_validation_status=rejected`
- set `nutrition_candidate_valid=false`
- set `nutrition_fallback_used=true`
- set `nutrition_fallback_reason=nutrition_provider_validation_failed`
- expose only count-level metadata
- never persist raw validation error content

## Timeout and exception behavior

Provider timeout or exception should:

- fall back deterministically
- set safe fallback reason
- not expose traceback
- not expose exception text
- not fail the full report job
- not discard an approved Training provider section

## Composition fallback behavior

If the old CrewAI full-report coordinator fails after Nutrition and/or Training sections were already approved, the fallback full-report composition should retain already-approved safe section content.

Accepted existing rule for Training should extend to Nutrition once full-report integration is implemented:

- approved section content survives coordinator failure
- deterministic full-report fallback composes safe text
- safe metadata records source/fallback behavior
- raw CrewAI error text remains absent from public report and persisted history

## Proposed safe metadata

Use Nutrition-prefixed keys to avoid confusing Training and Nutrition metadata.

Safe internal/job metadata may include:

- `nutrition_full_report_integration_enabled`
- `nutrition_provider_execution_enabled`
- `nutrition_provider_enabled`
- `nutrition_provider_attempted`
- `nutrition_selected_provider`
- `nutrition_selected_model`
- `nutrition_parse_status`
- `nutrition_candidate_valid`
- `nutrition_validation_status`
- `nutrition_validation_errors_count`
- `nutrition_fallback_used`
- `nutrition_fallback_reason`
- `nutrition_fallback_source`
- `nutrition_confidence_ceiling`
- `nutrition_approved_claim_types`
- `nutrition_approved_food_suggestion_count`
- `nutrition_section_source`
- `nutrition_provider_latency_ms`

Safe persisted metadata should be a subset of these fields and must remain exact-key allowlisted.

## Forbidden public/persisted content

These remain forbidden outside explicit debug endpoints:

- raw provider output
- raw output preview
- prompt
- schema
- rejected candidate text
- raw validation errors list
- traceback
- exception text
- provider payload
- model-facing context
- parser internals
- debug objects
- raw CrewAI error text

`validation_errors=[]` and `raw_output_preview_truncated=null` are acceptable only in explicit section-only debug endpoint metadata, consistent with accepted QA clarification.

## Proposed tests for implementation milestone

### Full-report integration tests

- deterministic default full report does not attempt Nutrition provider
- full-report Nutrition integration gate disabled prevents Nutrition provider attempt
- Nutrition section provider enabled but full-report integration gate disabled does not integrate Nutrition into full report
- opt-in full-report Nutrition integration uses fake generator
- valid fake Nutrition provider candidate renders approved Nutrition section
- invalid fake candidate falls back deterministically
- parser failure falls back deterministically
- validation failure falls back deterministically
- timeout falls back deterministically
- exception falls back deterministically
- missing Nutrition evidence falls back deterministically
- unavailable food suggestions do not cause provider invention

### Composition/persistence safety tests

- approved Training section survives Nutrition provider failure
- approved Nutrition section survives old CrewAI coordinator failure
- raw Nutrition provider output is absent from public report text
- rejected Nutrition candidate text is absent from public report text
- raw Nutrition provider output is absent from persisted report history
- raw validation error list is absent from persisted report history
- safe Nutrition metadata is persisted only through allowlisted keys
- no exact forbidden keys appear in persisted metadata
- Training remains the only Level 5 provider-integrated section until Architecture approval

### No-live-provider tests

- fake generator is used in pytest
- direct-Ollama transport is not called unless fake seam is explicitly bypassed
- no pytest requires local Ollama

## Proposed runtime QA matrix after future implementation

### Minimum runtime QA

1. Deterministic/default full-report smoke for user 102/date 2026-06-14.
2. Nutrition full-report integration disabled smoke with section provider enabled, proving no accidental provider attempt.
3. Opt-in Nutrition full-report integration smoke for user 102/date 2026-06-14 with qwen2.5:3b.
4. Persisted-history inspection for user 102.
5. Exact-key leakage checks.

### Required runtime output

- job_id
- job_status
- elapsed_seconds
- nutrition_full_report_integration_enabled
- nutrition_provider_execution_enabled
- nutrition_provider_enabled
- nutrition_provider_attempted
- nutrition_selected_provider
- nutrition_selected_model
- nutrition_parse_status
- nutrition_candidate_valid
- nutrition_validation_status
- nutrition_validation_errors_count
- nutrition_fallback_used
- nutrition_fallback_reason
- nutrition_section_source
- nutrition_provider_latency_ms
- training_section_source
- provider_integrated_report_sections
- nutrition_level
- persisted_row_found
- raw_debug_terms_in_report
- raw_debug_terms_in_persisted_history
- forbidden_exact_keys_in_persisted_history
- angle_brackets
- forbidden_seed_terms
- decision

### Expanded runtime QA before Level 5

Run users 101-105 only after minimum runtime QA passes and Architecture approves promotion consideration.

## Section maturity guidance

Current:

- Nutrition: Level 4
- Training: Level 5

After future full-report opt-in implementation and local tests:

- Nutrition should remain Level 4 until runtime QA passes.
- It may be described as `Level 4 with full-report opt-in integration implemented / pending runtime QA`.
- It must not be promoted to Level 5 during implementation alone.

Level 5 should require:

- async full-report integration implemented
- runtime QA passed
- persisted-history inspection passed
- raw/debug leakage checks passed
- composition fallback safety passed
- Architecture acceptance

## Explicit non-goals

Do not include in the future implementation unless separately approved:

- qwen3 testing
- qwen3 promotion
- Nutrition Level 5 promotion
- Training provider behavior changes
- persistence redesign
- report generation redesign
- Streamlit changes
- meal planning
- new foods
- serving-size expansion
- RAG
- embeddings
- agent orchestration
- validator loosening
- nutrition target formula changes

## Recommendation

Proceed to:

`Nutrition Full Report Opt-In Integration v1`

Implementation should be narrow:

- add explicit full-report integration gate
- call existing Nutrition provider service from full-report composition only when allowed
- render a distinct Nutrition Report Section
- preserve Nutrition Target Display
- add safe Nutrition metadata to job/persistence allowlists
- add fake-provider full-report integration tests
- do not promote Nutrition to Level 5
- do not run qwen3

Expected status after implementation:

`READY_FOR_FULL_REPORT_RUNTIME_QA`
