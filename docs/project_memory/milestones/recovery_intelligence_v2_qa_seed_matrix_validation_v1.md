# Milestone — Recovery Intelligence v2 QA Seed Matrix Validation v1

Status:

```text
RECOVERY_INTELLIGENCE_V2_QA_SEED_MATRIX_VALIDATION_V1_IMPLEMENTATION_COMPLETE
```

Source baseline:

```text
f50a1cb main_merge-recovery-intelligence-v2-product-language-docs-cleanup-v1
```

Source snapshot:

```text
fitness_ai_snapshot_2026-07-01_f50a1cb_main_merge-recovery-intelligence-v2-product-language-docs-cleanup-v1.zip
```

Feature branch:

```text
feature/recovery-intelligence-v2-qa-seed-matrix-validation-v1
```

## Purpose

This milestone adds a developer/QA seed matrix validation artifact for Recovery Intelligence v2 before any Daily Coach Note integration.

The seed matrix is intended to answer:

```text
Do the Recovery Intelligence v2 service and developer inspection path produce bounded, sensible, public-safe output across representative recovery scenarios?
```

## Added Files

```text
tools/dev_recovery_intelligence_v2_seed_matrix.py
tests/test_recovery_intelligence_v2_seed_matrix.py
docs/project_memory/milestones/recovery_intelligence_v2_qa_seed_matrix_validation_v1.md
```

## Updated Files

```text
docs/project_memory/current_state.md
docs/project_memory/next_milestone.md
docs/project_memory/project_state.json
```

## Tool Behavior

Primary command:

```text
python tools/dev_recovery_intelligence_v2_seed_matrix.py --date 2026-06-14
```

Supported options:

```text
--date YYYY-MM-DD
--json
--compact
--write-report
--output-dir <path>
```

The tool defines named recovery scenarios:

```text
supportive_recovery
recovery_limited_high_pressure
manageable_mixed_signals
improving_trend
limited_data_missing_checkins
messy_duplicates_same_day
missing_sleep_energy_soreness
body_weight_present_without_overclaiming
```

For each scenario, the runner calls the accepted service function:

```text
build_recovery_intelligence_v2(user_id, target_date)
```

The seed matrix does not duplicate Recovery Intelligence v2 calculations.

## Output Contract

Default text output includes:

```text
Recovery Intelligence v2 Seed Matrix
Baseline Commit
Target Date
Scenario Count
Pass / Fail Summary
Scenario Results
Per-scenario classification, pressure, confidence, data quality, warnings, limitations, and source-fact counts
```

JSON output is valid JSON-only stdout:

```text
no markdown fences
no prose before JSON
no prose after JSON
```

Service/database banners are redirected away from stdout so JSON consumers can parse the output.

If `--write-report` is used, the tool writes a local manual QA artifact under:

```text
qa-runs/recovery_intelligence_v2_seed_matrix_<timestamp>/qa_report.md
```

Generated `qa-runs` output is not committed unless Architecture explicitly authorizes it.

## Boundaries Preserved

This milestone does not add or change:

```text
Daily Coach Note integration
Daily Coach behavior
report behavior
recommendation behavior
API routes
Streamlit UI
provider behavior
OpenAI/Ollama/CrewAI behavior
database schema
migrations
persistence behavior
RAG/vector/agent work
wearable/HRV integration
automatic deload logic
automatic progression logic
medical interpretation
runtime product behavior
```

The tool does not expose:

```text
raw database rows
raw SQL dumps
private notes
debug dumps
secrets
provider payloads
unbounded user text
```

Body weight remains context only. The seed matrix guards against unsupported causation language such as fat-loss/fat-gain or nutrition-blame claims.

## Backend Chat Routing Rule

Backend does not prepare QA findings or QA instructions. Architecture prepares Backend tasks and separately routes QA testing instructions. Backend reports branch, commit, and validation evidence when requested.

## Recommended Next Step

After Architecture accepts this milestone, the likely next milestone is:

```text
Daily Coach Note Recovery v2 Integration v1
```

Architecture should not authorize that integration until seed-matrix evidence is reviewed.
