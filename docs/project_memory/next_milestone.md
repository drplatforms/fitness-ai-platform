# Next Milestone — Daily Coach Workout Set Intelligence v1 + Intelligence Snapshot v2

Baseline:

```text
main @ 43927d4
fitness_ai_snapshot_2026-06-30_43927d4_main_merge-daily-coach-intelligence-snapshot-recovery-v1.zip
```

Active milestone:

```text
Daily Coach Workout Set Intelligence v1 + Intelligence Snapshot v2
```

Owner:

```text
Backend Development
```

Purpose:

```text
Build the second read-only Backend Intelligence Foundation slice: Workout Set Intelligence v1 plus Daily Coach Intelligence Snapshot v2.
```

This milestone does not build the full foundation. It deepens the training source-data layer while preserving Recovery Intelligence v1 and existing read-only nutrition/training summaries.

Required implementation:

- `models/workout_set_intelligence_models.py`
- `services/workout_set_intelligence_service.py`
- `models/daily_coach_intelligence_models.py` update
- `services/daily_coach_intelligence_snapshot_service.py` update
- `tools/dev_daily_coach_intelligence_snapshot.py` update
- targeted tests
- project-memory updates

After this milestone, Architecture should review whether Workout Set Intelligence v1 and Daily Coach Intelligence Snapshot v2 are acceptable.

Future next architecture target after acceptance:

```text
Recovery Intelligence v2
```

Remaining Backend Intelligence Foundation slices:

- Recovery Intelligence v2
- Cross-Domain Trend Engine
- Food Knowledge Expansion
- Six-Month Seed Data refinement
