# Accepted Status — Daily Coach Fully Free Source-Data Lab v1

Status:

```text
DAILY_COACH_FULLY_FREE_SOURCE_DATA_LAB_V1_ACCEPTED_AS_DEVELOPER_ONLY_EVIDENCE
```

Review classification:

```text
DAILY_COACH_FULLY_FREE_SOURCE_DATA_LAB_V1_QA_REVIEWED_NOT_BETTER_THAN_V4_GENERIC_STILL_CONSTRAINED_PROVIDER_PAUSE_RECOMMENDED
```

Source feature branch:

```text
feature/daily-coach-fully-free-source-data-lab-v1
```

Source feature commit:

```text
f6fb371 Add fully free source data coach lab
```

Main merge commit:

```text
23b5378 Merge daily coach fully free source-data lab evidence v1
```

Snapshot:

```text
fitness_ai_snapshot_2026-06-29_23b5378_main_merge-daily-coach-fully-free-source-data-lab-evidence-v1.zip
```

Conclusion:

```text
Useful ceiling test. Technically complete. Did not beat v4 meaningfully. Provider voice iteration pauses.
```

---

# Daily Coach Fully Free Source-Data Lab v1

## Status

`DAILY_COACH_FULLY_FREE_SOURCE_DATA_LAB_V1_IMPLEMENTATION_CANDIDATE`

## Baseline

Baseline branch:

```text
main
```

Baseline commit:

```text
56d63c4 Merge daily coach free-range decaging diagnostic baseline v4
```

Implementation branch:

```text
feature/daily-coach-fully-free-source-data-lab-v1
```

## Purpose

This milestone starts after the free-range decaging diagnostic baseline v4 was merged to `main` and snapshotted.

The goal is to test GPT-5.5's Daily Coach ceiling from clean, organized source data with almost no coaching cage.

Fully free means:

```text
No deterministic coach prose.
No renderer template.
No phrase-ban loop.
No product voice cage.
No backend category names as prose.
No forced structure.
No requirement to mention every fact.
No coaching conclusion handed to the model.
```

Fully free does not mean unsafe. The lab still preserves safety boundaries, exact first-pass capture, post-hoc audit, OpenAI opt-in, developer-only artifacts, and unchanged normal Today behavior.

## Implemented scope

### Separate developer-only tool

Added:

```text
tools/dev_daily_coach_fully_free_source_data_lab.py
```

The lab is separated from the v4 free-range trial path for inspection clarity.

### Source-data packet

Added artifacts:

```text
fully_free_source_data_packet.json
fully_free_source_data_packet.md
```

The packet groups clean facts by domain:

```text
user_context
today_context
recovery_source_data
training_source_data
nutrition_source_data
food_and_snack_source_data
body_metrics_source_data
recent_history_source_data
available_unknowns
safety_boundaries
```

The packet avoids backend-shaped coaching summaries and keeps backend terms out of model-facing source material where possible.

### Minimal prompt

The lab uses a much shorter prompt than v4. It tells the model to use only the source data, avoid invented facts, avoid medical diagnosis and unsafe training advice, write naturally, choose what matters most, and leave confusing metrics out or explain them simply.

No examples, deterministic fallback copy, renderer structure, product voice cage, or phrase-ban list are included.

### Fully free prompt variants

Supported variants:

```text
fully_free_minimal
fully_free_human_coach
fully_free_direct
fully_free_energy
fully_free_story_style
fully_free_no_structure
```

Variants are short and intentionally less prescriptive than v4 voice variants.

### Exact provider input and first-pass capture

Required artifacts include:

```text
provider_input_prompt.md
provider_payload_debug.json
first_pass_drafts.md
first_pass_drafts_compact.md
run_config.json
token_cost_telemetry.md
token_cost_telemetry.csv
artifact_safety_summary.md
pasteback_report.md
```

No repair, fallback, reviewer, renderer, or mutation happens before first-pass capture.

### Backend-prose contamination audit

Added:

```text
backend_prose_contamination_summary.md
backend_prose_contamination_summary.json
```

The audit scans provider prompt, source packet, and first-pass drafts for backend-shaped phrases. It reports findings only and does not mutate drafts.

### Source-data completeness summary

Added:

```text
source_data_completeness_summary.md
source_data_completeness_summary.json
```

This answers which source domains were available, which were unavailable, and what remains too thin for future architecture.

### Model freedom summary

Added:

```text
model_freedom_summary.md
model_freedom_summary.json
```

Expected values:

```text
phrase_bans_included: false
deterministic_coach_prose_included: false
renderer_structure_included: false
output_structure_forced: false
model_can_choose_what_matters: true
```

### Completion diagnostics

Preserved/adapted:

```text
completion_diagnostics.md
completion_diagnostics.json
```

Reports expected, captured, complete, truncated, and skipped drafts with per-draft status fields where available.

## Boundaries preserved

This milestone does not authorize:

```text
production Today replacement
renderer/reviewer gate
OpenAI default
provider promotion
public UI
Streamlit controls
raw DB dumps
raw provider envelope persistence
secrets in artifacts
medical advice generation
meal planning production changes
workout generation production changes
nutrition target changes
recovery score changes
RAG
embeddings
vector database implementation
multi-agent runtime
LangGraph orchestration
CrewAI orchestration
LlamaIndex orchestration
Headroom/context compression
local model comparison
cheaper model comparison
project memory handoff-compression/stale-doc hygiene
full 450–500 food expansion
```

## Known baseline drift

Known baseline drift remains intentionally unpatched:

```text
tests/test_daily_narrative_rich_day_service.py
```

Known mismatch:

```text
expected:
Read the day before adding more

actual:
Consider the full day
```

Do not claim full-suite green if this remains.

## Completion status

Backend implementation candidate status:

```text
DAILY_COACH_FULLY_FREE_SOURCE_DATA_LAB_V1_IMPLEMENTATION_CANDIDATE
```

Final handoff status after commit + Linux validation should be:

```text
DAILY_COACH_FULLY_FREE_SOURCE_DATA_LAB_V1_IMPLEMENTATION_COMPLETE
```

## End Milestone
