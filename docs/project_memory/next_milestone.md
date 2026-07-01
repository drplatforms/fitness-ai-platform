# Next Milestone — Architecture Selection After Recovery Intelligence v2 QA Seed Matrix Validation v1

This next milestone should be selected only after Recovery Intelligence v2 QA Seed Matrix Validation v1 is accepted, merged to `main`, pushed, and snapshotted.

Current implementation milestone before this next step:

```text
Recovery Intelligence v2 QA Seed Matrix Validation v1
```

Current implementation baseline:

```text
f50a1cb main_merge-recovery-intelligence-v2-product-language-docs-cleanup-v1
```

Current implementation snapshot:

```text
fitness_ai_snapshot_2026-07-01_f50a1cb_main_merge-recovery-intelligence-v2-product-language-docs-cleanup-v1.zip
```

Likely next owner:

```text
Architecture
```

Likely next purpose:

```text
Review seed-matrix evidence and decide whether Recovery Intelligence v2 has enough backend confidence to begin Daily Coach Note Recovery v2 Integration v1.
```

Recommended next sequence:

```text
1. Architecture reviews Recovery Intelligence v2 QA Seed Matrix Validation v1 evidence.
2. If accepted, Architecture may authorize Daily Coach Note Recovery v2 Integration v1.
```

Non-goals unless Architecture explicitly authorizes them:

```text
Daily Coach Note integration
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

---

# Next Milestone — Architecture Selection After Recovery Intelligence v2 Dev Inspection Tool v1

This next milestone should be selected only after Recovery Intelligence v2 Developer Artifact / Inspection Tool v1 is accepted, merged to `main`, pushed, and snapshotted.

Current implementation milestone before this next step:

```text
Recovery Intelligence v2 Developer Artifact / Inspection Tool v1
```

Current implementation baseline:

```text
09c6581 main_merge-recovery-intelligence-v2-service-v1
```

Current implementation snapshot:

```text
fitness_ai_snapshot_2026-07-01_09c6581_main_merge-recovery-intelligence-v2-service-v1.zip
```

Likely next owner:

```text
Architecture
```

Likely next purpose:

```text
Choose the next Recovery Intelligence v2 slice after the developer inspection artifact exists. Candidate paths include QA Seed Matrix Validation v1 or future Daily Coach Note Recovery v2 Integration v1, but neither is authorized until Architecture scopes it.
```

Recommended next sequence:

```text
1. Recovery Intelligence v2 QA Seed Matrix Validation v1
2. Daily Coach Note Recovery v2 Integration v1
```

Non-goals unless Architecture explicitly authorizes them:

```text
Daily Coach Note integration
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

---

# Next Milestone — Architecture Selection After Recovery Intelligence v2 Service v1

This next milestone should be selected only after Recovery Intelligence v2 Service v1 is accepted, merged to `main`, pushed, and snapshotted.

Current implementation milestone before this next step:

```text
Recovery Intelligence v2 Service v1
```

Current implementation baseline:

```text
dd6db0f main_merge-recovery-intelligence-v2-model-contract-v1
```

Current implementation snapshot:

```text
fitness_ai_snapshot_2026-06-30_dd6db0f_main_merge-recovery-intelligence-v2-model-contract-v1.zip
```

Planning source:

```text
docs/project_memory/architecture/recovery_intelligence_v2_plan.md
```

Likely next owner:

```text
Architecture
```

Likely next purpose:

```text
Choose the next Recovery Intelligence v2 slice after the read-only service exists. Candidate paths include a developer artifact/inspection tool or Daily Coach Intelligence Snapshot v3 integration, but neither is authorized until Architecture scopes it.
```

Possible future deliverables after Architecture approval:

```text
tools/dev_recovery_intelligence_v2.py
Daily Coach Intelligence Snapshot v3 integration
Recovery Intelligence v2 QA seed matrix artifacts
```

Non-goals unless Architecture explicitly authorizes them:

```text
Daily Coach Note integration
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

---

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
Daily Coach Note integration
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
