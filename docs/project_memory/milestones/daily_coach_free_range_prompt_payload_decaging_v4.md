# Accepted Status — Daily Coach Free-Range Prompt + Payload Decaging v4

Status:

```text
DAILY_COACH_FREE_RANGE_PROMPT_PAYLOAD_DECAGING_V4_ACCEPTED_AS_DEVELOPER_ONLY_DIAGNOSTIC_BASELINE
```

Main merge commit:

```text
56d63c4
```

Snapshot:

```text
fitness_ai_snapshot_2026-06-29_56d63c4_main_merge-daily-coach-free-range-decaging-diagnostic-baseline-v4.zip
```

Meaning:

```text
Accepted as developer-only diagnostic baseline. Not production Today behavior and not provider promotion.
```

---

# Daily Coach Free-Range Prompt + Payload Decaging v4

## Status

`DAILY_COACH_FREE_RANGE_PROMPT_PAYLOAD_DECAGING_V4_IMPLEMENTATION_CANDIDATE`

## Baseline

Baseline branch:

```text
feature/daily-coach-free-range-output-completion-coach-surface-polish-data-seeding-v3
```

Baseline commit:

```text
c36c50a Polish free range output and data seeding
```

Implementation branch:

```text
feature/daily-coach-free-range-prompt-payload-decaging-v4
```

## Purpose

This milestone continues the unmerged free-range Daily Coach experiment after v3 reduced several issues but still left the model too backend-bound.

The purpose is to split internal/debug payloads from the model-facing coach packet, decage the prompt, and let GPT-5.5 write more naturally from clean coaching facts.

Core direction:

```text
Backend computes facts.
Backend provides clean source material.
Backend labels safety/precision internally.
Model gets clean, human-readable source facts.
Model writes freely.
Diagnostics audit afterward.
```

## Why v4 exists

v3 was promising, but QA/product review found the output still inherited too much backend wording, field naming, category labeling, and report-shaped structure.

The core problem is not model intelligence. The model is still being fed too much backend-shaped material and then trying to make it sound conversational.

v4 should make the provider prompt feel less like a backend report and more like organized source material for a coach.

## Implemented scope

### Deterministic provider opt-in regression

Deterministic provider runs must not be blocked by live-provider opt-in.

Expected rule:

```text
OpenAI/live provider + no allow_live_provider:
  skip with live_provider_not_allowed

deterministic provider + no allow_live_provider:
  run normally and write deterministic draft
```

OpenAI/live-provider opt-in safety must remain unchanged.

### Debug payload vs model-facing coach facts

The implementation should preserve internal/debug artifacts such as:

```text
full_user_day_packet.json
provider_payload_debug.json
```

These may include internal labels, backend field names, enum values, raw diagnostics, and technical data.

The provider prompt should instead use a cleaner model-facing layer when decaged mode is enabled:

```text
model_facing_coach_facts.json
model_facing_coach_facts.md
```

The model-facing packet should translate backend concepts into plain-language coaching facts.

Examples of backend-shaped terms that should be translated or kept debug-only:

```text
volume_load
main lever
confidence
limiter
anchor
gap
Rapid Increase
Progressing
High
Low
Moderate
weight_change
internal_workout_model
value_precision
quote_style
macro_gap
```

### Decaged prompt mode

The decaged prompt should tell the model:

```text
Write like a human coach.
Use the facts, but do not echo field labels.
Do not turn internal category names into prose.
Do not copy backend wording.
Use natural wording when discussing uncertainty.
Use numeric cards/tables only when they help readability.
If a detail sounds technical, either translate it or leave it out.
You may choose what matters most today.
You do not need to mention every fact.
```

This is not a phrase-ban loop.

A small instruction such as this is allowed:

```text
Do not use internal labels as user-facing phrases.
```

### Editorial judgment

The model should be allowed to select what matters most.

Guidance:

```text
You are not required to mention every number.
Lead with the coaching message.
Use details only when they support the message.
Dense numeric detail belongs in compact cards, not in the main paragraph.
If a metric would confuse a normal user, explain it briefly or omit it.
```

Example preferred prose:

```text
Your recent training workload has been high, so keep the session controlled instead of turning it into a max test.
```

Avoid surfacing unexplained technical metrics such as:

```text
35,406 total volume load
```

in the main coach note.

### Food and snack formatting

Food/snack cards should use natural ordering and aggregated meal/snack macros.

Bad shape:

```text
roughly chicken breast + rice — 52g protein, 486 calories
```

Preferred shape:

```text
Chicken breast + rice — roughly 52g protein, 486 calories
```

Better section shape:

```text
Approximate meal options:
- Chicken breast + rice — 52g protein, 486 calories
- Turkey wrap — 55g protein, 440 calories
- Oatmeal + whey — 34g protein, 420 calories
- Salmon + potatoes — 45g protein, 610 calories
```

The heading can carry uncertainty once.

Avoid repeating `roughly` on every number.

Do not produce:

```text
roughly 0g fat
```

Prefer:

```text
0g fat
```

Ingredient-level dumps should be aggregated before display.

### Reduce overuse of roughly

Model-facing guidance should explain:

```text
The meal-option numbers are estimates.
You can introduce the section once as approximate instead of repeating "roughly" on every number.
Do not hedge zero values.
```

### Remove Markdown from Today-style drafts

Today-style coach prose should avoid decorative Markdown:

```text
No Markdown bold.
No emoji headers.
No decorative Markdown.
```

Markdown tables are acceptable in artifact/card files only.

### Macro range decaging

Macro range guidance should avoid panic-level deficit framing.

Model-facing guidance should include:

```text
This is logged intake so far, not necessarily final daily intake.
Do not frame the full calorie range as a panic-level deficit.
Use the macro card for details.
In prose, say logged intake is below target and the next meal should include protein and carbs.
Consider remaining meals/time of day if available.
```

If time of day is unavailable:

```text
Based on what is logged so far...
```

Preferred action language:

```text
If anything is missing, log it first. Then make the next meal count.
Start with the next meal: protein first, then carbs.
```

Avoid:

```text
fix the day
```

### Direct and hypeman clean variants

v4 should emphasize the cleanest voice signals:

```text
direct
hypeman
practical-direct
direct-with-hypeman-closer
```

Possible variants:

```text
free_range_full_user_day_direct_clean
free_range_full_user_day_hypeman_clean
free_range_full_user_day_practical_direct
free_range_full_user_day_direct_with_hypeman_closer
```

Hypeman should keep energy but avoid:

```text
reckless advice
emoji spam
bold markdown
gym-bro nonsense
grinders
ego jumps
```

Use:

```text
ego lifts
```

not:

```text
ego jumps
ego reps
```

### Completion diagnostics

Preserve and improve:

```text
completion_diagnostics.md
completion_diagnostics.json
```

Report:

```text
expected_drafts
captured_drafts
complete_drafts
truncated_drafts
skipped_drafts
per-draft completion_status
finish_reason when available
output_tokens when available
max_output_tokens
```

Acceptance target:

```text
0 truncated drafts
```

If any remain, they must be clearly identified.

### Decaging artifacts

Preserve exact first-pass capture:

```text
first_pass_drafts.md
```

Add:

```text
model_facing_coach_facts.md
model_facing_coach_facts.json
decaging_summary.md
backend_label_exposure_summary.md
```

`backend_label_exposure_summary.md` should answer:

```text
Which backend/internal labels were present in debug artifacts?
Which labels were removed from model-facing facts?
Which labels still reached the provider prompt?
Which labels appeared in first-pass output?
```

## CLI additions

Extended developer-only CLI:

```text
tools/dev_daily_coach_full_user_day_free_range_trial.py
```

Added flags:

```text
--write-model-facing-coach-facts
--write-decaging-summary
--write-backend-label-exposure-summary
--prefer-decaged-prompt
```

Recommended QA command shape:

```bash
python tools/dev_daily_coach_full_user_day_free_range_trial.py \
  --run-matrix \
  --provider openai \
  --model gpt-5.5 \
  --allow-live-provider \
  --scenario rich_nutrition_training_recovery \
  --repeat 3 \
  --include-voice-variants \
  --prefer-decaged-prompt \
  --write-provider-payload-debug \
  --write-model-input-manifest \
  --write-model-facing-coach-facts \
  --write-decaging-summary \
  --write-backend-label-exposure-summary \
  --write-precision-summary \
  --write-food-candidate-summary \
  --write-completion-diagnostics \
  --write-food-option-card \
  --write-macro-display-card \
  --write-ai-snack-candidates \
  --write-number-formatting-summary \
  --write-voice-style-findings \
  --write-pasteback-report \
  --print-best-variant \
  --print-product-issues \
  --output-dir "$out"
```

Keep the larger developer-only token budget supported:

```bash
export DAILY_COACH_FULL_USER_DAY_MAX_OUTPUT_TOKENS=1400
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

Added artifacts:

```text
model_facing_coach_facts.md
model_facing_coach_facts.json
decaging_summary.md
backend_label_exposure_summary.md
```

Pasteback report should include:

```text
deterministic provider regression status
completion/truncation counts
model-facing coach facts summary
decaging summary
backend label exposure summary
best direct/hypeman outputs
macro range framing review
food/snack formatting review
roughly overuse review
markdown leak review
backend-bound language review
claim risk summary
consistency summary
token/cost summary
artifact safety summary
known baseline drift
```

## Language surface direction

Do not turn this into a brittle phrase-ban list, but the v4 prompt/payload should naturally reduce:

```text
volume load
use the good readiness
grinders
don't chase grinders
fix the day
one intentional meal today is a win
ego jumps
ego reps
roughly 0g fat
main lever
confidence is moderate
nutrition confidence limitation
anchor
protein gap
logging uncertainty
against target
raw enum capitalization
bold Markdown in Today copy
```

Preferred examples:

```text
Your high readiness points to a steady training session.
Recovery looks strong, so train steadily and keep reps clean.
Do not push it too hard.
Start with the next meal: protein first, then carbs.
If anything is missing, log it first.
Food is the thing to focus on today.
Your body seems ready for the work. Make sure it has enough fuel behind it.
No ego lifts.
```

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
DAILY_COACH_FREE_RANGE_PROMPT_PAYLOAD_DECAGING_V4_IMPLEMENTATION_CANDIDATE
```

Final handoff status after commit + Linux validation should be:

```text
DAILY_COACH_FREE_RANGE_PROMPT_PAYLOAD_DECAGING_V4_IMPLEMENTATION_COMPLETE
```

## End Milestone
