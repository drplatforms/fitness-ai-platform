# Nutrition Provider Implementation Design Review v1

Status: Implemented / docs-only design review complete

Branch: `feature/training-evidence-claim-service`

Review date: 2026-06-18

Related accepted milestone: `Nutrition Provider Contract Scaffolding v1`

## Readiness status

`READY_FOR_PROVIDER_IMPLEMENTATION_V1`

This means the codebase is ready for a future, explicitly approved provider implementation milestone that wires an opt-in Nutrition provider through the accepted parser, validator, safe metadata, and deterministic fallback contract.

This does **not** mean Nutrition is provider-integrated in the full report yet.

This does **not** mean Nutrition should be promoted to Level 4 or Level 5 yet.

This does **not** approve qwen3 nutrition/product voice.

## Executive summary

Nutrition now has enough backend-owned evidence, approved claims, parser scaffolding, validator scaffolding, fallback scaffolding, and negative tests to design a future provider execution path.

The recommended implementation path is to mirror the Training provider architecture at the boundary level, while keeping Nutrition-specific context, parsing, validation, and metadata separate.

The future Nutrition provider should be implemented as an opt-in service with deterministic fallback. It should not be wired into full-report composition as provider-integrated until runtime QA proves that parser/validator/fallback behavior works safely under real provider output.

## Files inspected

- `models/nutrition_report_section_models.py`
- `services/nutrition_report_section_service.py`
- `models/nutrition_provider_contract_models.py`
- `services/nutrition_provider_candidate_parser.py`
- `services/nutrition_provider_validation_service.py`
- `tests/test_nutrition_report_section_boundary.py`
- `tests/test_nutrition_provider_contract_parser.py`
- `tests/test_nutrition_provider_contract_validation.py`
- `tests/test_nutrition_provider_contract_fallback.py`
- `models/training_report_section_models.py`
- `services/training_report_section_provider_service.py`
- `services/training_report_section_direct_ollama_provider.py`
- `services/full_report_section_registry_service.py`
- `docs/project_memory/designs/nutrition_provider_contract_design_v1.md`
- `docs/project_memory/milestones/nutrition_provider_contract_scaffolding_v1.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/ai_boundaries.md`
- `docs/project_memory/backend_truth_contract.md`

## Current accepted state

### Training

- Level 5.
- Only provider-integrated full-report section.
- `direct_ollama/qwen2.5:3b` opt-in path exists.
- Async/background full-report path only.
- Deterministic fallback remains mandatory.

### Nutrition Target Display

- Level 2.
- Backend-approved display contract.
- Distinct from Nutrition Report Section.
- Not a provider voice section.

### Nutrition Report Section

- Level 3.
- Backend-owned evidence/claims/fallback boundary exists.
- Provider contract design accepted.
- Provider parser/validator/fallback scaffolding accepted.
- Not provider-integrated.
- Does not call `direct_ollama`.

## Design answers

### 1. Where should the Nutrition provider execution module live?

Future provider execution should live in a Nutrition-owned service module, not inside the existing generic nutrition report section service.

Recommended future file:

- `services/nutrition_report_section_direct_ollama_provider.py`

Rationale:

- Training already isolates direct-Ollama provider behavior in `services/training_report_section_direct_ollama_provider.py`.
- Nutrition should follow the same separation pattern so provider execution, prompt construction, timeout handling, raw output handling, parser invocation, validator invocation, and fallback conversion remain outside deterministic section rendering.
- This also makes it easier to prove no provider execution occurs in deterministic/default paths.

### 2. Should it mirror the Training provider module pattern or remain separate?

It should mirror the Training provider pattern structurally, but remain Nutrition-specific in implementation.

Mirror:

- provider module separation
- configured provider service boundary
- deterministic default
- opt-in provider enum
- direct-Ollama timeout
- fake generator injection for tests
- provider result object
- strict fallback on parse/validation/provider failure
- no live Ollama in pytest

Remain separate:

- nutrition-safe context shape
- candidate schema
- nutrition parser
- nutrition validator
- approved nutrition claims
- canonical food validation
- serving-size validation
- nutrition metadata allowlist
- nutrition-specific forbidden language

Do not reuse Training validators for Nutrition. Training and Nutrition have different claim spaces and failure modes.

### 3. What exact config variables are needed?

Recommended future env vars:

```text
AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED=false
NUTRITION_REPORT_SECTION_PROVIDER=deterministic
NUTRITION_REPORT_SECTION_MODEL=ollama/qwen2.5:3b
NUTRITION_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=300
```

Optional later if needed:

```text
NUTRITION_REPORT_SECTION_PROVIDER_MAX_RETRIES=0
```

Do not add retries in the first implementation unless Architecture explicitly approves them. Retries complicate latency and failure interpretation.

### 4. What should the default config be?

Defaults must be deterministic and non-provider:

```text
AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED=false
NUTRITION_REPORT_SECTION_PROVIDER=deterministic
NUTRITION_REPORT_SECTION_MODEL=ollama/qwen2.5:3b
NUTRITION_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=300
```

`AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED` should be the full-report safety gate equivalent to the Training full-report provider gate.

Even if `NUTRITION_REPORT_SECTION_PROVIDER=direct_ollama` is set globally, Nutrition should not attempt provider execution in full-report generation unless the full-report Nutrition provider gate is explicitly enabled.

### 5. What model should be used for initial opt-in testing?

Initial opt-in testing should use:

```text
ollama/qwen2.5:3b
```

Rationale:

- It is the practical supported model already used for Training provider boundary work.
- It is small enough for current local/runtime constraints.
- It is suitable for strict-contract testing where the success criterion is adherence to backend-approved context and schema, not final premium product voice.

`qwen3` should remain experimental and out of scope until qwen2.5 strict-contract behavior is stable.

### 6. What service function should be the public boundary?

Recommended future public service boundary:

```python
build_configured_nutrition_report_section_with_metadata(
    *,
    evidence_context: NutritionReportEvidenceContext,
    direct_ollama_generate: DirectOllamaGenerateCallable | None = None,
) -> ApprovedNutritionReportSectionResult
```

If an `ApprovedNutritionReportSectionResult` model does not exist yet, the implementation milestone should add one with:

- approved section
- source
- safe metadata

The service should also expose a public section-only convenience wrapper if needed:

```python
build_configured_nutrition_report_section(
    *,
    evidence_context: NutritionReportEvidenceContext,
) -> ApprovedNutritionReportSection
```

The metadata-returning function should be the integration boundary for future full-report composition.

### 7. What metadata should be returned internally?

Internal runtime metadata may include:

- `nutrition_provider_contract_version`
- `nutrition_provider_context_schema_version`
- `provider_enabled`
- `configured_provider`
- `selected_provider`
- `configured_model`
- `selected_model`
- `provider_attempted`
- `provider_latency_ms`
- `parse_status`
- `candidate_valid`
- `validation_status`
- `validation_errors_count`
- `fallback_used`
- `fallback_reason`
- `fallback_source`
- `nutrition_section_source`
- `confidence_ceiling`
- `approved_claim_types`
- `approved_food_suggestion_count`

Internal-only debug data may exist transiently in local provider result objects, but must not be public or persisted.

### 8. What metadata is safe to persist?

Safe persisted metadata should be allowlisted and summarized only:

- `nutrition_provider_contract_version`
- `nutrition_provider_context_schema_version`
- `nutrition_provider_execution_enabled`
- `provider_attempted`
- `selected_provider`
- `selected_model`
- `parse_status`
- `candidate_valid`
- `validation_status`
- `validation_errors_count`
- `fallback_used`
- `fallback_reason`
- `fallback_source`
- `confidence_ceiling`
- `approved_claim_types`
- `approved_food_suggestion_count`
- `nutrition_section_source`
- `provider_latency_ms`

The existing scaffolding already defines a safe metadata allowlist. Future implementation should preserve exact-key filtering and avoid adding raw/debug fields.

### 9. What metadata must never be public/persisted?

Never public or persisted:

- raw provider output
- raw prompt
- prompt template
- schema text sent to model
- rejected candidate text
- raw validation error list
- traceback
- exception text
- provider payload
- model-facing context
- parser internals
- debug objects
- raw food log payloads beyond approved summaries
- raw canonical food catalog dumps
- raw provider HTTP response
- raw provider request body

Persist counts and statuses, not raw details.

### 10. How should parser failure behave?

Parser failure should:

1. Mark `parse_status` with an allowlisted status.
2. Mark `candidate_valid=False`.
3. Skip validator approval.
4. Build deterministic Nutrition Report Section fallback.
5. Return fallback result with `fallback_used=True`.
6. Set `fallback_reason=nutrition_provider_parse_failed`.
7. Store only safe metadata.
8. Never expose raw provider output or parse error details publicly.

The existing `build_parse_failure_fallback_result(...)` scaffolding matches this direction.

### 11. How should validation failure behave?

Validation failure should:

1. Keep parsed candidate internal only.
2. Reject candidate.
3. Build deterministic Nutrition Report Section fallback.
4. Set `fallback_used=True`.
5. Set `fallback_reason=nutrition_provider_validation_failed`.
6. Store `validation_errors_count`, not raw validation errors, in public/persisted metadata.
7. Never render rejected candidate content.

The provider implementation must treat validation failure as normal safe fallback, not as an exception path.

### 12. How should provider timeout behave?

Provider timeout should:

1. Stop waiting after configured timeout.
2. Mark `provider_attempted=True`.
3. Mark `fallback_used=True`.
4. Set `fallback_reason=nutrition_provider_timeout`.
5. Return deterministic Nutrition Report Section fallback.
6. Store safe metadata only.
7. Not surface exception text or timeout stack traces publicly.

A future implementation should add an explicit timeout fallback reason constant.

### 13. How should missing nutrition evidence behave?

Missing nutrition evidence should not call the provider.

If target/actual/logging evidence is missing or insufficient:

- build deterministic Nutrition Report Section fallback
- use `confidence_ceiling=Limited`
- set `provider_attempted=False`
- set `fallback_reason=nutrition_provider_evidence_insufficient`
- preserve public-safe limitations language

Provider execution should require a provider-safe context with enough approved evidence to constrain outputs.

### 14. How should unavailable food suggestions behave?

Unavailable food suggestions should not block provider execution if other approved nutrition evidence is sufficient.

However, the provider must be unable to invent foods.

Rules:

- If no approved food suggestions exist, candidate text must not name a food as a suggestion.
- Practical food focus should use generic safe fallback language such as “No approved food suggestion is available yet.”
- Validator should reject food names, canonical food IDs, or serving sizes not present in `approved_food_suggestions`.

### 15. How should unsupported numeric claims be rejected?

Validator should reject numeric claims when:

- the number is not present in approved actuals, comparisons, targets, or approved food suggestions
- the nutrient comparison is unavailable
- the candidate states a specific deficit/surplus magnitude not approved by evidence
- the candidate unlocks hidden calorie/protein targets
- the candidate changes target ranges
- the candidate uses unsupported severity language such as “severe deficit”

The existing scaffolding already checks numeric values against approved safe context. Future implementation should extend tests as provider outputs reveal new numeric failure modes.

### 16. How should fallback preserve deterministic Nutrition Report Section content?

Fallback should call the existing deterministic Nutrition Report Section builder:

```python
build_deterministic_nutrition_report_section(evidence_context)
```

Fallback should return:

- approved deterministic section
- fallback source
- fallback reason
- safe metadata

Fallback must not render rejected provider text.

### 17. How should tests prove no live Ollama dependency in pytest?

Future tests should inject a fake generator callable into the provider service.

Test rules:

- Do not call `requests.post` or real Ollama in pytest.
- Provider implementation tests should use fake generator outputs.
- Add a test that monkeypatches the real provider HTTP call to raise if invoked unexpectedly.
- Add deterministic/default tests proving provider is not attempted unless the gate is enabled.
- Add opt-in tests with fake provider output proving parser/validator/fallback behavior.

### 18. What runtime QA matrix is required before acceptance?

Before Nutrition provider promotion or full-report integration, runtime QA should cover:

#### Deterministic/default smoke

- Provider env vars unset/default.
- Nutrition provider not attempted.
- Deterministic Nutrition Report Section fallback remains safe.
- Full report behavior unchanged.

#### Opt-in provider smoke with qwen2.5:3b

- User 102, report date `2026-06-14`.
- Provider gate enabled.
- Provider attempted.
- qwen2.5 selected.
- Approved candidate or deterministic fallback.
- No raw/debug leakage.
- Safe metadata present.

#### Negative provider-output simulations

Can be pytest-only with fake provider output first:

- malformed JSON
- wrapper object
- missing keys
- extra keys
- placeholder content
- unsupported calorie claim
- unsupported protein claim
- invented food suggestion
- unsupported serving size
- medical/supplement language
- guaranteed outcome language
- shame/compliance language
- confidence above ceiling

#### Runtime expansion before Level 5

If opt-in smoke passes, run users 101-105 on seeded runtime date before any Level 5 promotion.

### 19. When should `nutrition_report_section` move from Level 3 to Level 4 or Level 5?

Current status:

- Level 3: backend-owned evidence/claims/fallback plus contract scaffolding.

Move to Level 4 only when:

- provider implementation exists behind explicit opt-in config
- provider calls are isolated from deterministic path
- parser/validator/fallback tests pass
- no live Ollama in pytest
- fake-provider tests prove approval and rejection paths
- Nutrition still does not affect full-report provider-integrated metadata by default

Move to Level 5 only when:

- opt-in async full-report integration exists
- runtime QA passes
- safe persisted metadata is proven
- raw/debug leakage checks pass
- deterministic fallback preserves report safety
- Nutrition provider section survives/report-composes safely
- Architecture explicitly approves provider-integrated status

### 20. What must remain explicitly out of scope?

Out of scope for the next implementation milestone unless Architecture changes scope:

- qwen3 nutrition voice
- qwen3 promotion
- Nutrition Level 5 promotion
- direct full-report provider integration by default
- Streamlit controls
- persistence schema changes
- nutrition target formula changes
- new food catalog entries
- serving-size expansion
- meal planning
- supplements
- medical/deficiency claims
- RAG
- embeddings
- agent orchestration
- Training provider behavior changes

## Proposed future provider execution flow

```text
NutritionReportEvidenceContext
→ build_nutrition_provider_safe_context(...)
→ provider-safe prompt/context
→ direct_ollama candidate JSON
→ parse_candidate_nutrition_report_section(...)
→ validate_candidate_nutrition_report_section(...)
→ approved CandidateNutritionReportSection converted to ApprovedNutritionReportSection
→ safe metadata
→ deterministic fallback on any failure
```

All public output must come from either:

1. approved provider candidate after parser + validator success, or
2. deterministic Nutrition Report Section fallback.

## Proposed future module boundaries

Recommended implementation milestone files:

- `services/nutrition_report_section_direct_ollama_provider.py`
- `services/nutrition_report_section_provider_service.py`
- `tests/test_nutrition_report_section_direct_ollama_provider.py`
- `tests/test_nutrition_report_section_provider_service.py`

Possible model addition:

- `ApprovedNutritionReportSectionResult` in `models/nutrition_report_section_models.py` or `models/nutrition_provider_contract_models.py`

Recommendation: keep provider result/runtime metadata model near provider contract models if it is provider-specific. Keep public approved section models in nutrition report section models.

## Proposed future fallback reasons

Add constants in implementation milestone:

- `nutrition_provider_disabled`
- `nutrition_provider_parse_failed`
- `nutrition_provider_validation_failed`
- `nutrition_provider_timeout`
- `nutrition_provider_exception`
- `nutrition_provider_evidence_insufficient`
- `invalid_nutrition_provider`

## Proposed future tests

### Provider service tests

- deterministic default does not call provider
- invalid provider falls back deterministically
- direct_ollama opt-in calls fake generator
- provider parse failure falls back
- provider validation failure falls back
- provider timeout falls back
- provider exception falls back
- missing evidence does not attempt provider
- safe metadata excludes raw/debug keys

### Direct provider tests

- builds provider-safe context only
- accepts strict valid JSON candidate
- rejects wrapper object output
- rejects raw markdown or non-JSON output
- passes timeout to generator
- does not require live Ollama

### Integration-safety tests

- Training remains only provider-integrated section
- Nutrition remains not Level 5 until explicit approval
- no `direct_ollama` Nutrition call when env vars unset
- no qwen3 config promoted

## Recommended next milestone

`Nutrition Provider Implementation v1`

Alternative safer name:

`Nutrition Provider Opt-In Implementation v1`

Recommended status after this review:

`READY_FOR_PROVIDER_IMPLEMENTATION_V1`

Scope should still be narrow:

- implement provider execution behind explicit opt-in config
- use qwen2.5:3b as initial model
- fake generator tests only in pytest
- no qwen3
- no provider promotion to Level 5
- no broad full-report integration unless explicitly approved
- deterministic fallback mandatory

## Final position

Nutrition Provider Contract Scaffolding v1 is strong enough to proceed to a future opt-in provider implementation milestone.

The next milestone should implement provider execution behind config gates, with fake-generator tests and no live Ollama dependency in pytest.

Nutrition should remain non-provider-integrated until implementation tests and runtime QA prove the provider path is safe.
