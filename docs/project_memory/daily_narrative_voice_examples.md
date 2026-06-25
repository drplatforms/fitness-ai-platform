# Daily Narrative Voice Examples

Status: Daily Narrative User Feedback Capture + Preferred Rewrite Loop v1

This file is app-side memory for Daily Narrative copy QA. It records rejected wording, why it failed, and preferred directions. Future deterministic/provider copy should use these examples as style guidance without weakening factual grounding.

## nutrition_present_training_missing

Allowed facts:
- Food is logged.
- No workout is logged.
- The coaching read should stay nutrition-based.

Rejected:
> Keep the nutrition note grounded: Because nutrition shows up, but training does not for the selected date, Treat this as a food-context note, not a full training read.

Why it fails:
- “Nutrition note” sounds awkward.
- “food-context note” sounds like internal taxonomy.
- “Because” is forced.
- “selected date” sounds like a QA/debug label.
- The punctuation is too colon/comma heavy.

Preferred:
> I see food logged today, but no workout. That means this can be a nutrition-based read, not a full training recommendation.

## low_data_no_data

Allowed facts:
- There is not enough detail for strong coaching.
- A practical missing entry would improve the next recommendation.

Rejected:
> Add one concrete anchor: Because there is not enough signal for the selected date ending 2026-06-06 to coach from yet. Add the easiest concrete anchor now: a recovery check-in, one meal entry, or the workout you actually completed.

Why it fails:
- “concrete anchor” is weird user-facing language.
- “signal” is too technical.
- “selected date ending...” is backend/QA phrasing.
- The result sounds like an analytics panel, not a coach.

Preferred:
> Today's advice is limited. Log a recovery check-in, a meal or snack, or the workout you completed so the coach has enough to work with.

## generic_logging

Rejected:
> Today's useful move is to keep logging simple. Simple logging helps build a clearer picture.

Why it fails:
- It explains logging with more logging language.
- It does not tell the user why the missing piece matters in this situation.
- It sounds generic and disposable.

Preferred direction:
Only ask for logging when a specific missing piece changes the coaching read.

## rich_day

Allowed facts:
- Recovery, food, and training are present.
- There is enough context to compare the day cautiously.

Rejected:
> You have enough logged to compare the day instead of adding random data. Check whether training, food, and recovery tell the same story before making a stronger call.

Why it fails:
- “adding random data” sounds dismissive and weird.
- It makes the user's own logs sound random.
- The idea is right, but the phrase should be cleaner.

Preferred:
> You have enough logged to review the day before adding more entries. Check whether training, food, and recovery point in the same direction before making a stronger call.

## recovery_present_training_planned

Allowed facts:
- Recovery is logged.
- A workout is planned.
- Workout completion is not logged yet.

Rejected:
> You checked in, and a workout is planned. Use that recovery note to decide how hard to push before you treat the plan as automatic.

Why it fails:
- “before you treat the plan as automatic” is awkward and abstract.
- The sentence over-explains what should be a direct coaching point.

Preferred:
> Plan the intensity of your workout around how recovered you feel today.

## style notes

- Use “today” for user-facing Today copy.
- Do not use “selected date” outside Developer Mode diagnostics.
- Do not use “signal,” “concrete anchor,” “light read,” or “verify the daily picture.”
- Do not use “adding random data.” Prefer “before adding more entries” or “use what is already logged first.”
- Do not force “Because...” as a sentence starter.
- Reduce colon-heavy labels and comma-heavy run-ons.
- Keep the factual boundary, but make the sentence sound like a coach, not a debug trace.
- Runtime feedback captured through the Voice Lab should preserve scenario, candidate, reason-code, and preferred-rewrite context without storing raw logs or private data.
