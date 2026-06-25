from __future__ import annotations

from dataclasses import asdict, dataclass

from services.daily_narrative_copy_service import (
    awkward_daily_narrative_phrases_found,
    banned_daily_narrative_phrases_found,
)


@dataclass(frozen=True)
class DailyNarrativeVoiceLabScenario:
    scenario_id: str
    scenario_label: str
    situation_summary: str
    domains_present: tuple[str, ...]
    missing_domains: tuple[str, ...]
    data_quality: str
    confidence: str
    reason_codes: tuple[str, ...]
    safe_aggregate_facts: tuple[str, ...]
    next_action_intent: str
    prohibited_claims: tuple[str, ...]
    desired_coaching_angle: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DailyNarrativeVoiceLabCandidate:
    variant_id: str
    title: str
    body: str
    copy_family: str
    reason_codes: tuple[str, ...]
    banned_phrase_hits: tuple[str, ...]
    awkward_phrase_hits: tuple[str, ...]
    quality_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DailyNarrativeVoiceLabResult:
    scenario: DailyNarrativeVoiceLabScenario
    candidates: tuple[DailyNarrativeVoiceLabCandidate, ...]
    provider_allowed: bool = False
    provider_call_required: bool = False
    public_safe: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario.to_dict(),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "provider_allowed": self.provider_allowed,
            "provider_call_required": self.provider_call_required,
            "public_safe": self.public_safe,
        }


def list_daily_narrative_voice_lab_scenarios() -> list[DailyNarrativeVoiceLabScenario]:
    """Return deterministic, public-safe Daily Narrative copy lab fixtures."""

    return list(_SCENARIOS)


def get_daily_narrative_voice_lab_scenario(
    scenario_id: str,
) -> DailyNarrativeVoiceLabScenario:
    for scenario in _SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    valid = ", ".join(sorted(scenario.scenario_id for scenario in _SCENARIOS))
    raise ValueError(
        f"Unknown Daily Narrative Voice Lab scenario: {scenario_id}. Valid: {valid}"
    )


def build_daily_narrative_voice_lab_result(
    scenario_id: str,
) -> DailyNarrativeVoiceLabResult:
    scenario = get_daily_narrative_voice_lab_scenario(scenario_id)
    templates = _CANDIDATE_TEMPLATES[scenario.scenario_id]
    candidates = tuple(
        _build_candidate(
            scenario=scenario,
            variant_id=variant_id,
            title=title,
            body=body,
            copy_family=copy_family,
        )
        for variant_id, title, body, copy_family in templates
    )
    return DailyNarrativeVoiceLabResult(
        scenario=scenario,
        candidates=candidates,
        provider_allowed=False,
        provider_call_required=False,
        public_safe=True,
    )


def build_all_daily_narrative_voice_lab_results() -> list[DailyNarrativeVoiceLabResult]:
    return [
        build_daily_narrative_voice_lab_result(scenario.scenario_id)
        for scenario in _SCENARIOS
    ]


def daily_narrative_voice_lab_quality_hits(text: str) -> dict[str, list[str]]:
    """Return style-quality hits for public-safe copy lab text."""

    return {
        "banned_phrase_hits": banned_daily_narrative_phrases_found(text),
        "awkward_phrase_hits": awkward_daily_narrative_phrases_found(text),
    }


def _build_candidate(
    *,
    scenario: DailyNarrativeVoiceLabScenario,
    variant_id: str,
    title: str,
    body: str,
    copy_family: str,
) -> DailyNarrativeVoiceLabCandidate:
    combined = f"{title} {body}"
    banned_hits = tuple(banned_daily_narrative_phrases_found(combined))
    awkward_hits = tuple(awkward_daily_narrative_phrases_found(combined))
    quality_notes: list[str] = []
    if not banned_hits and not awkward_hits:
        quality_notes.append(
            "No known banned or awkward Daily Narrative phrases found."
        )
    if scenario.confidence.lower() in {"limited", "low"}:
        quality_notes.append(
            "Keep the language practical and avoid strong conclusions."
        )
    if scenario.missing_domains:
        quality_notes.append(
            "Name what is missing without sounding like a debug panel."
        )
    if scenario.scenario_id == "rich_day_multiple_domains":
        quality_notes.append(
            "Use the full-day view before asking for more entries; avoid optimal-results claims."
        )
    if scenario.scenario_id == "high_soreness_lower_body_planned":
        quality_notes.append(
            "Use conservative first-set language and let the body's response decide progression."
        )
    if scenario.scenario_id == "mixed_signals_day":
        quality_notes.append(
            "Name recovery/readiness as the weaker point only when supported; avoid unsupported physiology claims."
        )
    return DailyNarrativeVoiceLabCandidate(
        variant_id=variant_id,
        title=title,
        body=body,
        copy_family=copy_family,
        reason_codes=scenario.reason_codes,
        banned_phrase_hits=banned_hits,
        awkward_phrase_hits=awkward_hits,
        quality_notes=tuple(quality_notes),
    )


_SCENARIOS: tuple[DailyNarrativeVoiceLabScenario, ...] = (
    DailyNarrativeVoiceLabScenario(
        scenario_id="no_data_today",
        scenario_label="No data today",
        situation_summary="No recovery, nutrition, or completed workout information is available yet.",
        domains_present=(),
        missing_domains=("recovery", "nutrition", "training"),
        data_quality="insufficient",
        confidence="Limited",
        reason_codes=(
            "no_data_today",
            "missing_recovery",
            "missing_nutrition",
            "missing_training",
        ),
        safe_aggregate_facts=(
            "No recovery check-in is present.",
            "No food has been logged.",
            "No completed workout is present.",
        ),
        next_action_intent="Ask for one practical entry that makes coaching possible.",
        prohibited_claims=(
            "Do not infer poor adherence.",
            "Do not infer training or nutrition status.",
        ),
        desired_coaching_angle="Today needs a starting point, not a lecture.",
    ),
    DailyNarrativeVoiceLabScenario(
        scenario_id="nutrition_present_training_missing",
        scenario_label="Food logged, workout missing",
        situation_summary="Food is logged, but no workout is logged for today.",
        domains_present=("nutrition",),
        missing_domains=("training", "recovery"),
        data_quality="limited",
        confidence="Low",
        reason_codes=("nutrition_present_training_missing", "training_missing"),
        safe_aggregate_facts=("Food was logged.", "No completed workout is present."),
        next_action_intent="Give a nutrition-based read without calling it a full training recommendation.",
        prohibited_claims=(
            "Do not claim workout effort.",
            "Do not provide training readiness conclusions.",
        ),
        desired_coaching_angle="Keep the read scoped to nutrition because training is absent.",
    ),
    DailyNarrativeVoiceLabScenario(
        scenario_id="training_present_nutrition_missing",
        scenario_label="Workout logged, food missing",
        situation_summary="Training is logged, but food is missing.",
        domains_present=("training",),
        missing_domains=("nutrition", "recovery"),
        data_quality="limited",
        confidence="Low",
        reason_codes=("training_present_nutrition_missing", "nutrition_missing"),
        safe_aggregate_facts=("Training was logged.", "No food has been logged."),
        next_action_intent="Ask for the food context around the workout.",
        prohibited_claims=(
            "Do not claim under-fueling.",
            "Do not invent calories or macros.",
        ),
        desired_coaching_angle="Connect the training day to fueling without generic food logging copy.",
    ),
    DailyNarrativeVoiceLabScenario(
        scenario_id="recovery_present_training_planned",
        scenario_label="Recovery check-in with planned workout",
        situation_summary="Recovery is logged and a workout is planned, but completion is not logged yet.",
        domains_present=("recovery", "planned_training"),
        missing_domains=("completed_training", "nutrition"),
        data_quality="partial",
        confidence="Low",
        reason_codes=("recovery_present_training_planned", "completion_missing"),
        safe_aggregate_facts=(
            "Recovery check-in is present.",
            "A workout is planned.",
            "Workout completion is not logged.",
        ),
        next_action_intent="Frame the workout as readiness-aware without assuming it happened.",
        prohibited_claims=(
            "Do not say the workout was completed.",
            "Do not diagnose recovery problems.",
        ),
        desired_coaching_angle="Use recovery as a check before training, not as a verdict.",
    ),
    DailyNarrativeVoiceLabScenario(
        scenario_id="high_soreness_lower_body_planned",
        scenario_label="High soreness before lower-body plan",
        situation_summary="Recovery check-in suggests high soreness and lower-body training is planned.",
        domains_present=("recovery", "planned_training"),
        missing_domains=("completed_training", "nutrition"),
        data_quality="partial",
        confidence="Low",
        reason_codes=(
            "high_soreness",
            "lower_body_planned",
            "caution_without_diagnosis",
        ),
        safe_aggregate_facts=(
            "Soreness is elevated.",
            "Lower-body training is planned.",
        ),
        next_action_intent="Recommend a cautious training check without medical or fear language.",
        prohibited_claims=("Do not diagnose injury.", "Do not require a deload."),
        desired_coaching_angle="Caution should feel practical, not overprotective.",
    ),
    DailyNarrativeVoiceLabScenario(
        scenario_id="workout_completed_no_sets",
        scenario_label="Workout completed, set detail missing",
        situation_summary="A workout is logged, but set-level detail is missing.",
        domains_present=("training",),
        missing_domains=("actual_sets", "nutrition"),
        data_quality="partial",
        confidence="Low",
        reason_codes=("workout_completed_no_sets", "actual_sets_missing"),
        safe_aggregate_facts=(
            "Workout session exists.",
            "Actual set detail is missing.",
        ),
        next_action_intent="Ask for set detail only if progression is the question.",
        prohibited_claims=(
            "Do not evaluate performance trend.",
            "Do not imply poor logging discipline.",
        ),
        desired_coaching_angle="The missing detail matters only if the user wants progression feedback.",
    ),
    DailyNarrativeVoiceLabScenario(
        scenario_id="rich_day_multiple_domains",
        scenario_label="Rich day with all domains",
        situation_summary="Recovery, nutrition, and training are all present.",
        domains_present=("recovery", "nutrition", "training"),
        missing_domains=(),
        data_quality="rich",
        confidence="Moderate",
        reason_codes=("rich_day_multiple_domains", "consider_domains"),
        safe_aggregate_facts=(
            "Recovery is logged.",
            "Food is logged.",
            "Training is logged.",
        ),
        next_action_intent="Consider the full day before asking for more entries.",
        prohibited_claims=(
            "Do not claim causation.",
            "Do not make a medical or progress verdict.",
        ),
        desired_coaching_angle="Help the user see whether the day hangs together.",
    ),
    DailyNarrativeVoiceLabScenario(
        scenario_id="mixed_signals_day",
        scenario_label="Mixed signals",
        situation_summary="Food and training are present, while recovery looks weaker.",
        domains_present=("nutrition", "training", "recovery"),
        missing_domains=(),
        data_quality="partial",
        confidence="Low",
        reason_codes=("mixed_signals_day", "recovery_weaker_than_training_context"),
        safe_aggregate_facts=(
            "Food is logged.",
            "Training is logged.",
            "Recovery looks less supportive.",
        ),
        next_action_intent="Explain the mismatch without fake certainty.",
        prohibited_claims=(
            "Do not say the user is overtrained.",
            "Do not claim nutrition caused recovery.",
        ),
        desired_coaching_angle="Show the tension between effort and recovery without turning it into a diagnosis.",
    ),
    DailyNarrativeVoiceLabScenario(
        scenario_id="low_data_multiple_domains",
        scenario_label="Low data across several domains",
        situation_summary="A handful of entries exist across domains, but detail is too thin for a strong coaching read.",
        domains_present=("recovery", "nutrition", "training"),
        missing_domains=("detail",),
        data_quality="limited",
        confidence="Limited",
        reason_codes=("low_data_multiple_domains", "limited_confidence"),
        safe_aggregate_facts=(
            "Several domains have partial entries.",
            "Detail is limited.",
        ),
        next_action_intent="List practical completion options without overclaiming.",
        prohibited_claims=(
            "Do not compare everything as if confidence is high.",
            "Do not make progress claims.",
        ),
        desired_coaching_angle="There is something here, but not enough for a strong call.",
    ),
    DailyNarrativeVoiceLabScenario(
        scenario_id="chaotic_logging_week",
        scenario_label="Chaotic logging week",
        situation_summary="Entries are scattered across the week.",
        domains_present=("recovery", "nutrition", "training"),
        missing_domains=("consistency",),
        data_quality="limited",
        confidence="Limited",
        reason_codes=("chaotic_logging_week", "inconsistent_entries"),
        safe_aggregate_facts=(
            "Entries exist across the week.",
            "The pattern is inconsistent.",
        ),
        next_action_intent="Give a practical reset instead of a data lecture.",
        prohibited_claims=("Do not shame the user.", "Do not call adherence poor."),
        desired_coaching_angle="Pick one repeatable logging habit for the next day.",
    ),
    DailyNarrativeVoiceLabScenario(
        scenario_id="consistent_nutrition_no_training",
        scenario_label="Consistent nutrition, no training",
        situation_summary="Nutrition has been logged consistently, but training is absent.",
        domains_present=("nutrition",),
        missing_domains=("training",),
        data_quality="partial",
        confidence="Low",
        reason_codes=("consistent_nutrition_no_training", "training_missing"),
        safe_aggregate_facts=(
            "Nutrition logging is consistent.",
            "No training is logged.",
        ),
        next_action_intent="Acknowledge nutrition consistency while keeping the coaching read scoped.",
        prohibited_claims=(
            "Do not evaluate training progress.",
            "Do not assume rest was planned.",
        ),
        desired_coaching_angle="Give credit for food logging while keeping the read scoped.",
    ),
    DailyNarrativeVoiceLabScenario(
        scenario_id="planned_workout_missed",
        scenario_label="Planned workout not completed",
        situation_summary="A workout was planned, but there is no completion logged.",
        domains_present=("planned_training",),
        missing_domains=("completed_training", "nutrition"),
        data_quality="partial",
        confidence="Low",
        reason_codes=("planned_workout_missed", "reset_without_shame"),
        safe_aggregate_facts=("A workout was planned.", "No completion is logged."),
        next_action_intent="Offer a reset without guilt or failure language.",
        prohibited_claims=(
            "Do not say the user failed.",
            "Do not imply lack of discipline.",
        ),
        desired_coaching_angle="Make it easy to resume or log what actually happened.",
    ),
)

_CANDIDATE_TEMPLATES: dict[str, tuple[tuple[str, str, str, str], ...]] = {
    "no_data_today": (
        (
            "primary",
            "Today's advice is limited",
            "Log a recovery check-in, a meal/snack, or a completed workout so the coach has enough data to provide recommendations.",
            "no_data_start_point",
        ),
        (
            "alternate",
            "Start with one real update",
            "There is nothing reliable to coach from yet today. Add whichever entry is easiest right now: recovery, food, or completed training.",
            "no_data_start_point",
        ),
    ),
    "nutrition_present_training_missing": (
        (
            "primary",
            "Keep this nutrition-based",
            "I see food logged today, but no workout. That means this can be a nutrition-based read, not a full training recommendation.",
            "nutrition_only_read",
        ),
        (
            "alternate",
            "Food is the only solid piece",
            "Food is logged, but training is not. Use this for a nutrition check today and save training guidance until the workout is logged.",
            "nutrition_only_read",
        ),
    ),
    "training_present_nutrition_missing": (
        (
            "primary",
            "Add the food around the workout",
            "Your training session has been logged, but food entries are missing. Add any meals or snacks you've had today so the coach can connect the work you did with how you fueled it.",
            "training_without_fueling",
        ),
        (
            "alternate",
            "Tie fueling to the work",
            "The workout is there, but the food around it is not. Add one honest meal entry so the training read is not floating by itself.",
            "training_without_fueling",
        ),
    ),
    "recovery_present_training_planned": (
        (
            "primary",
            "Use recovery before the workout",
            "You checked in, and a workout is planned. Plan the intensity around how recovered you feel today.",
            "recovery_limited_caution",
        ),
        (
            "alternate",
            "Check readiness first",
            "Recovery is the clearest piece right now. Before training, use it to choose a manageable effort instead of guessing from the plan alone.",
            "recovery_limited_caution",
        ),
    ),
    "high_soreness_lower_body_planned": (
        (
            "primary",
            "Respect the soreness",
            "Soreness is up and lower-body work is planned. Keep the first sets conservative, then let how your body reacts decide how the session progresses.",
            "recovery_limited_caution",
        ),
        (
            "alternate",
            "Start lower, then decide",
            "This is a day to earn the heavier work. Warm up, check how the sore areas feel, and keep effort controlled if movement feels off.",
            "recovery_limited_caution",
        ),
    ),
    "workout_completed_no_sets": (
        (
            "primary",
            "Add set detail if progression matters",
            "The workout is logged, but set details are missing. Add sets, reps, and effort/RIR so the coach can evaluate progression instead of only attendance.",
            "workout_detail_missing",
        ),
        (
            "alternate",
            "The session needs detail",
            "A completed workout tells me you trained. Set detail tells me how hard it was, so add it if you want a better training read.",
            "workout_detail_missing",
        ),
    ),
    "rich_day_multiple_domains": (
        (
            "primary",
            "Use the full-day view",
            "Today's logs give the coach enough context to consider training load, food intake, and recovery together. Use that full-day view to decide whether the plan should stay consistent or needs a small adjustment.",
            "rich_day_interpretation",
        ),
        (
            "alternate",
            "Read what is already there",
            "Training, food, and recovery are all present. Review that full-day view before changing the plan or asking for more entries.",
            "rich_day_interpretation",
        ),
    ),
    "mixed_signals_day": (
        (
            "primary",
            "Separate effort from readiness",
            "Food and training are logged, but recovery is the weaker point today. Let readiness guide how aggressively you push the next session.",
            "mixed_signals",
        ),
        (
            "alternate",
            "Keep recovery in the decision",
            "Training and food are present, but readiness should still set the ceiling. Keep the next session honest until recovery looks more supportive.",
            "mixed_signals",
        ),
    ),
    "low_data_multiple_domains": (
        (
            "primary",
            "Let's get on the same page",
            "There are a handful of entries here, but not enough detail for a strong coaching read. Complete a Recovery Check-in, log a meal/snack, or add the details of today's completed workout so the coach has more to work with.",
            "low_data_practical_next_step",
        ),
        (
            "alternate",
            "Make the next note count",
            "This is not blank, but it is still thin. Add the one update that would change the coaching most: recovery, food, or what actually happened in training.",
            "low_data_practical_next_step",
        ),
    ),
    "chaotic_logging_week": (
        (
            "primary",
            "Pick one repeatable habit",
            "The week has entries, but they are scattered. Do not fix everything today; pick one repeatable check-in that makes tomorrow easier to coach.",
            "low_data_practical_next_step",
        ),
        (
            "alternate",
            "Reset the logging rhythm",
            "There is enough here to see the week was uneven. Choose one small logging habit for the next day so the coach is not piecing the story together afterward.",
            "low_data_practical_next_step",
        ),
    ),
    "consistent_nutrition_no_training": (
        (
            "primary",
            "Nutrition is the reliable part",
            "Food logs are present, which gives the coach nutrition context for today. Add training details when available so the recommendation can account for more than food intake.",
            "nutrition_only_read",
        ),
        (
            "alternate",
            "Food consistency is useful here",
            "Nutrition has a pattern, but training does not. Use the food log as the stable piece and add training only when there is a real session to review.",
            "nutrition_only_read",
        ),
    ),
    "planned_workout_missed": (
        (
            "primary",
            "Reset without making it a big deal",
            "A workout was planned, but completion is not logged. Either log what actually happened or pick the next manageable session and move forward.",
            "reset_after_missed_plan",
        ),
        (
            "alternate",
            "Close the loop",
            "The plan is still open-ended with no completion logged. Mark what happened, even if it was a miss, so the next step starts clean.",
            "reset_after_missed_plan",
        ),
    ),
}
