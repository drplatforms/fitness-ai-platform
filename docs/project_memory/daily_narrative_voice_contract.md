# Daily Narrative Voice Contract

Status: Daily Narrative Feedback-Driven Copy Rule Hardening v1

The Daily Narrative should sound like a practical coach who has seen the facts, not a compliance memo, debug template, or washer hardware manual.

## Target voice

- Human coach, not system report.
- Direct but not bossy.
- Plainspoken but not bland.
- Warm without fake hype.
- Specific to what is present and missing.
- Explains why the next step matters without forcing the word “because.”
- Avoids shame, guilt, medical claims, and motivational-poster language.
- States limits naturally when data is thin.
- Speaks to the user as if the Today card is about today, not “the selected date.”

The note should answer:

1. What is actually going on?
2. Why does it matter?
3. What is the next small action?
4. What should the user not over-read when the entry detail is limited?

## Banned or strongly discouraged defaults

- “useful move”
- “Today’s useful move”
- “builds a clearer picture”
- “clearer picture”
- “without overcomplicating it”
- “keep logging simple”
- “keep your food logs straightforward and basic”
- “start with one entry”
- “selected date” in user-facing copy
- “signal” as default user-facing copy
- “concrete anchor”
- “light read”
- “verify the daily picture”
- “nutrition note”
- “food-context note”
- “adding random data”
- “before you treat the plan as automatic”
- “let how you move decide whether the session stays heavy”
- “does not support expended energy”
- “optimal results” when backend facts do not prove alignment/results
- generic “log one meal or snack” when nutrition is not actually missing or weak

The words “useful” and “simple” are not impossible, but they must not become the house style.

## Rejected examples from user QA

> Keep the nutrition note grounded: Because nutrition shows up, but training does not for the selected date, Treat this as a food-context note, not a full training read.

Why it fails: awkward label, forced “Because,” too many commas, run-on structure, and “selected date” user-facing language.

Preferred direction:

> I see food logged today, but no workout. That means this can be a nutrition-based read, not a full training recommendation.

---

> Add one concrete anchor: Because there is not enough signal for the selected date ending 2026-06-06 to coach from yet. Add the easiest concrete anchor now: a recovery check-in, one meal entry, or the workout you actually completed.

Why it fails: “concrete anchor” is weird, “signal” sounds technical, “selected date ending…” sounds like QA/debug copy, and the label is not user-friendly.

Preferred direction:

> Today's advice is limited. Log a recovery check-in, a meal/snack, or a completed workout so the coach has enough data to provide recommendations.

## Better examples

> Your training session has been logged, but food entries are missing. Add any meals or snacks you've had today so the coach can connect the work you did with how you fueled it.

> Today's logs give the coach enough context to consider training load, food intake, and recovery together. Use that full-day view to decide whether the plan should stay consistent or needs a small adjustment.

> Soreness is up and lower-body work is planned. Keep the first sets conservative, then let how your body reacts decide how the session progresses.

> Food and training are logged, but recovery is the weaker point today. Let readiness guide how aggressively you push the next session.

> There are a handful of entries here, but not enough detail for a strong coaching read. Complete a Recovery Check-in, log a meal/snack, or add the details of today's completed workout so the coach has more to work with.

## Reason-code copy families

- `nutrition_present_training_missing`: food exists, workout is missing; keep the read nutrition-based.
- `training_present_nutrition_missing`: training exists, food is missing; ask for food around the workout.
- `multiple_domains_present_limited_confidence`: keep the next step practical and avoid strong comparison language.
- `rich_day_multiple_domains`: use the full-day view to consider training load, food intake, and recovery without overclaiming alignment or optimal results.
- `high_soreness_lower_body_planned`: keep first sets conservative and let the body response decide progression without diagnosing injury or requiring a deload.
- `mixed_signals_day`: name recovery/readiness as the weaker point only when supported; avoid unsupported physiology claims.
- `actual_sets_missing`: workout exists, set-level detail is missing; ask for workout detail if progression is the question.
- `no_data_today`: say advice is limited and ask for one practical entry.

## Model memory note

Ollama `keep_alive` keeps a model loaded. It does not train the model or make it remember prior app interactions. This document is app-side memory and should be included in provider-facing style guidance where appropriate.
