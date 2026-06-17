import os
import re
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv

from models.coaching_decision_models import CoachingDecision
from models.coordinator_models import UnifiedHealthReport
from services.coaching_decision_service import build_coaching_decision
from services.full_report_section_registry_service import (
    get_full_report_section_registry_metadata,
)
from services.nutrition_target_service import (
    build_nutrition_targets,
    nutrition_targets_to_user_dict,
)
from services.recommendation_engine_service import (
    build_approved_action_plan,
    build_configured_approved_action_plan,
    render_approved_action_plan,
)
from services.report_service import save_health_report
from services.training_report_section_direct_ollama_provider import (
    DirectOllamaGenerateCallable,
)
from services.training_report_section_provider_service import (
    FALLBACK_REASON_FULL_REPORT_PROVIDER_DISABLED,
    FINAL_SECTION_SOURCE_DETERMINISTIC,
    FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
    build_configured_training_report_section_with_metadata,
    build_deterministic_training_report_section_with_metadata,
)
from services.user_state_service import (
    build_user_health_state,
)

load_dotenv()

AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV = (
    "AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED"
)

FALLBACK_REASON_FULL_REPORT_PROVIDER_REQUIRES_BACKGROUND_JOB = (
    "provider_requires_async_report_job"
)


_TRUTHY_ENV_VALUES = {"1", "true", "yes", "on", "enabled"}


@dataclass(frozen=True)
class FullHealthReportGenerationResult:
    report_text: str
    training_report_section_result: object | None = None


@dataclass(frozen=True)
class FullReportCompositionResult:
    report: UnifiedHealthReport
    full_report_composer_source: str
    coordinator_fallback_used: bool
    coordinator_fallback_reason: str | None = None


FULL_REPORT_COMPOSER_SOURCE_CREWAI_STRUCTURED = "crewai_coordinator_structured"
FULL_REPORT_COMPOSER_SOURCE_DETERMINISTIC_INVALID_COORDINATOR_OUTPUT = (
    "deterministic_fallback_after_invalid_coordinator_output"
)
FULL_REPORT_COMPOSER_SOURCE_DETERMINISTIC_COORDINATOR_ERROR = (
    "deterministic_fallback_after_crewai_error"
)

COORDINATOR_FALLBACK_REASON_INVALID_OUTPUT = "invalid_coordinator_output"
COORDINATOR_FALLBACK_REASON_COORDINATOR_ERROR = "crewai_coordinator_error"


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


_DATA_QUALITY_LIMITED_FORBIDDEN_PATTERNS = [
    (
        re.compile(r"\bovertraining\b", re.IGNORECASE),
        "Data-quality-limited reports must not assert overtraining.",
    ),
    (
        re.compile(r"\bstalled\s+(?:weight|fat)\s*[-\s]?loss\b", re.IGNORECASE),
        "Data-quality-limited reports must not assert stalled weight-loss or fat-loss progress.",
    ),
    (
        re.compile(r"\bcompromise\s+recovery\b", re.IGNORECASE),
        "Data-quality-limited reports must not claim recovery is compromised.",
    ),
    (
        re.compile(r"\bcompromise\s+fat[-\s]?loss\s+progress\b", re.IGNORECASE),
        "Data-quality-limited reports must not claim fat-loss progress is compromised.",
    ),
    (
        re.compile(r"\blikely\s+(?:contribute|caused|causing)\b", re.IGNORECASE),
        "Data-quality-limited reports must not use strong likely-causal language.",
    ),
    (
        re.compile(
            r"\b(?:insufficient|inadequate)\s+caloric\s+intake\b", re.IGNORECASE
        ),
        "Data-quality-limited reports must not assert intake adequacy from incomplete data.",
    ),
    (
        re.compile(r"\b(?:severe\s+deficit|caloric\s+deficit)\b", re.IGNORECASE),
        "Data-quality-limited reports must not assert a caloric deficit from incomplete data.",
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

        for pattern, message in _DATA_QUALITY_LIMITED_FORBIDDEN_PATTERNS:
            if pattern.search(report_text):
                violations.append(message)

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


def _format_profile_context(
    health_state,
    coaching_decision: CoachingDecision | None = None,
) -> str:
    latest_weight = _format_weight(getattr(health_state, "latest_body_weight", None))
    starting_weight = _format_weight(getattr(health_state, "starting_weight", None))
    goal_weight = _format_weight(getattr(health_state, "goal_weight", None))
    goal = _format_goal(getattr(health_state, "primary_goal", None))
    activity_level = getattr(health_state, "activity_level", None) or "unspecified"
    weight_phrase = latest_weight or starting_weight

    context_parts = []
    if weight_phrase:
        context_parts.append(f"At roughly {weight_phrase}")
    else:
        context_parts.append("With the available profile data")

    if starting_weight and starting_weight != weight_phrase:
        context_parts.append(f"starting from {starting_weight}")
    if goal_weight:
        context_parts.append(f"goal weight {goal_weight}")

    base_context = (
        f"{context_parts[0]}"
        + (f" ({', '.join(context_parts[1:])})" if len(context_parts) > 1 else "")
        + f", with a {goal} goal and {activity_level} activity level"
    )

    scenario = coaching_decision.scenario if coaching_decision else None

    if scenario == "improving_after_deload":
        focus = (
            "the current focus should be controlled progression rather than "
            "aggressive increases in training stress."
        )
    elif scenario == "aligned_managed":
        focus = (
            "the current focus should be maintaining consistency and progressing "
            "gradually."
        )
    elif scenario == "recovery_limited":
        focus = (
            "the current focus should be recovery support before adding more "
            "training stress."
        )
    elif scenario == "nutrition_training_mismatch":
        focus = (
            "the current focus should be matching nutrition support to training demand."
        )
    elif scenario == "data_quality_limited":
        focus = (
            "the current focus should be improving logging confidence before making "
            "stronger coaching conclusions."
        )
    else:
        focus = "the current focus should be steady progress with recovery awareness."

    return f"{base_context}, {focus}"


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
                "Sleep, soreness, training load, and nutrition indicators do not "
                "show a major recovery bottleneck right now."
            ),
            priority_action=coaching_decision.training_action,
            recommendation=(
                "Continue gradual progression over the next 1-2 weeks. Keep sleep "
                "and nutrition logging consistent, monitor energy, soreness, body "
                "weight trend, and performance, and only increase training volume or "
                "load when those markers stay stable."
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
                "Sleep, soreness, and training effort suggest recovery capacity may "
                f"not yet be matching current training demand. {micronutrient_context}"
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
                f"{nutrition_context} Current training demand needs clearer nutrition "
                f"support before stronger conclusions are useful. {micronutrient_context}"
            ),
            priority_action=coaching_decision.nutrition_action,
            recommendation=(
                "Keep training progression controlled while nutrition support is clarified. "
                "Log complete nutrition entries on training days, review protein and "
                "carbohydrate support against body weight, goal, activity level, and "
                "training load, and monitor performance, soreness, and energy."
            ),
        )

    if coaching_decision.scenario == "improving_after_deload":
        return UnifiedHealthReport(
            overall_score=overall_score,
            biggest_issue=(
                "Recovery is improving, but the main risk is ramping intensity back up "
                "too quickly after the recent deload or reduced-stress period."
            ),
            likely_cause=(
                "Sleep, soreness, and training stress appear to be moving in a better "
                "direction, suggesting the reduced-stress period is helping."
            ),
            priority_action=(
                "Keep most working sets around RIR 2-3 for now and avoid frequent "
                "RIR 0-1 work until recovery stays stable."
            ),
            recommendation=(
                "Continue controlled progression for the next 1-2 weeks. Maintain the "
                "improved sleep pattern, keep nutrition logging consistent on training "
                "days, and monitor energy, soreness, and performance. If those markers "
                "stay stable, gradually increase training volume or load rather than "
                "jumping straight back to high-effort sessions."
            ),
        )

    if coaching_decision.scenario == "data_quality_limited":
        return UnifiedHealthReport(
            overall_score=overall_score,
            biggest_issue=(
                "Data quality limits confidence in nutrition and training conclusions."
            ),
            likely_cause=(
                f"{nutrition_context} {micronutrient_context} Missing fields should "
                "be treated as unknown rather than low or zero intake."
            ),
            priority_action=(
                "Verify food entries and improve logging completeness before making "
                "stronger nutrition or training changes."
            ),
            recommendation=(
                "Keep training manageable while logging quality improves. Continue "
                "tracking sleep, soreness, effort, calories, protein, carbohydrates, "
                "and fats consistently. Once the data is more complete, nutrition and "
                "training targets can be adjusted with more confidence."
            ),
        )

    return UnifiedHealthReport(
        overall_score=overall_score,
        biggest_issue=coaching_decision.primary_focus,
        likely_cause=micronutrient_context,
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


def compose_full_report_from_coordinator_output(
    raw_text: str,
    health_state,
    coaching_decision: CoachingDecision | None = None,
) -> FullReportCompositionResult:
    """Compose from valid coordinator fields or deterministic section-safe fallback.

    The coordinator may help shape final report voice, but it does not own public
    report truth. If the structured coordinator fields are missing or fail
    validation, the full report falls back to deterministic composition while
    preserving already-approved sections such as the training report section.
    """

    if coaching_decision is None:
        coaching_decision = build_coaching_decision(health_state)

    parsed_report = _parse_unified_report(
        raw_text,
        coaching_decision=coaching_decision,
    )
    if parsed_report is not None:
        return FullReportCompositionResult(
            report=parsed_report,
            full_report_composer_source=FULL_REPORT_COMPOSER_SOURCE_CREWAI_STRUCTURED,
            coordinator_fallback_used=False,
        )

    return FullReportCompositionResult(
        report=_build_fallback_unified_report(health_state, coaching_decision),
        full_report_composer_source=(
            FULL_REPORT_COMPOSER_SOURCE_DETERMINISTIC_INVALID_COORDINATOR_OUTPUT
        ),
        coordinator_fallback_used=True,
        coordinator_fallback_reason=COORDINATOR_FALLBACK_REASON_INVALID_OUTPUT,
    )


def build_final_report_from_coordinator_output(
    raw_text: str,
    health_state,
    coaching_decision: CoachingDecision | None = None,
) -> UnifiedHealthReport:
    """Use valid structured coordinator output, otherwise fall back deterministically."""

    return compose_full_report_from_coordinator_output(
        raw_text,
        health_state,
        coaching_decision=coaching_decision,
    ).report


def _format_target_range(minimum, maximum, unit: str) -> str | None:
    if minimum is None or maximum is None:
        return None
    return f"{minimum}-{maximum} {unit}"


def _render_nutrition_target_display(health_state) -> str:
    targets = build_nutrition_targets(health_state)
    display_payload = nutrition_targets_to_user_dict(targets)

    if display_payload["confidence"] == "Limited":
        return (
            "**Nutrition Target Display:** "
            f"{display_payload['nutrition_display_message']}"
        )

    target_lines = []
    if display_payload["allow_calorie_targets"]:
        target_range = _format_target_range(
            display_payload["calorie_target_min"],
            display_payload["calorie_target_max"],
            "calories/day",
        )
        if target_range:
            target_lines.append(f"- Calories: {target_range}")

    if display_payload["allow_protein_targets"]:
        target_range = _format_target_range(
            display_payload["protein_grams_min"],
            display_payload["protein_grams_max"],
            "g/day",
        )
        if target_range:
            target_lines.append(f"- Protein: {target_range}")

    if display_payload["allow_carbohydrate_targets"]:
        target_range = _format_target_range(
            display_payload["carbohydrate_grams_min"],
            display_payload["carbohydrate_grams_max"],
            "g/day",
        )
        if target_range:
            target_lines.append(f"- Carbohydrates: {target_range}")

    if display_payload["allow_fat_targets"]:
        target_range = _format_target_range(
            display_payload["fat_grams_min"],
            display_payload["fat_grams_max"],
            "g/day",
        )
        if target_range:
            target_lines.append(f"- Fat: {target_range}")

    if not target_lines:
        return (
            "**Nutrition Target Display:** "
            f"{display_payload['nutrition_display_message']}"
        )

    return "**Nutrition Target Display:**\n" + "\n".join(target_lines)


def _render_grounded_recommendation_section(
    health_state, approved_action_plan=None
) -> str:
    if approved_action_plan is None:
        approved_action_plan = build_approved_action_plan(health_state)

    return (
        render_approved_action_plan(approved_action_plan)
        + "\n\n"
        + _render_nutrition_target_display(health_state)
    )


def _full_report_training_section_provider_enabled() -> bool:
    return (
        os.getenv(AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED_ENV, "")
        .strip()
        .lower()
        in _TRUTHY_ENV_VALUES
    )


def build_full_report_training_section_result(
    *,
    user_id: int,
    report_date: str,
    approved_context: dict | None = None,
    direct_ollama_generate: DirectOllamaGenerateCallable | None = None,
    allow_training_section_provider: bool = False,
):
    """Build the training section used by full report rendering.

    The full report has its own explicit opt-in gate. When disabled, it returns a
    deterministic training section without attempting direct Ollama even if the
    lower-level training section provider env is set to direct_ollama. When the
    gate is enabled, direct Ollama is still attempted only from an approved
    async/background report job context.
    """

    if not _full_report_training_section_provider_enabled():
        return build_deterministic_training_report_section_with_metadata(
            user_id=user_id,
            report_date=report_date,
            configured_provider="full_report_disabled",
            fallback_used=False,
            fallback_reason=FALLBACK_REASON_FULL_REPORT_PROVIDER_DISABLED,
            final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC,
        )

    if not allow_training_section_provider:
        return build_deterministic_training_report_section_with_metadata(
            user_id=user_id,
            report_date=report_date,
            configured_provider="full_report_requires_background_job",
            fallback_used=True,
            fallback_reason=FALLBACK_REASON_FULL_REPORT_PROVIDER_REQUIRES_BACKGROUND_JOB,
            final_section_source=FINAL_SECTION_SOURCE_DETERMINISTIC_FALLBACK,
        )

    return build_configured_training_report_section_with_metadata(
        user_id=user_id,
        report_date=report_date,
        approved_context=approved_context,
        direct_ollama_generate=direct_ollama_generate,
    )


def _render_training_report_section(training_report_section_result) -> str:
    section = training_report_section_result.approved_section
    observations = "\n".join(
        f"- {observation}" for observation in section.key_observations
    )
    if not observations:
        observations = "- No approved training observations are available."

    return (
        "**Training Report Section:**\n"
        f"**Summary:** {section.section_summary}\n"
        f"**Key Observations:**\n{observations}\n"
        f"**Performance Interpretation:** {section.performance_interpretation}\n"
        f"**Fatigue / Recovery Interpretation:** {section.fatigue_recovery_interpretation}\n"
        f"**Next Training Focus:** {section.suggested_focus}\n"
        f"**Limitations:** {section.limitations_context}"
    )


def render_unified_health_report(
    report: UnifiedHealthReport,
    timestamp: str | None = None,
    health_state=None,
    coaching_decision: CoachingDecision | None = None,
    approved_action_plan=None,
    training_report_section_result=None,
) -> str:
    generated_line = f"Generated: {timestamp}\n\n" if timestamp else ""

    if coaching_decision is None and health_state is not None:
        coaching_decision = build_coaching_decision(health_state)

    profile_context = ""
    grounded_recommendation = ""
    if health_state is not None:
        profile_context = (
            "\n\n**Profile Context:** "
            f"{_format_profile_context(health_state, coaching_decision)}"
        )
        grounded_recommendation = "\n\n" + _render_grounded_recommendation_section(
            health_state,
            approved_action_plan=approved_action_plan,
        )

    training_section = ""
    if training_report_section_result is not None:
        training_section = "\n\n" + _render_training_report_section(
            training_report_section_result
        )

    return (
        f"{generated_line}"
        "**Unified Health Report**\n\n"
        f"**Overall Score:** {report.overall_score}/100"
        f"{profile_context}"
        f"{grounded_recommendation}"
        f"{training_section}\n\n"
        f"**1. Biggest Issue:** {report.biggest_issue}\n\n"
        f"**2. Likely Cause:** {report.likely_cause}\n\n"
        f"**3. Highest Priority Action:** {report.priority_action}\n\n"
        f"**4. Best Recommendation:** {report.recommendation}"
    )


def _report_generation_mode(allow_training_section_provider: bool) -> str:
    return "async_report_job" if allow_training_section_provider else "synchronous"


def _persist_final_health_report(
    *,
    user_id: int,
    report_text: str,
    resolved_report_date: str,
    training_report_section_result,
    report_job_id: str | None,
    allow_training_section_provider: bool,
    provider_enabled: bool,
    model_summary: str = "ollama/qwen3:8b",
    report_status: str = "completed",
    full_report_composer_source: str = FULL_REPORT_COMPOSER_SOURCE_CREWAI_STRUCTURED,
    coordinator_attempted: bool = True,
    coordinator_fallback_used: bool = False,
    coordinator_fallback_reason: str | None = None,
) -> None:
    save_health_report(
        user_id=user_id,
        report_text=report_text,
        model_summary=model_summary,
        report_date=resolved_report_date,
        report_metadata=build_health_report_persistence_metadata(
            training_report_section_result,
            report_job_id=report_job_id,
            report_status=report_status,
            report_generation_mode=_report_generation_mode(
                allow_training_section_provider
            ),
            full_report_composer_source=full_report_composer_source,
            coordinator_attempted=coordinator_attempted,
            coordinator_fallback_used=coordinator_fallback_used,
            coordinator_fallback_reason=coordinator_fallback_reason,
            async_job_used=allow_training_section_provider,
            provider_enabled=provider_enabled,
        ),
    )


def _build_deterministic_fallback_full_report_text(
    *,
    health_state,
    coaching_decision: CoachingDecision,
    approved_action_plan,
    training_report_section_result,
) -> str:
    structured_report = _build_fallback_unified_report(health_state, coaching_decision)
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    return render_unified_health_report(
        report=structured_report,
        timestamp=timestamp,
        health_state=health_state,
        coaching_decision=coaching_decision,
        approved_action_plan=approved_action_plan,
        training_report_section_result=training_report_section_result,
    )


def generate_health_report(
    user_id,
    report_date: str | None = None,
    direct_ollama_generate=None,
    allow_training_section_provider: bool = False,
    return_training_section_result: bool = False,
    report_job_id: str | None = None,
):
    from crewai import LLM, Agent, Crew, Task

    resolved_report_date = report_date or datetime.now().date().isoformat()
    provider_enabled = _full_report_training_section_provider_enabled()
    health_state = build_user_health_state(user_id)
    coaching_decision = build_coaching_decision(health_state)
    approved_action_plan = build_configured_approved_action_plan(health_state)
    training_report_section_result = build_full_report_training_section_result(
        user_id=user_id,
        report_date=resolved_report_date,
        direct_ollama_generate=direct_ollama_generate,
        allow_training_section_provider=allow_training_section_provider,
    )

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
        Reason codes: {", ".join(coaching_decision.reason_codes)}

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
        composition_result = compose_full_report_from_coordinator_output(
            raw_text=result.raw,
            health_state=health_state,
            coaching_decision=coaching_decision,
        )
        final_report = render_unified_health_report(
            report=composition_result.report,
            timestamp=timestamp,
            health_state=health_state,
            coaching_decision=coaching_decision,
            approved_action_plan=approved_action_plan,
            training_report_section_result=training_report_section_result,
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

        _persist_final_health_report(
            user_id=user_id,
            report_text=final_report,
            resolved_report_date=resolved_report_date,
            training_report_section_result=training_report_section_result,
            report_job_id=report_job_id,
            allow_training_section_provider=allow_training_section_provider,
            provider_enabled=provider_enabled,
            full_report_composer_source=composition_result.full_report_composer_source,
            coordinator_attempted=True,
            coordinator_fallback_used=composition_result.coordinator_fallback_used,
            coordinator_fallback_reason=composition_result.coordinator_fallback_reason,
        )

        if return_training_section_result:
            return FullHealthReportGenerationResult(
                report_text=final_report,
                training_report_section_result=training_report_section_result,
            )

        return final_report

    except Exception as e:
        print("\n=== CREWAI ERROR ===\n")
        print(type(e))
        print(e)

        import traceback

        traceback.print_exc()

        fallback_report = _build_deterministic_fallback_full_report_text(
            health_state=health_state,
            coaching_decision=coaching_decision,
            approved_action_plan=approved_action_plan,
            training_report_section_result=training_report_section_result,
        )
        _persist_final_health_report(
            user_id=user_id,
            report_text=fallback_report,
            resolved_report_date=resolved_report_date,
            training_report_section_result=training_report_section_result,
            report_job_id=report_job_id,
            allow_training_section_provider=allow_training_section_provider,
            provider_enabled=provider_enabled,
            model_summary="deterministic_fallback_after_crewai_error",
            report_status="completed_with_full_report_fallback",
            full_report_composer_source=(
                FULL_REPORT_COMPOSER_SOURCE_DETERMINISTIC_COORDINATOR_ERROR
            ),
            coordinator_attempted=True,
            coordinator_fallback_used=True,
            coordinator_fallback_reason=COORDINATOR_FALLBACK_REASON_COORDINATOR_ERROR,
        )

        if return_training_section_result:
            return FullHealthReportGenerationResult(
                report_text=fallback_report,
                training_report_section_result=training_report_section_result,
            )

        return fallback_report


def build_health_report_persistence_metadata(
    training_report_section_result,
    *,
    report_job_id: str | None = None,
    report_status: str = "completed",
    report_generation_mode: str = "synchronous",
    full_report_composer_source: str | None = None,
    coordinator_attempted: bool | None = None,
    coordinator_fallback_used: bool | None = None,
    coordinator_fallback_reason: str | None = None,
    async_job_used: bool = False,
    provider_enabled: bool | None = None,
) -> dict:
    """Return safe metadata intended for persisted report history.

    This mirrors the async job status boundary: summary-level provider/fallback
    facts are allowed, while raw model output, quote context, parser details, and
    validator internals stay out of persisted public report content.
    """

    metadata = training_section_provider_job_metadata(
        training_report_section_result,
        report_job_id=report_job_id,
        provider_enabled=provider_enabled,
    )
    metadata.update(get_full_report_section_registry_metadata())
    metadata.update(
        {
            "report_status": report_status,
            "report_generation_mode": report_generation_mode,
            "full_report_composer_source": full_report_composer_source,
            "coordinator_attempted": coordinator_attempted,
            "coordinator_fallback_used": coordinator_fallback_used,
            "coordinator_fallback_reason": coordinator_fallback_reason,
            "async_job_used": async_job_used,
        }
    )
    return metadata


def training_section_provider_job_metadata(
    training_report_section_result,
    *,
    report_job_id: str | None = None,
    provider_enabled: bool | None = None,
) -> dict:
    """Return safe report-job metadata for training section provider behavior."""

    if training_report_section_result is None:
        return {
            "report_job_id": report_job_id,
            "provider_enabled": provider_enabled,
            "provider_attempted": False,
        }

    metadata = training_report_section_result.runtime_metadata
    approved_section = training_report_section_result.approved_section
    return {
        "report_job_id": report_job_id,
        "user_id": metadata.user_id,
        "report_date": metadata.report_date,
        "provider_enabled": provider_enabled,
        "provider_attempted": metadata.provider_attempted,
        "selected_provider": metadata.selected_provider,
        "selected_model": metadata.selected_model,
        "fallback_used": metadata.fallback_used,
        "fallback_reason": metadata.fallback_reason,
        "training_section_source": approved_section.source,
        "provider_latency_ms": metadata.provider_latency_ms,
        "validation_status": metadata.validation_status,
        "validation_errors_count": len(metadata.validation_errors),
    }


if __name__ == "__main__":
    report = generate_health_report(1)

    print("\n=== FINAL REPORT ===\n")
    print(report)
