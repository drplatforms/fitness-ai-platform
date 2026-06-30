# Stale Docs Hygiene Report v1

**Status:** Active docs-refresh evidence
**Baseline:** `23b5378 Merge daily coach fully free source-data lab evidence v1`
**Snapshot:** `fitness_ai_snapshot_2026-06-29_23b5378_main_merge-daily-coach-fully-free-source-data-lab-evidence-v1.zip`

## Purpose

This report records the stale-doc risks corrected by Project Memory + Handoff Workflow Compression + Stale Docs Hygiene + Development Architecture v1.

## Main Corrections

The docs were moved from:

```text
Fully Free Source-Data Lab v1 is active implementation work from 56d63c4.
```

to:

```text
Fully Free Source-Data Lab v1 was merged as developer-only evidence at 23b5378.
The result was useful but not meaningfully better than v4.
Provider voice iteration is paused.
Docs/process/development architecture cleanup is active.
Backend Intelligence Foundation is next.
```

## Corrected Truth

- Current accepted main: `23b5378`
- Latest accepted snapshot: `fitness_ai_snapshot_2026-06-29_23b5378_main_merge-daily-coach-fully-free-source-data-lab-evidence-v1.zip`
- Fully Free source feature commit: `f6fb371`
- v4 baseline accepted at `56d63c4`
- Fully Free Lab v1 accepted as developer-only evidence
- Provider voice iteration paused
- Backend Intelligence Foundation established as next product center
- Exact seven team lanes recorded
- DevOps & Tooling marked narrow/low-frequency
- Portfolio Packaging marked low-frequency

## Known Baseline Drift

Known drift remains intentionally unpatched:

```text
tests/test_daily_narrative_rich_day_service.py
expected: Read the day before adding more
actual: Consider the full day
```

Do not claim full-suite green if this remains.
