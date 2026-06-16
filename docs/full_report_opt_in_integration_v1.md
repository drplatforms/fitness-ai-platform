# Full Report Opt-In Integration v1

## Status

IMPLEMENTED / SOURCE TESTED / READY FOR LOCAL VALIDATION

Branch: `feature/training-evidence-claim-service`

## Summary

The validated Training Report Section provider is now integrated into full AI Health Report rendering behind an explicit full-report opt-in gate.

This milestone does not promote `direct_ollama` to default behavior. It does not change Streamlit normal UI behavior. It does not redesign report persistence.

The full report now consumes only `ApprovedTrainingReportSection` content from the training section provider boundary. Raw provider output, model-facing quote context, parser diagnostics, and validator internals are not rendered as public report content.

## Configuration

Existing training section provider config remains unchanged:

- `TRAINING_REPORT_SECTION_PROVIDER`
- `TRAINING_REPORT_SECTION_MODEL`
- `TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS`

Full report integration adds an explicit higher-level opt-in gate:

- `AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED`

Truthy values:

- `1`
- `true`
- `yes`
- `on`
- `enabled`

Default behavior with the full-report gate unset or false:

- full report renders a deterministic training section
- direct Ollama is not attempted
- global lower-level `TRAINING_REPORT_SECTION_PROVIDER=direct_ollama` does not trigger a full-report provider call unless the full-report gate is also enabled

Opt-in behavior:

- full report attempts the configured Training Report Section provider
- provider output is used only if it becomes an approved `ApprovedTrainingReportSection`
- deterministic fallback is rendered if provider output fails parser or validator gates

## Public Report Content

The rendered full report may include approved training section fields:

- `section_summary`
- `key_observations`
- `performance_interpretation`
- `fatigue_recovery_interpretation`
- `suggested_focus`
- `limitations_context`

The rendered full report must not include:

- raw provider output
- raw output preview
- model-facing quote context
- approved quote context payload
- parser status fields
- validator internals
- candidate extra keys
- unapproved model text

## Metadata

Training section runtime metadata remains available internally through the provider boundary result.

The normal persisted report text remains public/sanitized report content only. This milestone does not persist raw provider output as user-facing content.

## Implementation Notes

Primary integration points:

- `services/coordinator_service.py`
- `services/training_report_section_provider_service.py`
- `tests/test_training_report_section_full_report_integration.py`

New public helper:

- `build_full_report_training_section_result(...)`

Rendering update:

- `render_unified_health_report(...)` accepts an optional `training_report_section_result`

Report generation update:

- `generate_health_report(...)` builds the full-report training section result and passes it to the renderer

Provider service update:

- added `build_deterministic_training_report_section_with_metadata(...)` so full report can force deterministic rendering when its higher-level opt-in gate is disabled

## Test Coverage

Added tests cover:

- full report provider gate disabled path
- no direct Ollama call when full-report gate is disabled
- opt-in approved provider path
- opt-in parser-failure fallback path
- rendered full report includes approved training section content
- rendered full report excludes raw/debug provider fields

Related provider/seed/evidence tests were run with the new tests.

## Runtime QA Plan

After local validation, commit, push, and pull to Linux runtime.

Run compact full-report opt-in runtime QA:

- provider: `direct_ollama`
- model: `qwen2.5:3b`
- users: `101, 102, 103, 104, 105`
- report date: `2026-06-14`

Expected:

- full report generation succeeds for all users
- training section renders approved direct Ollama content when provider passes
- deterministic fallback renders if provider fails
- public report contains no raw/debug provider fields
- metadata accurately reports provider/fallback behavior through the section result artifacts
- no forbidden provider-facing terms appear
- no angle-bracket artifacts appear

## Acceptance Position

This milestone should be accepted only after runtime full-report opt-in QA passes across users 101-105.
