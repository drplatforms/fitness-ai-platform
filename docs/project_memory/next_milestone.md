# Next Milestone — Architecture Review After Daily Coach GPT Family Human Voice Trial v1

This next milestone should be selected only after Daily Coach GPT Family Human Voice Trial v1 is accepted, pushed, and reviewed by Architecture.

Current implementation milestone before this next step:

```text
Daily Coach GPT Family Human Voice Trial v1
```

Current implementation baseline:

```text
05313fd Merge daily coach human voice prompt contract v1
```

Current implementation snapshot:

```text
fitness_ai_snapshot_2026-07-01_05313fd_main_merge-daily-coach-human-voice-prompt-contract-v1.zip
```

Likely next owner:

```text
Architecture
```

Likely next purpose:

```text
Review whether GPT-family/OpenAI raw human-voice trial evidence is useful enough to guide future Daily Coach voice work.
```

Recommended next sequence:

```text
1. Backend completes the developer-only GPT-family/OpenAI trial tooling and reports validation evidence.
2. Architecture reviews raw trial outputs, if any real OpenAI smoke was run.
3. Architecture decides whether to continue prompt iteration, run additional model comparisons, or route a separate product-integration design.
```

Non-goals unless Architecture explicitly authorizes them:

```text
normal Today provider calls
Today UI
Streamlit UI layout
API routes
database schema
migrations
persistence behavior
report behavior
recommendation behavior
Daily Next Action selection logic
Daily Coach Note public copy
workout plan behavior
nutrition target behavior
automatic deload logic
automatic progression logic
wearable/HRV integration
medical interpretation
provider promotion
model approval
RAG/vector/agent behavior
CrewAI behavior
OpenAI behavior outside explicit developer CLI
```

---
# Next Milestone — Architecture Review After Daily Coach Human Voice Prompt Contract v1

This next milestone should be selected only after Daily Coach Human Voice Prompt Contract v1 is accepted, merged to `main`, pushed, and snapshotted by Architecture.

Current implementation milestone before this next step:

```text
Daily Coach Human Voice Prompt Contract v1
```

Current implementation baseline:

```text
d5bfd29 Merge daily coach provider preview raw data payload v1
```

Current implementation snapshot:

```text
fitness_ai_snapshot_2026-07-01_d5bfd29_main_merge-daily-coach-provider-preview-raw-data-payload-v1.zip
```

Likely next owner:

```text
Architecture
```

Likely next purpose:

```text
Review whether human-editable Daily Coach voice prompt iteration is now safe enough to support manual prompt trials without Python patching.
```

Recommended next sequence:

```text
1. Architecture reviews Daily Coach Human Voice Prompt Contract v1 implementation evidence.
2. If accepted, Architecture may authorize a manual prompt QA/trial milestone using the developer-only runner.
3. Any later provider-product integration must remain separately scoped and must not reuse the rejected runtime-spike prompt path.
```

Non-goals unless Architecture explicitly authorizes them:

```text
normal Today provider calls
Today UI
Streamlit UI layout
API routes
database schema
migrations
persistence behavior
report behavior
recommendation behavior
Daily Next Action selection logic
Daily Coach Note public copy
workout plan behavior
nutrition target behavior
automatic deload logic
automatic progression logic
wearable/HRV integration
medical interpretation
provider promotion
model approval
RAG/vector/agent behavior
CrewAI behavior
OpenAI behavior
```

---
# Next Milestone — Architecture Selection After Daily Coach Provider Preview Raw Data Payload v1

This next milestone should be selected only after Daily Coach Provider Preview Raw Data Payload v1 is accepted, merged to `main`, pushed, and snapshotted.

Current implementation milestone before this next step:

```text
Daily Coach Provider Preview Raw Data Payload v1
```

Current implementation baseline:

```text
e26c4e0 Merge daily coach note copy QA matrix v1
```

Current implementation snapshot:

```text
fitness_ai_snapshot_2026-07-01_e26c4e0_main_merge-daily-coach-note-copy-qa-matrix-v1.zip
```

Likely next owner:

```text
Architecture
```

Likely next purpose:

```text
Review whether the developer-only raw data payload is sufficient as the future provider-preview input surface before authorizing any provider call, provider prompt, or Daily Coach Note copy generation work.
```

Recommended next sequence:

```text
1. Architecture reviews Daily Coach Provider Preview Raw Data Payload v1 evidence.
2. QA verifies the payload is developer-only, read-only, source-labeled, and free of final-copy/sentence-bank fields.
3. Architecture decides whether to authorize a later provider-preview prompt/runtime slice, a payload inspection slice, or another source-data enrichment slice.
```

Future provider voice reminder:

```text
Future provider work should receive raw deterministic backend data, source facts, confidence, limitations, recovery/training/nutrition indicators, and user context. It should not be forced into backend-authored sentence banks or only backend-written prose summaries.
```

Non-goals unless Architecture explicitly authorizes them:

```text
provider-generated Daily Coach Note copy
provider calls from normal Today load
Daily Next Action selection changes
API changes
Streamlit layout changes
database/schema changes
OpenAI/Ollama/CrewAI behavior changes
model routing
Prompt Lab runtime behavior
recommendation behavior changes
report behavior changes
automatic deloads
automatic progression
workout plan changes
nutrition target changes
RAG/vector/agent work
wearable/HRV integration
medical claims
```

---
# Next Milestone — Architecture Selection After Daily Coach Note Copy QA Matrix v1

This next milestone should be selected only after Daily Coach Note Copy QA Matrix v1 is accepted, merged to `main`, pushed, and snapshotted.

Current implementation milestone before this next step:

```text
Daily Coach Note Copy QA Matrix v1
```

Current implementation baseline:

```text
33ebf18 Merge daily coach note recovery-aware language v1
```

Current implementation snapshot:

```text
fitness_ai_snapshot_2026-07-01_33ebf18_main_merge-daily-coach-note-recovery-aware-language-v1.zip
```

Likely next owner:

```text
Architecture
```

Likely next purpose:

```text
Review whether Daily Coach Note public-copy evaluation coverage is sufficient, then choose the next narrow Daily Coach Note or provider-preview slice.
```

Recommended next sequence:

```text
1. Architecture reviews Daily Coach Note Copy QA Matrix v1 evidence.
2. QA verifies deterministic Today card copy remains safe, bounded, backward compatible, and unchanged without a supplied recovery contract.
3. Architecture decides whether to authorize broader Daily Coach Note integration, provider-preview copy experimentation, or another documentation/QA hardening slice.
```

Future provider voice reminder:

```text
Future provider work should receive raw deterministic backend data, source facts, confidence, limitations, recovery/training/nutrition indicators, and user context. It should not be forced into backend-authored sentence banks or only backend-written prose summaries.
```

Non-goals unless Architecture explicitly authorizes them:

```text
provider-generated Daily Coach copy
Daily Next Action selection changes
API changes
Streamlit layout changes
database/schema changes
OpenAI/Ollama/CrewAI behavior changes
recommendation behavior changes
report behavior changes
automatic deloads
automatic progression
workout plan changes
nutrition target changes
RAG/vector/agent work
wearable/HRV integration
medical claims
```

---

# Next Milestone — Architecture Selection After Daily Coach Note Recovery-Aware Language v1

This next milestone should be selected only after Daily Coach Note Recovery-Aware Language v1 is accepted, merged to `main`, pushed, and snapshotted.

Current implementation milestone before this next step:

```text
Daily Coach Note Recovery-Aware Language v1
```

Current implementation baseline:

```text
c940ff4 Merge recovery-aware coach copy contract v1
```

Current implementation snapshot:

```text
fitness_ai_snapshot_2026-07-01_c940ff4_main_merge-recovery-aware-coach-copy-contract-v1.zip
```

Likely next owner:

```text
Architecture
```

Likely next purpose:

```text
Review whether the deterministic Today card can now safely use the recovery-aware copy contract, then choose the next narrow Daily Coach Note integration slice.
```

Recommended next sequence:

```text
1. Architecture reviews Daily Coach Note Recovery-Aware Language v1 evidence.
2. QA verifies Today card copy remains bounded, public-safe, and unchanged without a supplied contract.
3. Architecture chooses whether to authorize broader Daily Coach Note integration or keep recovery-aware language limited to explicit contract-supplied paths.
```

Non-goals unless Architecture explicitly authorizes them:

```text
provider-generated Daily Coach copy
Daily Next Action selection changes
API changes
Streamlit layout changes
database/schema changes
OpenAI/Ollama/CrewAI behavior changes
recommendation behavior changes
report behavior changes
automatic deloads
automatic progression
workout plan changes
nutrition target changes
RAG/vector/agent work
wearable/HRV integration
medical claims
```

---

# Next Milestone — Architecture Selection After Recovery-Aware Coach Copy Contract v1

This next milestone should be selected only after Recovery-Aware Coach Copy Contract v1 is accepted, merged to `main`, pushed, and snapshotted.

Current implementation milestone before this next step:

```text
Recovery-Aware Coach Copy Contract v1
```

Current implementation baseline:

```text
66a70d3 Merge daily coach note recovery v2 integration v1
```

Current implementation snapshot:

```text
fitness_ai_snapshot_2026-07-01_66a70d3_main_merge-daily-coach-note-recovery-v2-integration-v1.zip
```

Likely next owner:

```text
Architecture
```

Likely next purpose:

```text
Review whether the deterministic recovery-aware copy contract is sufficient to authorize a later Daily Coach Note language milestone that uses Recovery Intelligence v2 facts safely.
```

Recommended next sequence:

```text
1. Architecture reviews Recovery-Aware Coach Copy Contract v1 evidence.
2. If accepted, Architecture may authorize a future Daily Coach Note recovery-aware language milestone.
3. That future milestone should still keep final copy bounded by the approved contract and backend-owned facts.
```

Non-goals unless Architecture explicitly authorizes them:

```text
Daily Coach final copy changes
Today card copy changes
API changes
Streamlit changes
database/schema changes
provider behavior changes
OpenAI/Ollama/CrewAI changes
recommendation behavior changes
report behavior changes
automatic deloads
automatic progression
workout plan changes
nutrition target changes
RAG/vector/agent work
wearable/HRV integration
medical claims
```

---

# Next Milestone — Architecture Selection After Daily Coach Note Recovery v2 Integration v1

This next milestone should be selected only after Daily Coach Note Recovery v2 Integration v1 is accepted, merged to `main`, pushed, and snapshotted.

Current implementation milestone before this next step:

```text
Daily Coach Note Recovery v2 Integration v1
```

Current implementation baseline:

```text
d2e0178 main_merge-recovery-intelligence-v2-qa-seed-matrix-validation-v1
```

Current implementation snapshot:

```text
fitness_ai_snapshot_2026-07-01_d2e0178_main_merge-recovery-intelligence-v2-qa-seed-matrix-validation-v1.zip
```

Likely next owner:

```text
Architecture
```

Likely next purpose:

```text
Review whether the backend Daily Coach Note context now exposes Recovery Intelligence v2 facts safely enough to authorize a future recovery-aware copy or recommendation contract.
```

Recommended next sequence:

```text
1. Architecture reviews Daily Coach Note Recovery v2 Integration v1 evidence.
2. If accepted, Architecture may authorize Recovery-Aware Coach Copy Contract v1 or another narrow Daily Coach Note usage milestone.
```

Non-goals unless Architecture explicitly authorizes them:

```text
Daily Coach final copy changes
Today card copy changes
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
