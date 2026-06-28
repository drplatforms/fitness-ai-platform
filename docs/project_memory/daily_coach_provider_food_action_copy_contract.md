# Daily Coach Provider Food Action Copy Contract

Purpose: define how backend-approved food suggestions may be shown to Daily Coach narrative providers without letting the provider invent foods, serving sizes, or macro facts.

## Core rule

Backend owns food facts, macro gaps, serving amounts, display permission, validation, and fallback.

The provider may only synthesize approved food facts into natural copy.

## Food labels

Canonical food names remain available for traceability/debug, for example:

- `Tuna, Canned in Water`

Provider-facing user copy should prefer backend-generated friendly labels when available, for example:

- `canned tuna`

Friendly labels must be backend-generated and quote/value backed.

If a friendly label exists, visible provider copy should not leak the awkward canonical label.

## Serving display

Serving displays are conservative.

Do not allow the provider to invent:

- one can
- one packet
- half cup
- one scoop
- one bowl
- one serving
- handful
- plate
- snack size

unless Backend explicitly provides a serving display claim.

Grams are allowed only when `suggested_grams` is approved and declared in `quoted_values_used`.

## Nutrition action context

The provider may receive backend-derived `nutrition_action_context` with:

- primary_gap
- secondary_gap
- action_type
- user_goal
- food_action_allowed
- approved_food_option_count
- avoid_actions
- optional timing_hint only when backend-approved

The provider must not infer meal timing, post-workout timing, or serving units unless the context explicitly permits them.

## Preferred wording

Prefer:

- Add an easy protein option.
- One simple protein bump is enough.
- Something simple like canned tuna.
- Keep it simple.

Avoid:

- make nutrition support the work
- useful move
- support the day
- nutrition support
- rebuilding the whole plan
- must eat
- required
- fix it by eating

## Validation

Provider output should fallback if it:

- uses an unquoted friendly food label
- leaks a canonical food label when a friendly label exists
- invents serving display language
- uses banned deterministic/framework phrases
- uses unsupported food/macro claims
- uses raw claim keys or backend/process language
