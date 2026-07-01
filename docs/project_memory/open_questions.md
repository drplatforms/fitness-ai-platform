# Open Questions — Recovery Intelligence v2 Model Contract v1

Active questions for Architecture / Backend review:

1. Does the v2 model contract preserve the accepted Recovery Intelligence v2 architecture plan without sneaking in service behavior?
2. Are readiness classification, recovery pressure, indicator status, trend direction, data-quality status, and confidence values bounded enough for future service use?
3. Do Limited/Low confidence model outputs require reason codes or limitations consistently?
4. Does the contract keep missing values explicit as `None` / unknown instead of coercing incomplete data to zero?
5. Are provenance/source-fact references sufficient for a future read-only service and Daily Coach Snapshot integration?
6. Does the model-level forbidden-language guard block medical, diagnostic, injury, illness, sleep-disorder, overtraining, and forced-deload language where the model owns coach-safe summary text?
7. Does new user/product-facing text prefer indicator language while avoiding churn against existing legacy/internal class names?
8. After this contract is accepted, should Recovery Intelligence v2 Service v1 be the next Backend implementation slice?

Closed / answered before this milestone:

- Recovery Intelligence v2 Architecture Planning v1 was accepted and merged at `871d090`.
- The accepted v2 plan established staged implementation: model contract, then service, then Daily Coach Snapshot integration, then later recommendation/report usage only after separate scope.
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
