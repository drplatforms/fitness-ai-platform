# Nutrition Provider Approved Suggestion Context Inspection v1

Status: IMPLEMENTED / READY FOR RUNTIME QA

## Context

Nutrition Provider Practical Food Focus Runtime QA v1 passed with improved diagnostics. User 105, which has no approved food suggestions, is now provider-approved. Users 101-104 still fail practical_food_focus validation with approved food suggestions available.

Remaining repeated diagnostic:

- validation_error_categories: ["unsupported_food_suggestion"]
- validation_error_fields: ["practical_food_focus"]
- nutrition_approved_food_suggestion_count: 3

## Goal

Tune the approved-food-suggestion-present path without changing the successful no-approved-suggestion path.

## Implemented behavior

The provider-safe Nutrition context now includes backend-approved practical_food_focus option lists:

- approved_practical_food_focus_options
- approved_practical_food_focus_unavailable_options

When approved food suggestions exist, the direct-Ollama prompt tells the provider to copy exactly one sentence from approved_practical_food_focus_options.

When approved food suggestions are absent, the prompt tells the provider to copy exactly one sentence from approved_practical_food_focus_unavailable_options.

## Why this is safer

The provider no longer needs to infer how to phrase practical_food_focus from raw approved_food_suggestions data. The backend supplies exact safe sentences that already respect approved display names, approved gram values, and no-invention boundaries.

## Boundaries preserved

- no broad validator loosening
- no invented foods
- no unsupported serving sizes or gram values
- no substitutions
- no supplements
- no meal plans
- no qwen3
- no Nutrition Level 5 promotion
- no Training behavior changes
- no Streamlit/UI changes

## Expected next status

READY_FOR_APPROVED_SUGGESTION_RUNTIME_QA
