# Open Questions — Recovery Intelligence v2 Architecture Planning v1

Active questions:

1. What specific recovery limitations remain after Recovery Intelligence v1?
2. Which v2 recovery signals should be added without creating medical, diagnostic, injury, illness, sleep-disorder, or overtraining claims?
3. Should v2 remain a pure read-only service layer, or should it also update the Daily Coach Intelligence Snapshot contract?
4. What minimum check-in coverage is required before v2 can use trend language?
5. How should v2 represent confidence, provenance, limitations, and data-quality flags?
6. How should recovery trend interpretation interact with Workout Set Intelligence v1 without turning hard training into unsupported overtraining claims?
7. What exact fields should Backend add to models/services if implementation is later approved?
8. What test scenarios are required before v2 can influence recommendations or report copy?
9. What should remain explicitly out of scope until Cross-Domain Trend Engine planning?
10. Does any stale project-memory status still incorrectly describe `123d115` as the current accepted baseline instead of the historical pre-north-star baseline?

Closed / answered before this milestone:

- Workout Set Intelligence v1 was accepted and merged at `123d115`.
- Daily Coach Intelligence Snapshot v2 now carries recovery and workout-set intelligence.
- Provider voice iteration remains paused.
- RAG/vector/agent work remains future/parked behind backend intelligence.

Known baseline drift remains documented and intentionally out of scope:

```text
tests/test_daily_narrative_rich_day_service.py
expected: Read the day before adding more
actual: Consider the full day
```
