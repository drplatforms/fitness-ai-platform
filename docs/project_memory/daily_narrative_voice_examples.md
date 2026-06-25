# Daily Narrative Voice Examples

Status: Daily Narrative Feedback-Driven Copy Rule Hardening v1

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
> Today's logs give the coach enough context to compare training load, food intake, and recovery. Use that full-day view to decide whether the plan should stay consistent or needs a small adjustment.

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
> You checked in, and a workout is planned. Plan the intensity of your workout around how recovered you feel today.

## high_soreness_lower_body_planned

Allowed facts:
- Soreness is elevated.
- Lower-body training is planned.
- The app should not diagnose injury or require a deload.

Rejected:
> Soreness is up and lower-body work is planned. Keep the first sets conservative and let how you move decide whether the session stays heavy.

Why it fails:
- “let how you move decide” is close but not natural enough.
- “session stays heavy” over-focuses on load and sounds like a template.
- The idea is right, but the coach should phrase it as body response guiding progression.

Preferred:
> Soreness is up and lower-body work is planned. Keep the first sets conservative, then let how your body reacts decide how the session progresses.

## rich_day_multiple_domains

Allowed facts:
- Recovery, food, and training are present.
- There is enough context to compare the day cautiously.
- Backend facts may not prove true alignment or optimal outcomes.

Rejected direction:
> Today, your adherence to logging provides the coach with a clear picture. Training intensity, food intake, and recovery align with keeping your plan consistent for optimal results.

Why it needs tightening:
- “optimal results” is too strong unless backend facts prove it.
- “align” may overclaim true agreement across domains.
- The useful point is full-day context, not guaranteed progress.

Preferred:
> Today's logs give the coach enough context to compare training load, food intake, and recovery. Use that full-day view to decide whether the plan should stay consistent or needs a small adjustment.

## mixed_signals_day

Allowed facts:
- Food is logged.
- Training is logged.
- Recovery looks less supportive.

Rejected direction:
> Food and training are logged, but recovery does not support expended energy. Consider your readiness score before tomorrow's training session.

Why it needs tightening:
- “does not support expended energy” sounds like unsupported physiology.
- “tomorrow's training session” should appear only when tomorrow/planned workout context exists.
- The useful point is readiness limiting the next push.

Preferred:
> Food and training are logged, but recovery is the limiting factor today. Use readiness as the check before pushing the next session.

## style notes

- Use “today” for user-facing Today copy.
- Do not use “selected date” outside Developer Mode diagnostics.
- Do not use “signal,” “concrete anchor,” “light read,” or “verify the daily picture.”
- Do not use “adding random data.” Prefer “before adding more entries,” “use what is already logged first,” or “use the full-day view.”
- Do not use “before you treat the plan as automatic.” Prefer recovery-based intensity planning.
- Do not use “let how you move decide whether the session stays heavy.” Prefer body-reaction / session-progression language.
- Do not use “does not support expended energy.” Prefer readiness/recovery-limiting-factor language when supported.
- Do not use “optimal results” unless backend facts can prove the claim.
- Do not force “Because...” as a sentence starter.
- Reduce colon-heavy labels and comma-heavy run-ons.
- Keep the factual boundary, but make the sentence sound like a coach, not a debug trace.
- Runtime feedback captured through the Voice Lab should preserve scenario, candidate, reason-code, and preferred-rewrite context without storing raw logs or private data.
