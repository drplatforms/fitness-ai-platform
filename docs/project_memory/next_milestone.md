# Next Milestone — Recovery Intelligence v2 Service v1

This next milestone is recommended only after Recovery Intelligence v2 Model Contract v1 is accepted, merged to `main`, pushed, and snapshotted.

Current implementation milestone before this next step:

```text
Recovery Intelligence v2 Model Contract v1
```

Current implementation baseline:

```text
871d090 main_merge-recovery-intelligence-v2-architecture-planning-v1
```

Current implementation snapshot:

```text
fitness_ai_snapshot_2026-06-30_871d090_main_merge-recovery-intelligence-v2-architecture-planning-v1.zip
```

Planning source:

```text
docs/project_memory/architecture/recovery_intelligence_v2_plan.md
```

Likely next owner:

```text
Backend Development
```

Likely next purpose:

```text
Implement a read-only Recovery Intelligence v2 service that builds the accepted v2 model contract from daily_checkins without changing Daily Coach output, provider behavior, API, UI, schema, or recommendation behavior.
```

Likely future deliverables:

```text
services/recovery_intelligence_v2_service.py
tests/test_recovery_intelligence_v2_service.py
```

Expected future service behavior:

- read from `daily_checkins`
- preserve `checkin_date` as the primary date
- dedupe duplicate same-day check-ins by latest `created_at` / `id`
- construct current-day context, baseline, recent-vs-baseline delta, recent-vs-prior delta, data quality, and indicator interpretations
- keep missing values explicit as unknown / `None`
- expose provenance/source facts
- preserve confidence, reason codes, and limitations
- block medical, diagnostic, injury, illness, sleep-disorder, overtraining, forced-deload, or prescriptive treatment language

Non-goals for the next service slice unless Architecture explicitly expands scope:

```text
Daily Coach Snapshot integration
API changes
Streamlit changes
database/schema changes
provider behavior changes
OpenAI/Ollama/CrewAI changes
recommendation behavior changes
report behavior changes
automatic deloads
workout plan changes
nutrition target changes
RAG/vector/agent work
wearable/HRV integration
medical claims
```

After the service is accepted, a separate later milestone may consider Daily Coach Intelligence Snapshot Recovery v2 integration.
