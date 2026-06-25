# Review — Daily Narrative Coaching Intelligence + Voice Lab v1

Status: ready for Architecture review

## Acceptance target

`DAILY_NARRATIVE_COACHING_INTELLIGENCE_VOICE_LAB_V1_ACCEPTED`

## Review notes

This milestone is a product-language workflow improvement, not a model escalation. It creates a Developer Mode lab with synthetic scenario fixtures, visible reason codes, coaching angles, deterministic candidates, and copy-quality checks so the user has concrete examples to critique.

## Manual QA focus

Review these scenarios:

- `nutrition_present_training_missing`
- `training_present_nutrition_missing`
- `low_data_multiple_domains`
- `rich_day_multiple_domains`
- `mixed_signals_day`
- `workout_completed_no_sets`

Acceptance should focus on whether the lab produces meaningfully different, fact-grounded copy examples and avoids known rejected phrases such as “selected date,” “signal,” “concrete anchor,” “light read,” “useful move,” and “clearer picture.”
