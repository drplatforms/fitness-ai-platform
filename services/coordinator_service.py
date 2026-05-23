import re
from datetime import datetime

from dotenv import load_dotenv

from models.coaching_decision_models import CoachingDecision
from models.coordinator_models import UnifiedHealthReport
from services.coaching_decision_service import build_coaching_decision
from services.report_service import save_health_report
from services.user_state_service import (
    build_user_health_state,
)

load_dotenv()

_FORBIDDEN_REPORT_PATTERNS = [
    (
        re.compile(
            r"high[-\s]?rir[^\n]*(?:0\s*[-–]\s*1|near[-\s]?failure)",
            re.IGNORECASE,
        ),
        "Do not describe RIR 0-1 or near-failure work as high RIR.",
    ),
    (
        re.compile(r"high[-\s]?rir\s+risks\s+overtraining", re.IGNORECASE),
        "Use low-RIR/high-effort language for near-failure overtraining risk.",
    ),
    (
        re.compile(r"lower\s+rir\s+(?:to|toward)\s+2\s*[-–]\s*3", re.IGNORECASE),
        "Moving from RIR 0-1 to RIR 2-3 means raising RIR, not lowering it.",
    ),
    (
        re.compile(r"\b\d+(?:\.\d+)?\s*/\s*10\b"),
        "Do not describe sleep hours as a score out of 10.",
    ),
    (
        re.compile(
            r"\blikely\s+(?:from|reflect|due to|because of|caused by)[^\n]*(?:supplement|over[-\s]?supplement)",
            re.IGNORECASE,
        ),
        "Do not confidently attribute suspicious micronutrients to supplementation.",
    ),
    (
        re.compile(
            r"reduce\s+(?:your\s+)?(?:supplements|fortified foods)",
            re.IGNORECASE,
        ),
        "Do not recommend reducing supplements or fortified foods unless confirmed.",
    ),
    (
        re.compile(
            r"\b(?:20\s*[-–]\s*40|40\s*[-–]\s*60)\s*g\s*carbs?\b",
            re.IGNORECASE,
        ),
        "Do not give fixed low carbohydrate targets without context.",
    ),
    (
        re.compile(r"\b(?:severe|critical)\s+caloric\s+deficit\b", re.IGNORECASE),
        "Do not assert severe or critical caloric deficit when nutrition logging may be incomplete.",
    ),
    (
        re.compile(r"\binadequate\s+energy\s+availability\b", re.IGNORECASE),
        "Do not assert inadequate energy availability without confirmed calorie context.",
    ),
    (
        re.compile(
            r"\b(?:over[-\s]?supplementation\s+likely|likely\s+over[-\s]?supplementation|supplements?\s+likely)\b",
            re.IGNORECASE,
        ),
        "Do not frame suspicious micronutrients as likely over-supplementation.",
    ),
    (
        re.compile(r"\b\d+\s*[-–]\s*\d+\s*kcal\s*/\s*day\b", re.IGNORECASE),
        "Do not give hard calorie prescriptions without sufficient context.",
    ),
    (
        re.compile(
            r"\b\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?\s*g\s*/\s*kg\b",
            re.IGNORECASE,
        ),
        "Do not give hard macro gram-per-kilogram prescriptions without sufficient context.",
    ),
]


def _validate_report_against_coaching_decision(
    report_text: str,
    coaching_decision: CoachingDecision | None,
) -> list[str]:
    if coaching_decision is None:
        return []

    report_lower = report_text.lower()
    violations = []
    scenario = coaching_decision.scenario

    if scenario == "aligned_managed":
        forbidden_terms = [
            "recovery mismatch",
            "deload",
            "reduce intensity",
            "reduce training stress",
            "insufficient caloric",
            "caloric deficit",
            "inadequate energy availability",
            "outpacing confirmed recovery support",
        ]
        for term in forbidden_terms:
            if term in report_lower:
                violations.append(
                    "Aligned/managed reports should not use unnecessary intervention framing."
                )
                break

    elif scenario == "recovery_limited":
        if "recovery" not in report_lower:
            violations.append(
                "Recovery-limited reports must keep recovery as the focus."
            )
        if "low_rir_high_effort_training" in coaching_decision.reason_codes and (
            "rir 2-3" not in report_lower or "rir 0-1" not in report_lower
        ):
            violations.append(
                "Recovery-limited low-RIR reports must include RIR 2-3 guidance."
            )

    elif scenario == "nutrition_training_mismatch":
        if "nutrition" not in report_lower or "training" not in report_lower:
            violations.append(
                "Nutrition/training mismatch reports must mention nutrition and training demand."
            )
        if "0 kcal" in report_lower or "0 g protein" in report_lower:
            violations.append("Missing nutrition must not be treated as zero intake.")

    elif scenario == "data_quality_limited":
        required_terms = ["logging", "verify"]
        if not all(term in report_lower for term in required_terms):
            violations.append(
                "Data-quality-limited reports must emphasize logging and verification."
            )
        if (
            "supplementation artifacts" in report_lower
            or "likely from supplements" in report_lower
        ):
            violations.append(
                "Data-quality-limited reports must not assume supplement causes."
            )

    elif scenario == "improving_after_deload":
        if "progress" not in report_lower and "progression" not in report_lower:
            violations.append(
                "Improving-after-deload reports should emphasize controlled progression."
            )

    return violations


def validate_report_language(
    report_text: str,
    health_state=None,
    coaching_decision: CoachingDecision | None = None,
) -> list[str]:
    """Return deterministic language-guardrail violations before saving a report."""
    violations = []

    for pattern, message in _FORBIDDEN_REPORT_PATTERNS:
        if pattern.search(report_text):
            violations.append(message)

    violations.extend(
        _validate_report_against_coaching_decision(report_text, coaching_decision)
    )

    if health_state is None:
        return violations

    nutrition_state = health_state.nutrition_state
    nutrition_summary = nutrition_state.nutrition_summary.lower()
    recovery_nutrition_status = nutrition_state.recovery_nutrition_status.lower()

    calories_unknown = nutrition_state.calories == "Unknown"
    incomplete_nutrition = (
        calories_unknown
        or "incomplete" in recovery_nutrition_status
        or "missing" in recovery_nutrition_status
        or "unavailable" in nutrition_summary
        or "unknown" in nutrition_summary
    )

    if not incomplete_nutrition:
        return violations

    incomplete_context_patterns = [
        (
            re.compile(
                r"\b(?:severe|critical)\s+caloric\s+deficit\b",
                re.IGNORECASE,
            ),
            "Incomplete nutrition data cannot support severe or critical caloric deficit language.",
        ),
        (
            re.compile(r"\binadequate\s+energy\s+availability\b", re.IGNORECASE),
            "Incomplete calorie data cannot support inadequate energy availability language.",
        ),
        (
            re.compile(r"\b\d+\s*[-–]\s*\d+\s*kcal\s*/\s*day\b", re.IGNORECASE),
            "Incomplete nutrition data cannot support numeric calorie prescriptions.",
        ),
        (
            re.compile(
                r"\b\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?\s*g\s*/\s*kg\b",
                re.IGNORECASE,
            ),
            "Incomplete nutrition data cannot support numeric gram-per-kilogram macro prescriptions.",
        ),
    ]

    for pattern, message in incomplete_context_patterns:
        if pattern.search(report_text):
            violations.append(message)

    return violations


def _format_sleep(avg_sleep: float | str) -> str:
    if isinstance(avg_sleep, int | float):
        return f"approximately {avg_sleep:g} hours/night"
    return "sleep data unavailable"


def _format_training_effort(avg_rir: float | str) -> str:
    if not isinstance(avg_rir, int | float):
        return "training effort data unavailable"
    if avg_rir <= 1:
        return "low-RIR/high-effort work at RIR 0-1"
    if avg_rir <= 3:
        return f"moderate-effort work around RIR {avg_rir:g}"
    return f"higher-RIR/lower-effort work around RIR {avg_rir:g}"


def _format_weight(value: float | int | str | None) -> str | None:
    if isinstance(value, int | float):
        return f"{value:g} lb"
    return None


def _format_goal(goal: str | None) -> str:
    if not goal:
        return "unspecified goal"

    return goal.replace("_and_", "/").replace("_", " ")


def _format_profile_context(health_state) -> str:
    latest_weight = _format_weight(getattr(health_state, "latest_body_weight", None))
    starting_weight = _format_weight(getattr(health_state, "starting_weight", None))
    goal_weight = _format_weight(getattr(health_state, "goal_weight", None))
    goal = _format_goal(getattr(health_state, "primary_goal", None))
    activity_level = getattr(health_state, "activity_level", None) or "unspecified"

    weight_phrase = latest_weight or starting_weight

    if not weight_phrase:
        return (
            f"With a {goal} goal and {activity_level} activity level, guidance should "
            "use available profile context while avoiding hard numeric prescriptions "
            "until target rules are defined."
        )

    extra_context = []
    if starting_weight and starting_weight != weight_phrase:
        extra_context.append(f"starting weight {starting_weight}")
    if goal_weight:
        extra_context.append(f"goal weight {goal_weight}")

    extra_phrase = ""
    if extra_context:
        extra_phrase = f" ({', '.join(extra_context)})"

    return (
        f"At roughly {weight_phrase}{extra_phrase}, with a {goal} goal and "
        f"{activity_level} activity level, nutrition and training guidance should "
        "use this available context while avoiding hard numeric prescriptions until "
        "target rules are defined."
    )


def _join_items(items: list[str]) -> str:
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    return f"{', '.join(items[:-1])} and {items[-1]}"


def _nutrition_context(health_state) -> str:
    nutrition_state = health_state.nutrition_state
    incomplete_fields = []

    if nutrition_state.calorie_status == "Unknown":
        incomplete_fields.append("calories")
    if nutrition_state.protein_status == "Unknown":
        incomplete_fields.append("protein")
    if nutrition_state.carbohydrate_grams == "Unknown":
        incomplete_fields.append("carbohydrates")
    if nutrition_state.fat_grams == "Unknown":
        incomplete_fields.append("fat")

    if incomplete_fields:
        fields = _join_items(incomplete_fields)
        return f"Nutrition logging is incomplete for {fields}."

    return (
        "Nutrition support should be evaluated against training demand and "
        "recovery status."
    )


def _micronutrient_context(health_state) -> str:
    nutrition_summary = health_state.nutrition_state.nutrition_summary

    if "Unusually high micronutrient values" in nutrition_summary:
        return (
            "Some micronutrient values appear unusually high and may reflect "
            "logging, database, or unit artifacts; verify before acting."
        )

    return "No suspicious micronutrient pattern requires action from this report alone."


def _build_fallback_unified_report(
    health_state,
    coaching_decision: CoachingDecision,
) -> UnifiedHealthReport:
    sleep_phrase = _format_sleep(health_state.recovery_state.avg_sleep)
    effort_phrase = _format_training_effort(health_state.training_state.avg_rir)
    profile_context = _format_profile_context(health_state)
    nutrition_context = _nutrition_context(health_state)
    nutrition_context_lower = nutrition_context.removesuffix(".").lower()
    micronutrient_context = _micronutrient_context(health_state)

    score_by_scenario = {
        "aligned_managed": 85,
        "improving_after_deload": 80,
        "nutrition_training_mismatch": 70,
        "recovery_limited": 55,
        "data_quality_limited": 65,
    }
    overall_score = score_by_scenario.get(coaching_decision.scenario, 70)

    if coaching_decision.scenario == "aligned_managed":
        return UnifiedHealthReport(
            overall_score=overall_score,
            biggest_issue=(
                "Recovery, training, and nutrition appear broadly aligned; the main "
                "priority is maintaining consistency while progressing gradually."
            ),
            likely_cause=(
                f"Recovery, training load, and nutrition appear broadly aligned. "
                f"{profile_context}"
            ),
            priority_action=coaching_decision.training_action,
            recommendation=(
                f"{coaching_decision.primary_focus} {coaching_decision.sleep_action} "
                f"{coaching_decision.nutrition_action} "
                f"{coaching_decision.monitoring_action}"
            ),
        )

    if coaching_decision.scenario == "recovery_limited":
        return UnifiedHealthReport(
            overall_score=overall_score,
            biggest_issue=(
                f"Recovery appears limited by {sleep_phrase}, "
                f"{nutrition_context_lower}, and recent training includes {effort_phrase}."
            ),
            likely_cause=(
                "Training demand may be outpacing confirmed recovery support. "
                f"{profile_context} {micronutrient_context}"
            ),
            priority_action=(
                f"{coaching_decision.sleep_action} {coaching_decision.training_action}"
            ),
            recommendation=(
                f"{coaching_decision.primary_focus} {coaching_decision.nutrition_action} "
                f"{coaching_decision.monitoring_action}"
            ),
        )

    if coaching_decision.scenario == "nutrition_training_mismatch":
        return UnifiedHealthReport(
            overall_score=overall_score,
            biggest_issue=(
                "Nutrition support may not be well matched to current training demand."
            ),
            likely_cause=(
                f"{nutrition_context} {profile_context} {micronutrient_context}"
            ),
            priority_action=coaching_decision.nutrition_action,
            recommendation=(
                f"{coaching_decision.training_action} {coaching_decision.sleep_action} "
                f"{coaching_decision.monitoring_action} Avoid numeric calorie or macro "
                "prescriptions until target rules are explicitly defined."
            ),
        )

    if coaching_decision.scenario == "improving_after_deload":
        return UnifiedHealthReport(
            overall_score=overall_score,
            biggest_issue=(
                "Recovery markers appear improved; the priority is controlled progression "
                "instead of reacting strongly to older high-stress data."
            ),
            likely_cause=(
                "Recent recovery and training patterns suggest the deload or reduced-stress "
                f"period is helping. {profile_context}"
            ),
            priority_action=coaching_decision.training_action,
            recommendation=(
                f"{coaching_decision.primary_focus} {coaching_decision.sleep_action} "
                f"{coaching_decision.nutrition_action} "
                f"{coaching_decision.monitoring_action}"
            ),
        )

    if coaching_decision.scenario == "data_quality_limited":
        return UnifiedHealthReport(
            overall_score=overall_score,
            biggest_issue=(
                "Data quality limits confidence in the current assessment; the priority "
                "is improving logging completeness before making stronger nutrition or "
                "training conclusions."
            ),
            likely_cause=(
                f"{nutrition_context} {profile_context} {micronutrient_context}"
            ),
            priority_action=coaching_decision.nutrition_action,
            recommendation=(
                f"{coaching_decision.training_action} {coaching_decision.sleep_action} "
                f"{coaching_decision.monitoring_action}"
            ),
        )

    return UnifiedHealthReport(
        overall_score=overall_score,
        biggest_issue=coaching_decision.primary_focus,
        likely_cause=f"{profile_context} {micronutrient_context}",
        priority_action=coaching_decision.training_action,
        recommendation=(
            f"{coaching_decision.nutrition_action} {coaching_decision.sleep_action} "
            f"{coaching_decision.monitoring_action}"
        ),
    )


def _extract_structured_field(raw_text: str, field_name: str) -> str | None:
    label = field_name.replace("_", r"[_\s]")
    next_labels = (
        r"overall[_\s]score|biggest[_\s]issue|likely[_\s]cause|"
        r"priority[_\s]action|recommendation"
    )
    pattern = re.compile(
        rf"(?:^|\n)\s*\*{{0,2}}{label}\*{{0,2}}\s*:\s*(.*?)"
        rf"(?=\n\s*\*{{0,2}}(?:{next_labels})\*{{0,2}}\s*:|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(raw_text)
    if not match:
        return None
    return match.group(1).strip()


def _parse_unified_report(
    raw_text: str,
    coaching_decision: CoachingDecision | None = None,
) -> UnifiedHealthReport | None:
    score_text = _extract_structured_field(raw_text, "overall_score")
    biggest_issue = _extract_structured_field(raw_text, "biggest_issue")
    likely_cause = _extract_structured_field(raw_text, "likely_cause")
    priority_action = _extract_structured_field(raw_text, "priority_action")
    recommendation = _extract_structured_field(raw_text, "recommendation")

    if not all(
        [score_text, biggest_issue, likely_cause, priority_action, recommendation]
    ):
        return None

    score_match = re.search(r"\d{1,3}", score_text or "")
    if not score_match:
        return None

    candidate = UnifiedHealthReport(
        overall_score=int(score_match.group()),
        biggest_issue=biggest_issue or "",
        likely_cause=likely_cause or "",
        priority_action=priority_action or "",
        recommendation=recommendation or "",
    )

    rendered_candidate = render_unified_health_report(candidate)
    if validate_report_language(
        rendered_candidate,
        coaching_decision=coaching_decision,
    ):
        return None

    return candidate


def build_final_report_from_coordinator_output(
    raw_text: str,
    health_state,
    coaching_decision: CoachingDecision | None = None,
) -> UnifiedHealthReport:
    """Use valid structured coordinator output, otherwise fall back deterministically."""
    if coaching_decision is None:
        coaching_decision = build_coaching_decision(health_state)

    parsed_report = _parse_unified_report(
        raw_text,
        coaching_decision=coaching_decision,
    )
    if parsed_report is not None:
        return parsed_report

    return _build_fallback_unified_report(health_state, coaching_decision)


def render_unified_health_report(
    report: UnifiedHealthReport,
    timestamp: str | None = None,
    health_state=None,
) -> str:
    generated_line = f"Generated: {timestamp}\n\n" if timestamp else ""

    profile_context = ""
    if health_state is not None:
        profile_context = (
            f"\n\n**Profile Context:** {_format_profile_context(health_state)}"
        )

    return (
        f"{generated_line}"
        "**Unified Health Report**\n\n"
        f"**Overall Score:** {report.overall_score}/100"
        f"{profile_context}\n\n"
        f"**1. Biggest Issue:** {report.biggest_issue}\n\n"
        f"**2. Likely Cause:** {report.likely_cause}\n\n"
        f"**3. Highest Priority Action:** {report.priority_action}\n\n"
        f"**4. Best Recommendation:** {report.recommendation}"
    )


def generate_health_report(user_id):
    from crewai import LLM, Agent, Crew, Task

    health_state = build_user_health_state(user_id)
    coaching_decision = build_coaching_decision(health_state)

    # -----------------------------
    # Nutrition Summary
    # -----------------------------

    nutrition_summary = health_state.nutrition_state.nutrition_summary

    # -----------------------------
    # Workout Summary
    # -----------------------------

    workout_summary = health_state.training_state.workout_summary

    # -----------------------------
    # Local LLMs
    # -----------------------------

    fast_llm = LLM(
        model="ollama/qwen3:8b",
        base_url="http://localhost:11434",
    )

    smart_llm = LLM(
        model="ollama/qwen3:8b",
        base_url="http://localhost:11434",
    )

    # -----------------------------
    # Recovery Agent
    # -----------------------------

    recovery_agent = Agent(
        role="Recovery Coach",
        goal="Analyze recovery trends and training readiness.",
        backstory="""
        You specialize in recovery management,
        fatigue analysis,
        and training readiness.
        """,
        llm=fast_llm,
        verbose=False,
    )

    recovery_task = Task(
        description=f"""
        Analyze the following user profile and recovery data.

        User Profile:
        Name: {health_state.user_name}
        Goal: {health_state.primary_goal}

        Recovery Metrics:
        Average sleep hours/night: {health_state.recovery_state.avg_sleep}
        Average energy: {health_state.recovery_state.avg_energy}
        Average soreness: {health_state.recovery_state.avg_soreness}
        Weight change: {health_state.recovery_state.weight_change}

        Recovery Interpretation:
        Recovery score: {health_state.recovery_state.recovery_score}
        Fatigue risk: {health_state.recovery_state.fatigue_risk}
        Readiness level: {health_state.recovery_state.readiness_level}
        Sleep trend: {health_state.recovery_state.sleep_trend}
        Weight trend: {health_state.recovery_state.weight_trend}

        Provide:
        1. Recovery assessment
        2. Training readiness
        3. Recovery recommendations
        """,
        expected_output="Concise recovery analysis.",
        agent=recovery_agent,
    )

    # -----------------------------
    # Nutrition Agent
    # -----------------------------

    nutrition_agent = Agent(
        role="Nutrition Coach",
        goal="Analyze nutrition intake and recovery support.",
        backstory="""
        You specialize in performance nutrition,
        body composition,
        and recovery nutrition.
        """,
        llm=fast_llm,
        verbose=False,
    )

    nutrition_task = Task(
        description=f"""
        Analyze macro and micronutrient intake,
        recovery support,
        overall nutrition quality,
        and performance implications.

        Nutrition Data:
        {nutrition_summary}

        Nutrition Interpretation:
        Calories: {health_state.nutrition_state.calories}
        Protein: {health_state.nutrition_state.protein_grams} g
        Carbohydrates: {health_state.nutrition_state.carbohydrate_grams} g
        Fat: {health_state.nutrition_state.fat_grams} g
        Protein status: {health_state.nutrition_state.protein_status}
        Calorie status: {health_state.nutrition_state.calorie_status}
        Recovery nutrition status: {health_state.nutrition_state.recovery_nutrition_status}

        Guardrails:
        - Treat missing nutrition fields as unknown, not zero intake.
        - Do not say the user consumed 0 kcal unless Calories is explicitly logged as 0.
        - If Calories is Unknown, say calorie intake is unavailable or incomplete.
        - Do not infer supplementation, over-supplementation, or true excess micronutrient intake from suspicious values without confirmation.
        - Avoid absolute protein gram targets unless current body weight is available. Use qualitative protein guidance instead.
        - Do not give fixed calorie, carbohydrate, sodium, calcium, potassium, magnesium, or zinc targets without required context.

        Provide:
        1. Nutrition assessment
        2. Recovery implications
        3. Nutrition recommendations
        """,
        expected_output="Concise nutrition analysis.",
        agent=nutrition_agent,
    )

    # -----------------------------
    # Workout Agent
    # -----------------------------

    workout_agent = Agent(
        role="Strength Coach",
        goal="Analyze workout quality and training balance.",
        backstory="""
        You specialize in resistance training,
        recovery management,
        and performance progression.
        """,
        llm=fast_llm,
        verbose=False,
    )

    workout_task = Task(
        description=f"""
        Analyze the following workout history.

        Training Adherence:
        Workout count: {health_state.training_state.workout_count}

        Adherence level: {health_state.training_state.adherence_level}

        Training trend: {health_state.training_state.training_trend}
        Estimated volume load: {health_state.training_state.total_volume_load}
        Average RIR: {health_state.training_state.avg_rir}
        Training load: {health_state.training_state.training_load}
        Recovery demand: {health_state.training_state.recovery_demand}

        RIR guardrail:
        - RIR means reps in reserve.
        - RIR 0-1 means low RIR, high effort, close to failure.
        - RIR 2-3 means moderate effort with more reps left in reserve than RIR 0-1.
        - RIR 4+ means high RIR, lower effort, farther from failure.
        - Never describe RIR 0-1 as high RIR.
        - Never say "lower RIR to 2-3" when current RIR is 0-1.
        - Moving from RIR 0-1 to RIR 2-3 means raising RIR, reducing effort, and leaving more reps in reserve.

        Workout Data:
        {workout_summary}

        Provide:
        1. Workout quality assessment
        2. Recovery implications
        3. Training recommendations
        """,
        expected_output="Concise workout analysis.",
        agent=workout_agent,
    )

    # -----------------------------
    # Coordinator Agent
    # -----------------------------

    coordinator_agent = Agent(
        role="Health Performance Coordinator",
        goal="""
        Combine recovery, nutrition, and workout insights
        into unified coaching recommendations.
        """,
        backstory="""
        You synthesize recovery, nutrition, and workout analyses
        into practical, actionable health guidance.
        """,
        llm=smart_llm,
        verbose=False,
    )

    coordinator_task = Task(
        description=f"""
        Combine the recovery, nutrition, and workout analyses
        into a unified health recommendation.

        System Stress Interpretation:
        System stress level: {health_state.system_stress_level}
        Nutrition/training alignment: {health_state.nutrition_training_alignment}
        Coordinator focus: {health_state.coordinator_focus}

        Approved Coaching Decision Contract:
        Scenario: {coaching_decision.scenario}
        Primary focus: {coaching_decision.primary_focus}
        Training action: {coaching_decision.training_action}
        Nutrition action: {coaching_decision.nutrition_action}
        Sleep action: {coaching_decision.sleep_action}
        Monitoring action: {coaching_decision.monitoring_action}
        Confidence: {coaching_decision.confidence}
        Reason codes: {', '.join(coaching_decision.reason_codes)}

        Follow the Approved Coaching Decision Contract. Do not change the scenario,
        primary focus, or safety posture. Explain it naturally and concisely.

        User Profile Context:
        Age: {getattr(health_state, "age", None)}
        Height cm: {getattr(health_state, "height_cm", None)}
        Starting weight: {getattr(health_state, "starting_weight", None)}
        Latest body weight: {getattr(health_state, "latest_body_weight", "Unknown")}
        Goal weight: {getattr(health_state, "goal_weight", None)}
        Primary goal: {health_state.primary_goal}
        Activity level: {getattr(health_state, "activity_level", None)}

        Use available profile context directly when helpful.
        Example wording:
        "At roughly 190 lb with a strength/recomposition goal..."
        Do not use profile context to invent hard calorie or macro prescriptions.

        Critical final report guardrails:
        - Missing nutrition fields are unknown, not zero intake.
        - Do not say 0 kcal, 0 g protein, 0 g carbs, or 0 g fat unless those values were explicitly logged as 0.
        - If nutrition data is incomplete, describe it as incomplete rather than as severe restriction.
        - Average sleep is measured in hours/night, not on a 10-point scale.
        - If average sleep is 5.3, say approximately 5.3 hours/night. Do not say 5.3/10.
        - RIR means reps in reserve.
        - RIR 0-1 means low RIR / high effort / close to failure.
        - RIR 2-3 means more reps left in reserve than RIR 0-1.
        - Moving from RIR 0-1 to RIR 2-3 means raising RIR, reducing effort, and leaving more reps in reserve.
        - Never describe RIR 0-1 as high RIR.
        - Never say "lower RIR to 2-3" when current RIR is 0-1.
        - Treat suspicious micronutrient values cautiously.
        - Do not assume supplementation, over-supplementation, or true intake without confirmation.
        - Do not recommend reducing supplements or fortified foods unless supplementation or fortified-food intake is confirmed.
        - Avoid fixed carbohydrate targets such as 20-40g or 40-60g unless supported by body weight, training volume, and user goal context.
        - For carbohydrate guidance, use contextual wording based on training load, recovery status, body weight, and goals.
        - Avoid absolute protein targets unless current body weight is available.

        Forbidden final report wording:
        - Any phrase that combines "high RIR" or "high-RIR" with "0", "1", or "0-1"
        - "high-RIR lifts (0-1)"
        - "high-RIR session" when referring to RIR 0-1
        - "high RIR (near-failure efforts)"
        - "high RIR risks overtraining"
        - "Replace high-RIR (0-1)"
        - "sleep deprivation (5.3/10)"
        - "likely from supplements"
        - "reduce supplements" unless supplement use is confirmed
        - "20-40g carbs" or "40-60g carbs" as a fixed recommendation without context

        RIR wording requirements:
        - For RIR 0-1, the ONLY acceptable labels are:
          "low RIR", "high effort", "near failure", "close to failure", or "low-RIR/high-effort work".
        - Never pair the phrase "high RIR" with values 0, 1, or 0-1.
        - The phrase "high RIR" may only be used for RIR 4+.
        - If discussing RIR 0-1, always say "low RIR" instead of "high RIR".
        - If recommending RIR 2-3 from current RIR 0-1, say "raise RIR to 2-3" or "move toward RIR 2-3", never "lower RIR."

        Micronutrient wording requirements:
        - Do not use "likely" when explaining suspicious micronutrient values.
        - Use "may reflect" instead.
        - Do not recommend reducing supplements, fortified foods, sodium, calcium, potassium, magnesium, or zinc unless the source is confirmed.
        - Recommend verification first.

        Macro recommendation requirements:
        - Do not give fixed calorie, protein, carbohydrate, sodium, calcium, potassium, magnesium, or zinc targets unless required context is available.
        - Prefer qualitative guidance: "evaluate relative to body weight, training load, recovery status, goals, and logged intake completeness."

        Required replacement language:
        - Say "low-RIR/high-effort work at RIR 0-1."
        - Say "for 1-2 weeks, keep most working sets around RIR 2-3 instead of RIR 0-1."
        - Say "approximately 5.3 hours/night," not "5.3/10."
        - Say "some micronutrient values appear unusually high and may reflect logging, database, or unit artifacts; verify before acting."
        - For carbohydrates, say "carbohydrate intake should be evaluated relative to training load, recovery, body weight, and goals" instead of giving fixed low gram targets.

        Output exactly these structured fields and no extra sections:
        overall_score: integer from 0 to 100
        biggest_issue: one concise sentence
        likely_cause: one concise sentence
        priority_action: one concise sentence
        recommendation: one concise paragraph
        """,
        expected_output="Structured UnifiedHealthReport fields only.",
        agent=coordinator_agent,
        context=[
            recovery_task,
            nutrition_task,
            workout_task,
        ],
    )

    # -----------------------------
    # Build Crew
    # -----------------------------

    crew = Crew(
        agents=[
            recovery_agent,
            nutrition_agent,
            workout_agent,
            coordinator_agent,
        ],
        tasks=[
            recovery_task,
            nutrition_task,
            workout_task,
            coordinator_task,
        ],
        verbose=False,
    )

    # -----------------------------
    # Execute Crew
    # -----------------------------

    print("Recovery agent ready.")
    print("Nutrition agent ready.")
    print("Workout agent ready.")
    print("Coordinator agent ready.")
    print("Starting coordinator crew...")

    try:
        print("\nCalling crew.kickoff()...\n")
        print("DEBUG MARKER")

        result = crew.kickoff()

        print("\ncrew.kickoff() completed.\n")

        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        structured_report = build_final_report_from_coordinator_output(
            raw_text=result.raw,
            health_state=health_state,
            coaching_decision=coaching_decision,
        )
        final_report = render_unified_health_report(
            report=structured_report,
            timestamp=timestamp,
            health_state=health_state,
        )

        language_violations = validate_report_language(
            final_report,
            health_state=health_state,
            coaching_decision=coaching_decision,
        )
        if language_violations:
            raise ValueError(
                "Final report failed language validation: "
                + "; ".join(language_violations)
            )

        save_health_report(
            user_id=user_id,
            report_text=final_report,
            model_summary="ollama/qwen3:8b",
        )

        return final_report

    except Exception as e:
        print("\n=== CREWAI ERROR ===\n")
        print(type(e))
        print(e)

        import traceback

        traceback.print_exc()

        return str(e)


if __name__ == "__main__":
    report = generate_health_report(1)

    print("\n=== FINAL REPORT ===\n")
    print(report)
