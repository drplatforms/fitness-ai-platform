# Report Persistence Boundary v1

## Status

Implemented / ready for local validation and runtime QA.

## Architecture Decision

Architecture accepted Async / Report Job Integration v1 and approved Report Persistence Boundary v1.

This milestone preserves the same trust boundary used by provider-backed full report generation:

```text
Backend owns truth.
AI explains approved truth.
Validator enforces reality.

approved facts/evidence
→ approved section output
→ public report content
```

Raw model output must not become trusted report history.

## Scope Implemented

Report persistence now has an explicit public-content and metadata boundary.

Implemented behavior:

- persisted public report text is validated before save
- raw/debug/provider terms are rejected from public report text
- report history can store safe summary metadata separately from public report text
- raw provider output is not persisted as public report content
- unsafe metadata keys are dropped before persistence
- deterministic report generation can persist safe content
- provider-approved report generation can persist approved public content and safe metadata
- provider-fallback report generation can persist deterministic fallback public content and safe fallback metadata
- report history remains queryable through existing latest/history service functions

## Files Changed

Primary implementation files:

- `database.py`
- `services/report_service.py`
- `services/coordinator_service.py`
- `api/routes/reports.py`

Tests:

- `tests/test_report_persistence_boundary.py`

Docs:

- `docs/report_persistence_boundary_v1.md`

## Persistence Schema

`health_reports` now supports:

- `report_text`
- `model_summary`
- `report_date`
- `report_metadata_json`
- `created_at`

Existing databases are migrated lazily by `services.report_service` using safe `ALTER TABLE` checks when saving or reading reports.

## Public Report Content Boundary

Public persisted report text may include:

- approved rendered full report text
- approved training report section content
- deterministic fallback content

For the Training Report Section, public content may include:

- `section_summary`
- `key_observations`
- `performance_interpretation`
- `fatigue_recovery_interpretation`
- `suggested_focus`
- `limitations_context`

Public persisted report text is rejected if it contains forbidden provider/debug terms such as:

- `raw_output`
- `raw_output_preview_truncated`
- `model_facing_quote_context`
- `approved_training_quote_context`
- `candidate_parse_status`
- `candidate_validation_status`
- `validation_errors`
- `prompt`
- `schema`

## Safe Metadata Boundary

Safe metadata is persisted separately in `report_metadata_json`.

Allowed summary fields:

- `user_id`
- `report_date`
- `report_job_id`
- `report_status`
- `generated_at`
- `completed_at`
- `provider_enabled`
- `provider_attempted`
- `selected_provider`
- `selected_model`
- `fallback_used`
- `fallback_reason`
- `training_section_source`
- `provider_latency_ms`
- `validation_status`
- `validation_errors_count`
- `report_generation_mode`
- `async_job_used`

Unsafe/debug metadata fields are dropped before persistence.

Examples of dropped fields:

- `raw_output`
- `raw_output_preview_truncated`
- `model_facing_quote_context`
- `approved_training_quote_context`
- `matched_required_fact_anchors`
- `candidate_parse_status`
- `candidate_validation_status`
- `validation_errors`

## Coordinator Integration

`generate_health_report(...)` now accepts:

```python
report_job_id: str | None = None
```

When saving a report, the coordinator persists:

- final public report text
- report date
- safe provider/fallback metadata
- async job usage metadata

The async report route passes its `job_id` into report generation so persisted metadata can identify the originating report job without exposing raw provider data.

## Fallback Persistence

If provider succeeds:

- approved/sanitized report text is persisted
- safe metadata records provider approval
- raw output is not persisted publicly

If provider fails:

- deterministic fallback report text is persisted
- safe metadata records fallback behavior
- rejected candidate text is not persisted publicly

Provider failure should not create empty or broken report history.

## Tests

Focused persistence tests:

```bash
pytest tests/test_report_persistence_boundary.py -q
```

Related focused suite:

```bash
pytest tests/test_full_report_async_provider_integration.py \
  tests/test_training_report_section_full_report_integration.py \
  tests/test_report_status.py \
  tests/test_training_report_section_provider_service.py \
  tests/test_direct_ollama_training_report_section_spike.py \
  tests/test_training_evidence_claim_service.py \
  tests/test_training_execution_summary_service.py \
  tests/test_longitudinal_qa_seed_data.py \
  tests/test_seed_training_execution_qa.py \
  tests/test_api_smoke.py \
  tests/test_report_persistence_boundary.py -q
```

Sandbox validation:

```text
tests/test_report_persistence_boundary.py: 12 passed
related focused suite: 160 passed
py_compile touched/related files: passed
```

`ruff` and `black` were not available in the sandbox environment. Run them locally before commit.

## Runtime QA Required After Commit/Pull

After local tests pass and the branch is pushed/pulled to Linux runtime:

1. Run deterministic/default report generation.

Expected:

- report job completes
- provider not attempted
- persisted report content is deterministic and safe
- no raw/debug provider fields in persisted report history

2. Run opt-in async provider-backed report generation.

Environment:

```bash
AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED=true
TRAINING_REPORT_SECTION_PROVIDER=direct_ollama
TRAINING_REPORT_SECTION_MODEL=ollama/qwen2.5:3b
TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=300
OLLAMA_BASE_URL=http://192.168.1.104:11434
```

Users:

```text
101, 102, 103, 104, 105
```

Report date:

```text
2026-06-14
```

Expected:

- report jobs complete
- persisted public report contains only approved/safe content
- raw/debug fields are absent from persisted public report text
- persisted safe metadata accurately records provider/fallback behavior
- job status metadata remains safe

Do not run qwen3 unless Architecture asks.

## Non-Goals Preserved

No changes were made to:

- direct_ollama default behavior
- qwen3 promotion
- qwen3 prompt tuning
- parser looseness
- validator looseness
- approved training evidence rules
- Streamlit UI
- provider controls in normal UI
- food catalog
- exercise catalog
- meal planning
- workout generation
- CrewAI behavior
- latency optimization

## Final Position

Report Persistence Boundary v1 is accepted after local validation and runtime persistence QA.

The system now separates:

```text
public persisted report content
safe persisted metadata
forbidden raw/debug provider content
```

Raw provider output is not persisted as user-facing report content.


## Final Runtime Acceptance Addendum

Runtime QA accepted Report Persistence Boundary v1 after the follow-up fallback persistence wiring fix.

Final accepted result:

- async provider-backed full report jobs passed for users `101-105`
- persisted `health_reports` rows exist for users `101-105`
- `report_date` persisted as `2026-06-14`
- safe provider metadata persisted correctly
- public report text contained no raw/debug/provider payload fields
- persisted metadata contained only allowlisted safe fields
- `raw_output` was absent
- `raw_output_preview_truncated` was absent
- `model_facing_quote_context` was absent
- `approved_training_quote_context` was absent
- `candidate_parse_status` was absent
- raw `validation_errors` lists were absent
- `validation_errors_count` appeared only as safe summary metadata
- no angle-bracket artifacts were detected
- no forbidden QA/Seeded/Test/Placeholder/Dummy/Synthetic terms were detected
- persisted-history inspection returned `OVERALL: PASS`

Accepted runtime observation:

```text
model_summary=deterministic_fallback_after_crewai_error
```

This is correct safety behavior for v1. It means the direct-Ollama training section provider succeeded, the approved provider-backed training section was retained, the older CrewAI full-report coordinator failed, and the system persisted a safe deterministic fallback full report without exposing raw CrewAI error text.

Next accepted milestone: Full Report Composition Boundary v1.
