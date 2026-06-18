# Full Report Composition Boundary v1

Status: Implemented / local regression tested / pending runtime QA

Branch: `feature/training-evidence-claim-service`

## Purpose

Full Report Composition Boundary v1 makes the full-report composition layer explicit now that training-section provider integration, async report jobs, and report persistence are accepted.

The goal is to ensure that the final public report is always composed from approved or deterministic section content, never from raw coordinator/provider output.

## Core rule

```text
approved/deterministic section content
→ safe full-report composition
→ safe public report text
→ safe allowlisted metadata
→ persisted health_report history
```

The report must never become:

```text
raw coordinator output
→ public report history
```

## Section ownership

Current full-report ownership is:

| Report area | Owner | Notes |
|---|---|---|
| Profile Context | deterministic backend renderer | Derived from `UserHealthState` and `CoachingDecision`. |
| Grounded Recommendation | approved backend recommendation contract | Uses `ApprovedActionPlan` and backend-owned target display flags. |
| Nutrition Target Display | deterministic backend renderer | Uses `NutritionTargets` display contract. |
| Training Report Section | deterministic or approved provider-backed section | Full report consumes only `ApprovedTrainingReportSection`. |
| Biggest Issue / Likely Cause / Priority Action / Recommendation | CrewAI structured coordinator if valid, otherwise deterministic fallback | Coordinator output must parse and pass validation before use. |
| Persistence metadata | allowlisted backend metadata | Raw provider/coordinator/debug payloads are excluded. |

## Coordinator boundary

The old CrewAI full-report coordinator may still be attempted, but it does not own public truth.

Valid coordinator output must be structured into these fields:

- `overall_score`
- `biggest_issue`
- `likely_cause`
- `priority_action`
- `recommendation`

If the coordinator output is missing fields, invalid, or fails language validation, the report composer falls back to deterministic `UnifiedHealthReport` content.

## Provider-backed training section survival

If the training section provider produces an approved section and the full-report coordinator later fails, the approved training section is retained in the deterministic fallback full report.

The accepted fallback behavior is:

```text
direct_ollama approved training section
+ CrewAI coordinator failure
→ deterministic full-report shell
→ approved training section retained
→ safe metadata persisted
```

## Composition metadata

Safe report metadata may include summary-level composition fields:

- `full_report_composer_source`
- `coordinator_attempted`
- `coordinator_fallback_used`
- `coordinator_fallback_reason`

Current composer source values:

- `crewai_coordinator_structured`
- `deterministic_fallback_after_invalid_coordinator_output`
- `deterministic_fallback_after_crewai_error`

Current coordinator fallback reasons:

- `invalid_coordinator_output`
- `crewai_coordinator_error`

These are safe summary labels. They must not include raw exception text.

## Persisted content boundary

Do not persist as public report text or public history metadata:

- raw provider output
- raw CrewAI output
- raw CrewAI exception text
- prompt text
- schema text
- model-facing quote context
- approved quote context
- raw validation error lists
- parser internals
- validator internals
- rejected candidate text
- debug artifacts

## Tests

Focused tests:

```bash
pytest tests/test_full_report_composition_boundary.py -q
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
  tests/test_report_persistence_boundary.py \
  tests/test_full_report_composition_boundary.py -q
```

Local sandbox validation:

```text
tests/test_full_report_composition_boundary.py: 3 passed
report persistence + composition focused tests: 16 passed
related focused suite: 164 passed
```

## Runtime QA still required

After commit/push and Linux pull, run deterministic/default report generation and opt-in async provider-backed report generation for users `101-105` on report date `2026-06-14`.

Expected runtime result:

- report jobs complete
- approved training section is retained
- full report persists safely
- raw provider output absent
- raw CrewAI error text absent
- safe composition metadata present
- fallback behavior clear and intentional

## Non-goals preserved

No changes in this milestone should:

- make `direct_ollama` default
- promote `qwen3`
- loosen parser behavior
- loosen validator behavior
- expose raw provider output publicly
- expose raw CrewAI errors publicly
- persist raw provider output publicly
- persist raw CrewAI errors publicly
- redesign Streamlit UI
- add provider controls to normal UI
- change foods
- change exercises
- change workout generation
- add meal planning
- broadly rewrite report generation
