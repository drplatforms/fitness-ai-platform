# Daily Coach Free-Range Output Completion + Coach Surface Polish + Data Seeding v3

## Status

`DAILY_COACH_FREE_RANGE_OUTPUT_COMPLETION_COACH_SURFACE_POLISH_DATA_SEEDING_V3_IMPLEMENTATION_CANDIDATE`

## Baseline

Baseline branch:

```text
feature/daily-coach-free-range-voice-precision-payload-enrichment-v2
```

Baseline commit:

```text
d731a6c Enrich free range voice precision payload
```

Implementation branch:

```text
feature/daily-coach-free-range-output-completion-coach-surface-polish-data-seeding-v3
```

## Purpose

This milestone continues the developer-only free-range Daily Coach experiment after v2 showed product signal but also revealed truncation, raw-number formatting, thin food context, and output-surface issues.

The purpose is to improve the free-range coach surface without changing production behavior, adding restrictive gates, or flattening the rich coach note.

Core direction:

```text
Seed more data.
Give the model better food/training/recovery context.
Let it fly.
Capture first pass exactly.
Audit afterward.
```

## Why v3 exists

v2 was a promising partial, not a pass.

Known v2 issues:

- targeted deterministic-provider regression
- visible first-pass truncation
- raw decimal precision in coach prose
- awkward macro target phrasing
- food guidance needed card/table support
- food context remained too thin
- anomalous user 102 weight trend signal
- inconsistent voice style
- remaining backend-ish language
- insufficient display-ready context

This is not a pivot away from the free-range path.

This is the next developer-only iteration.

## Implemented scope

### Deterministic provider opt-in regression

Deterministic provider runs must not be blocked by live-provider opt-in.

Expected rule:

```text
deterministic provider:
  allowed without --allow-live-provider

external/live provider:
  requires --allow-live-provider
```

OpenAI/live-provider safety remains unchanged.

### Completion diagnostics

Added completion/truncation diagnostics artifacts:

```text
completion_diagnostics.md
completion_diagnostics.json
```

Diagnostics may report:

- finish reason
- output token metadata when available
- max output token setting
- completion status
- truncation boolean
- variant id
- repeat index
- local heuristic flags

Local heuristics may include:

- ends with comma
- ends mid-sentence
- incomplete conjunction
- incomplete list item
- markdown table/list not closed
- no terminal punctuation
- output token count near cap

Diagnostics are post-hoc only and do not modify first-pass drafts.

### Display-ready numeric values

Added display-ready surfaces so the model receives cleaner values instead of raw floats.

Examples:

```text
35,406 total volume load
1,278 calories
22 lb
48g protein
256 calories
```

Avoid raw user-facing values such as:

```text
35406.0
1278.0
22.0
48.0g
255.8 calories
```

### Macro display card

Added macro display artifacts:

```text
macro_display_card.md
macro_display_card.json
```

Macro cards present compact display values instead of forcing the coach note to narrate every exact deficit.

Example direction:

```text
Calories: 1,278 / 2,750–3,000
Protein: 101g / 150–200g
Carbs: 155g / 260–465g
Fat: 27g / 60–100g
```

### Food option cards

Added food option artifacts:

```text
food_option_card.md
food_option_card.json
```

Food cards are structured for QA readability and future display surfaces.

Example direction:

```markdown
| Option | Serving | Protein | Calories |
|---|---:|---:|---:|
| Cooked chicken breast | 155g | 48g | 256 |
| Turkey breast | 170g | 49g | 230 |
| Canned tuna | 150g | 38g | 174 |
```

### AI snack / mini-meal candidates

Added developer-only snack/mini-meal candidate artifacts:

```text
ai_snack_candidates.md
ai_snack_candidates.json
```

This is not production meal planning.

Backend creates snack/mini-meal candidates from known seeded/candidate foods. The model may describe them naturally, but should not invent foods outside the candidate pool.

Candidate fields may include:

```text
snack_name
foods_included
serving_notes
estimated_calories
estimated_protein_g
estimated_carbs_g
estimated_fat_g
helps_with
value_precision
quote_style
display_phrase
```

### Bounded scenario food seeding

Added bounded developer-trial food candidate expansion for the free-range scenario.

v3 target:

```text
20–50 practical food candidates available to the scenario/candidate builder
```

Food categories should include:

- protein-focused foods
- carb-support foods
- calorie-support foods
- fat-support foods
- balanced mini-meal components

Full food knowledge expansion remains future work.

Future target:

```text
450–500 practical, curated, coach-usable foods
```

### Weight trend anomaly handling

Added low-confidence/anomaly handling for the developer path.

At minimum, the payload can expose:

```text
weight_trend_confidence: low
weight_trend_surface_to_coach: false
reason: anomalous recent check-in / insufficient confidence
```

If surfaced, display as:

```text
22 lb
```

not:

```text
22.0 change
Rapid Increase
```

Internal debug evidence should remain available.

### Workout/session naming visibility

Added honest visibility for workout/session naming fields:

```text
internal_workout_model
user_facing_session_name
session_type
session_intensity
session_name_source
```

If only an internal label exists, the manifest should say so.

Future milestone:

```text
Daily Coach Workout Type + Session Naming v1
```

### Voice style findings

Added voice-style findings artifact:

```text
voice_style_findings.md
```

The milestone should preserve coach energy and not over-sanitize strong voice.

Strong voice signal to preserve:

```text
Today’s mission: train with fire, execute with discipline, and eat like you actually want the strength progression you’re chasing. Clean reps. Full control. No wasted sets. LET’S WORK.
```

### Full first-pass capture preserved

The full model note remains primary.

Exact first-pass output remains captured in:

```text
first_pass_drafts.md
```

No repair, fallback, phrase cleanup, or product-language rewrite happens before first-pass capture.

## CLI additions

Extended developer-only CLI:

```text
tools/dev_daily_coach_full_user_day_free_range_trial.py
```

Added flags:

```text
--write-completion-diagnostics
--write-food-option-card
--write-macro-display-card
--write-ai-snack-candidates
--write-number-formatting-summary
--write-voice-style-findings
```

Existing free-range inspection flags remain supported:

```text
--include-voice-variants
--write-provider-payload-debug
--write-model-input-manifest
--write-precision-summary
--write-food-candidate-summary
--write-pasteback-report
--print-best-variant
--print-product-issues
```

## Artifacts

Preserved artifacts:

```text
run_config.json
provider_input_prompt.md
provider_payload_debug.json
full_user_day_packet.json
full_user_day_packet_summary.md
model_input_manifest.md
voice_variant_summary.md
precision_usage_summary.md
food_candidate_summary.md
prompt_variants.md
first_pass_drafts.md
first_pass_drafts_compact.md
side_by_side_comparison.md
best_variant_summary.md
product_language_findings.md
claim_risk_summary.md
consistency_summary.md
token_cost_telemetry.md
token_cost_telemetry.csv
artifact_safety_summary.md
pasteback_report.md
```

Added or improved artifacts:

```text
completion_diagnostics.md
completion_diagnostics.json
food_option_card.md
food_option_card.json
macro_display_card.md
macro_display_card.json
ai_snack_candidates.md
ai_snack_candidates.json
number_formatting_summary.md
voice_style_findings.md
```

Pasteback report should include:

- targeted validation result
- completion/truncation summary
- best exact first-pass note
- best voice variant
- food option card
- macro display card
- AI snack candidates summary
- number formatting summary
- weight trend handling summary
- workout/session naming summary
- voice style findings
- claim risk summary
- consistency summary
- token/cost summary
- artifact safety summary
- known baseline drift

## Boundaries preserved

This milestone does not authorize:

```text
production Today replacement
restrictive reviewer/renderer gate
OpenAI default
provider promotion
public UI
Streamlit controls
final approval bypass
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
multi-agent runtime
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

## Validation expectation

Focused tests:

```bash
python -m pytest tests/test_daily_coach_full_user_day_free_range_service.py -q
python -m pytest tests/test_dev_daily_coach_full_user_day_free_range_trial.py -q
```

Project memory:

```bash
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
```

Targeted style checks only on touched files.

Do not use repo-wide mutating formatters.

## Completion status

Backend implementation candidate status:

```text
DAILY_COACH_FREE_RANGE_OUTPUT_COMPLETION_COACH_SURFACE_POLISH_DATA_SEEDING_V3_IMPLEMENTATION_CANDIDATE
```

Final handoff status after commit + Linux validation should be:

```text
DAILY_COACH_FREE_RANGE_OUTPUT_COMPLETION_COACH_SURFACE_POLISH_DATA_SEEDING_V3_IMPLEMENTATION_COMPLETE
```

## End Milestone
