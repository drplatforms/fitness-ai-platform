# Recovery Intelligence v2 Developer Artifact / Inspection Tool v1

Status:

```text
RECOVERY_INTELLIGENCE_V2_DEV_INSPECTION_TOOL_V1_IMPLEMENTATION_CANDIDATE
```

Baseline commit:

```text
09c6581 Merge recovery intelligence v2 service v1
```

Baseline snapshot:

```text
fitness_ai_snapshot_2026-07-01_09c6581_main_merge-recovery-intelligence-v2-service-v1.zip
```

Feature branch:

```text
feature/recovery-intelligence-v2-dev-inspection-tool-v1
```

## Purpose

Add a terminal-friendly developer and QA inspection tool for Recovery Intelligence v2 before any future Daily Coach Note, report, recommendation, UI, API, provider, or schema integration.

The tool exists so Architecture, QA, Backend, Product, and future agents can inspect what `build_recovery_intelligence_v2()` believes for a given user/date.

## Added / Expected Files

```text
tools/dev_recovery_intelligence_v2.py
tests/test_dev_recovery_intelligence_v2_tool.py
docs/project_memory/milestones/recovery_intelligence_v2_dev_inspection_tool_v1.md
```

## CLI Contract

Primary command:

```text
python tools/dev_recovery_intelligence_v2.py --user-id 102 --date 2026-06-14
```

Supported options:

```text
--user-id
--date
--json
--compact
--show-source-facts
--hide-source-facts
```

JSON mode prints only valid formatted JSON from `RecoveryIntelligenceV2Summary.to_dict()`.

Text mode prints pasteback-friendly terminal sections for current day, baseline, recent deltas, indicators, classifications, data quality, reason codes, limitations, coach-safe summary, and source facts.

## Naming Note

New roadmap/docs language should prefer:

```text
Daily Coach Note
```

instead of casually adding more product-facing uses of:

```text
Daily Coach Note
```

Existing implementation names such as `DailyCoachIntelligenceSnapshot` are not renamed by this milestone.

## Non-Goals

This milestone does not authorize or implement:

```text
Daily Coach Note integration
Daily Coach behavior changes
report behavior changes
recommendation behavior changes
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
```

## Validation Focus

Required validation includes:

```text
python -m pytest tests/test_dev_recovery_intelligence_v2_tool.py -q
python -m pytest tests/test_recovery_intelligence_v2_service.py -q
python -m pytest tests/test_recovery_intelligence_v2_models.py -q
python -m pytest tests/test_recovery_intelligence_service.py -q
python -m pytest tests/test_daily_coach_intelligence_snapshot_service.py -q
python -m pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
scripts/dev_commit_check.ps1 -Mode code
```

## Recommended Next Step After Acceptance

Architecture should select the next Recovery Intelligence v2 slice. Likely next sequence:

```text
Recovery Intelligence v2 QA Seed Matrix Validation v1
Daily Coach Note Recovery v2 Integration v1
```

Do not wire Recovery Intelligence v2 into the Daily Coach Note until the developer artifact and QA matrix provide enough confidence in service outputs.
