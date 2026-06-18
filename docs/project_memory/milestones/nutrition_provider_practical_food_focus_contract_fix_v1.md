# Nutrition Provider Practical Food Focus Contract Fix v1

Status: IMPLEMENTED / READY FOR RUNTIME QA

## Context

Nutrition Provider Diagnostic Matrix QA Retry v1 passed diagnostics capture and confirmed that rejected Nutrition provider candidates now expose safe validation categories through the debug endpoint.

The repeated rejection field is:

- practical_food_focus

Observed diagnostic pattern:

- users 101-104: unsupported_food_suggestion on practical_food_focus
- user 105: unsupported_food_suggestion_availability_claim on practical_food_focus

Nutrition remains Level 4. Level 5 promotion is not approved.

## Goal

Clarify and tighten the practical_food_focus contract so the provider can safely produce valid output when approved food suggestions exist and when they do not exist.

## Implemented behavior

When approved food suggestions exist, practical_food_focus may only:

- mention exact approved backend food display names
- mention exact approved gram values only when backend supplied them
- summarize the approved suggestion purpose
- use generic approved-list language such as choosing from approved food suggestions

When approved food suggestions are absent, practical_food_focus may only:

- say no approved food suggestion is available from the current evidence
- say the evidence is not enough for a specific food suggestion yet
- recommend improving logging completeness/verification first

Still rejected:

- invented foods
- unapproved serving sizes or gram values
- substitutions
- supplements
- meal-plan language
- implication that approved food suggestions exist when none are approved

## Boundaries preserved

- no broad validator loosening
- no unsupported food suggestion approval
- no unsupported numeric claim approval
- no serving-size expansion
- no new foods
- no meal planning
- no qwen3
- no Nutrition Level 5 promotion
- no Streamlit/UI changes
- no Training provider changes

## Expected next status

READY_FOR_PRACTICAL_FOOD_FOCUS_RUNTIME_QA
