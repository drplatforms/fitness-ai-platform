# Full Report Section Registry v1

Status: Implemented / local regression tested / pending Architecture review

Branch: `feature/training-evidence-claim-service`

## Purpose

Full Report Section Registry v1 defines the generated AI Health Report as a set of explicit section-owned components instead of one monolithic coordinator-owned report.

The goal is to make the current report ownership visible before expanding provider-backed product voice beyond the Training Report Section.

## Core principle

```text
source data
→ derived evidence
→ approved claims
→ optional provider explanation
→ validator
→ deterministic fallback
→ full report composition
→ safe persistence
```

The report should not become:

```text
entire messy report context
→ one model writes everything
→ hope it is right
```

## Registry implementation

Added:

- `models/full_report_section_registry_models.py`
- `services/full_report_section_registry_service.py`
- `tests/test_full_report_section_registry.py`

The v1 registry is static and intentionally conservative. It maps the current public sections rendered by `services.coordinator_service.render_unified_health_report(...)`.

Registry version:

```text
full_report_section_registry_v1
```

Safe persisted metadata now includes:

- `full_report_section_registry_version`
- `full_report_section_ids`
- `provider_integrated_report_sections`

These fields are summary-level metadata only. They do not include raw model output, prompt text, schema text, provider payloads, parser internals, validator internals, or raw errors.

## Current section ownership map

| Section id | Public display name | Current source | Fallback owner | Provider status | Maturity |
|---|---|---|---|---|---:|
| `overall_score` | Overall Score | `UnifiedHealthReport.overall_score` | `_build_fallback_unified_report` | none | 1 |
| `profile_context` | Profile Context | `UserHealthState` profile fields | `_format_profile_context` | none | 1 |
| `grounded_recommendation` | Grounded Recommendation | `ApprovedActionPlan` | `build_approved_action_plan` | not full-report integrated | 3 |
| `nutrition_target_display` | Nutrition Target Display | `NutritionTargets` display contract | `_render_nutrition_target_display` | none | 2 |
| `nutrition_report_section` | Nutrition Report Section | `ApprovedNutritionReportSection` boundary | `build_deterministic_nutrition_report_section` | none | 3 |
| `training` | Training Report Section | `ApprovedTrainingReportSection` | deterministic training section provider fallback | opt-in full-report integrated | 5 |
| `biggest_issue` | Biggest Issue | valid structured coordinator output or deterministic fallback | `_build_fallback_unified_report` | none | 1 |
| `likely_cause` | Likely Cause | valid structured coordinator output or deterministic fallback | `_build_fallback_unified_report` | none | 1 |
| `priority_action` | Highest Priority Action | valid structured coordinator output or deterministic fallback | `_build_fallback_unified_report` | none | 1 |
| `best_recommendation` | Best Recommendation | valid structured coordinator output or deterministic fallback | `_build_fallback_unified_report` | none | 1 |

## Section maturity model

| Level | Meaning |
|---:|---|
| 0 | deterministic/static section only |
| 1 | section has source data and deterministic fallback |
| 2 | section has derived evidence service |
| 3 | section has approved claim/action contract |
| 4 | section has opt-in provider-backed explanation with parser/validator |
| 5 | section is integrated into async full report + persistence boundary |

## Current provider integration decision

Training is the only full-report section marked as provider-integrated in v1.

Training is Level 5 because it has:

- backend-approved quote context
- training evidence claim service
- strict provider parser/validator
- deterministic fallback
- async full-report integration
- safe persistence metadata
- runtime QA through `direct_ollama/qwen2.5:3b`

Non-training sections remain deterministic/current-state for full-report ownership. Nutrition now has a Level 3 boundary, but it is not provider-integrated and does not replace Nutrition Target Display.

Important nuance:

- The app may have standalone/debug provider experiments for other content.
- Those are not promoted to full-report section ownership by this registry.
- They must not be treated as qwen/full-report product voice until each section gets its own evidence, approved-claim, parser, validator, fallback, and persistence path.

## Composition metadata

`build_health_report_persistence_metadata(...)` now includes safe registry metadata:

```text
full_report_section_registry_version=full_report_section_registry_v1
full_report_section_ids=overall_score,profile_context,grounded_recommendation,nutrition_target_display,nutrition_report_section,training,biggest_issue,likely_cause,priority_action,best_recommendation
provider_integrated_report_sections=training
```

This lets persisted report history identify which section map was used without storing raw/debug/provider internals.

## Boundaries preserved

This milestone does not:

- make `direct_ollama` default
- promote `qwen3`
- tune `qwen3`
- replace the full report with one model call
- loosen validators
- expose raw provider output
- expose raw CrewAI errors
- persist raw provider output publicly
- redesign Streamlit
- add provider UI controls
- add foods
- add exercises
- change workout generation
- change meal planning
- broaden CrewAI usage

## Tests

Focused test:

```bash
pytest tests/test_full_report_section_registry.py -q
```

Related tests:

```bash
pytest tests/test_full_report_composition_boundary.py -q
pytest tests/test_report_persistence_boundary.py -q
pytest tests/test_full_report_async_provider_integration.py -q
pytest tests/test_training_report_section_full_report_integration.py -q
pytest tests/test_report_status.py -q
pytest tests/test_training_report_section_provider_service.py -q
pytest tests/test_training_evidence_claim_service.py -q
pytest tests/test_training_execution_summary_service.py -q
pytest tests/test_longitudinal_qa_seed_data.py -q
pytest tests/test_seed_training_execution_qa.py -q
pytest tests/test_api_smoke.py -q
```

## Future path

The long-term product path remains:

```text
section-owned evidence and claims
→ qwen3 explanation section by section
→ section validator
→ approved section
→ composed full report
```

Not:

```text
one qwen3 call owns the entire report truth
```
