# Daily Coaching Product Loop v1

Status: PLANNED / READY FOR ARCHITECTURE REVIEW

Expected planning status after acceptance: DAILY_COACHING_PRODUCT_LOOP_V1_PLAN_ACCEPTED

## Scope

Planning/design only.

This milestone defines the daily product loop and recommends `Daily Next Action Panel v1` as the first narrow implementation slice.

## Product objective

Move from separate capable tabs toward a daily operating loop that helps the user answer:

> What should I do today?

## Accepted product direction

The Today page should become the center of the daily flow:

```text
recovery check-in
→ current state
→ nutrition target-vs-actual / logging completeness
→ workout preview / workout execution
→ validated report guidance
→ one next action
```

## First implementation slice

`Daily Next Action Panel v1`

The panel should:

- show one primary action
- explain why it matters using backend-approved state
- point to an existing workflow
- avoid unsupported AI/provider claims
- keep implementation narrow enough for QA

## Ownership

Backend:

- deterministic next-action selection
- reason codes
- workflow targets
- tests

Streamlit UI:

- Today-page rendering
- simple workflow links or pointers

QA:

- seeded user scenario checks
- no unsupported claims
- no provider semantics regression

Architecture:

- truth boundary review
- acceptance of implementation slice

## Recommended next milestone

`Daily Next Action Panel v1`
