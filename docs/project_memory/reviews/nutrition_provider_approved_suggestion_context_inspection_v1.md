# Nutrition Provider Approved Suggestion Context Inspection v1 Review

## Decision

Implemented as a narrow approved-suggestion context and prompt tuning fix.

## Finding

The approved_food_suggestions context already includes exact display_name, suggested_grams, macro_gap_addressed, reason-code-related fields, and safe nutrient estimates. However, qwen2.5 still has to transform those structured fields into practical_food_focus prose, and runtime QA showed that transformation remained fragile for users 101-104.

## Fix

Add backend-approved practical_food_focus sentence options to the provider-safe context and instruct the provider to copy exactly from those options.

This keeps the validator strict while reducing ambiguity for the provider.

## Tests added/proved

- provider-safe context includes exact backend-approved practical_food_focus options
- exact backend-approved practical_food_focus option passes validation
- paraphrased food names fail validation
- unapproved gram values fail validation
- direct-Ollama prompt includes approved_practical_food_focus_options
- direct-Ollama prompt requires copying exactly one sentence
- no-approved-suggestion limitation path remains protected by approved unavailable options

## Runtime QA required

Yes. The next runtime QA should rerun users 101-105 with qwen2.5:3b and verify that users 101-104 practical_food_focus failures reduce or resolve while user 105 does not regress.
