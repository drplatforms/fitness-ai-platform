# Current QA Handoff — Docs-Only Project Memory Refresh v1

**Status:** Active QA handoff
**Baseline:** `main @ 23b5378`
**Milestone:** Project Memory + Handoff Workflow Compression + Stale Docs Hygiene + Development Architecture v1

## QA Scope

Validate that the docs now agree on accepted main `23b5378`, Fully Free Source-Data Lab v1 accepted as developer-only evidence, Fully Free v1 not meaningfully better than v4, provider voice iteration paused, docs refresh active milestone, Backend Intelligence Foundation next, exact seven team lanes, DevOps & Tooling narrow/low-frequency, and Portfolio Packaging low-frequency.

## Required Checks

```bash
git diff --check
python -m pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
```

Windows may also run:

```powershell
scripts/dev_commit_check.ps1 -Mode docs-only
fsweep
```

## Known Baseline Drift

Known drift remains intentionally unpatched:

```text
tests/test_daily_narrative_rich_day_service.py
expected: Read the day before adding more
actual: Consider the full day
```

Do not claim full-suite green if this remains.
