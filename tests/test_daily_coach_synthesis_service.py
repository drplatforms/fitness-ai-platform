from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import database
from api.main import app
from models.coaching_decision_models import CoachingDecision
from models.daily_coach_synthesis_models import DailyCoachSynthesis
from models.nutrition_food_suggestion_models import (
    ApprovedFoodSuggestion,
    ApprovedNutritionFoodSuggestions,
    NutritionMacroGap,
)
from models.nutrition_target_models import NutritionTargets
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    TARGET_STATUS_BELOW,
    TARGET_STATUS_NEAR,
    TARGET_STATUS_UNAVAILABLE,
    ApprovedNutritionGuidance,
    NutritionActuals,
    NutritionLoggingSummary,
    NutritionTargetComparison,
    TargetVsActualNutritionSummary,
)
from models.recommendation_models import ApprovedActionPlan, RecommendationContext
from models.training_constraint_models import TrainingConstraints
from models.training_execution_summary_models import TrainingExecutionSummary
from models.user_state_models import (
    UserHealthState,
    UserNutritionState,
    UserRecoveryState,
    UserTrainingState,
)
from models.workout_plan_models import (
    ApprovedWorkoutExercise,
    ApprovedWorkoutExplanation,
    ApprovedWorkoutPlan,
)
from scripts.seed_qa_scenarios import QA_USER_IDS, seed_qa_scenarios
from services.daily_coach_synthesis_service import (
    build_daily_coach_synthesis,
    build_daily_coach_synthesis_from_components,
    validate_daily_coach_synthesis,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()


def _no_recovery_health_state() -> UserHealthState:
    return UserHealthState(
        user_id=999,
        user_name="No Recovery User",
        primary_goal="strength_and_recomposition",
        recovery_state=UserRecoveryState(
            avg_sleep="Unknown",
            avg_energy="Unknown",
            avg_soreness="Unknown",
            weight_change="Unknown",
            recovery_score=0,
            fatigue_risk="Unknown",
            readiness_level="Unknown",
            sleep_trend="Unknown",
            weight_trend="Unknown",
        ),
        nutrition_state=UserNutritionState(
            nutrition_summary="Nutrition logging is available but limited.",
            has_nutrition_data=False,
            calories="Unknown",
            protein_grams="Unknown",
            carbohydrate_grams="Unknown",
            fat_grams="Unknown",
            protein_status="Unknown",
            calorie_status="Unknown",
            recovery_nutrition_status="Unknown",
        ),
        training_state=UserTrainingState(
            workout_summary="No planned workout execution history yet.",
            has_workout_data=False,
            workout_count=0,
            adherence_level="Unknown",
            training_trend="Unknown",
            total_volume_load=0,
            avg_rir="Unknown",
            training_load="Unknown",
            recovery_demand="Unknown",
        ),
        system_stress_level="Unknown",
        nutrition_training_alignment="Unknown",
        coordinator_focus="data_quality_limited",
        activity_level="moderate",
    )


def _summary(
    *,
    completed_execution_count: int = 0,
    confidence: str = "Limited",
    execution_quality: str = "no_planned_execution_data",
    execution_effort_trend: str = "no_planned_execution_data",
    execution_completion_trend: str = "no_planned_execution_data",
    incomplete_logging_count: int = 0,
    skipped_exercise_count: int = 0,
    substituted_exercise_count: int = 0,
    average_rir_deviation: float | None = None,
) -> TrainingExecutionSummary:
    return TrainingExecutionSummary(
        user_id=999,
        completed_execution_count=completed_execution_count,
        recent_plan_instance_ids=list(range(1, completed_execution_count + 1)),
        average_completion_percentage=95 if completed_execution_count else None,
        average_planned_rir=3 if completed_execution_count else None,
        average_actual_rir=(
            3 + average_rir_deviation
            if completed_execution_count and average_rir_deviation is not None
            else (3 if completed_execution_count else None)
        ),
        average_rir_deviation=average_rir_deviation,
        skipped_exercise_count=skipped_exercise_count,
        substituted_exercise_count=substituted_exercise_count,
        sets_below_planned_reps=0,
        sets_inside_planned_reps=8 if completed_execution_count else 0,
        sets_above_planned_reps=0,
        incomplete_logging_count=incomplete_logging_count,
        missing_actual_rir_count=incomplete_logging_count,
        missing_actual_reps_count=0,
        execution_quality=execution_quality,
        execution_effort_trend=execution_effort_trend,
        execution_completion_trend=execution_completion_trend,
        confidence=confidence,
        reason_codes=[execution_quality, execution_effort_trend, confidence.lower()],
    )


def _fake_recommendation_context(
    health_state: UserHealthState,
    summary: TrainingExecutionSummary,
    *,
    scenario: str | None = None,
    confidence: str = "Moderate",
) -> RecommendationContext:
    scenario = scenario or (
        "data_quality_limited" if health_state.user_id == 999 else "aligned_managed"
    )
    nutrition_targets = NutritionTargets(
        body_weight_lb=190,
        calorie_target_min=None,
        calorie_target_max=None,
        protein_grams_min=140,
        protein_grams_max=180,
        carbohydrate_grams_min=None,
        carbohydrate_grams_max=None,
        fat_grams_min=None,
        fat_grams_max=None,
        confidence="Limited" if scenario == "data_quality_limited" else "Moderate",
        allow_calorie_targets=False,
        allow_protein_targets=True,
        allow_carbohydrate_targets=False,
        allow_fat_targets=False,
        nutrition_display_message="Nutrition targets are limited until logging improves.",
        reason_codes=["unit_test_nutrition_targets"],
    )
    training_constraints = TrainingConstraints(
        recommended_rir_min=2,
        recommended_rir_max=4,
        low_rir_guidance="Keep working sets controlled around RIR 2-4.",
        progression_guidance="Progress only when recovery and performance stay stable.",
        recovery_constraint="normal",
        confidence=confidence,
        reason_codes=["unit_test_training_constraints"],
    )
    coaching_decision = CoachingDecision(
        scenario=scenario,
        primary_focus="Keep today's plan controlled and well logged.",
        training_action="Use the approved workout plan without changing it.",
        nutrition_action="Keep nutrition logging complete before stronger conclusions.",
        sleep_action="Complete the recovery check-in when possible.",
        monitoring_action="Track reps, weight, and RIR.",
        confidence=confidence,
        reason_codes=[f"scenario_{scenario}"],
    )
    return RecommendationContext(
        user_id=health_state.user_id,
        scenario=scenario,
        primary_goal=health_state.primary_goal,
        body_weight_lb=190,
        nutrition_targets=nutrition_targets,
        training_constraints=training_constraints,
        coaching_decision=coaching_decision,
        training_execution_summary=summary,
        allowed_actions=[
            coaching_decision.training_action,
            coaching_decision.nutrition_action,
            coaching_decision.sleep_action,
        ],
        forbidden_claims=["No progression, deload, or discipline claims."],
        confidence=confidence,
        reason_codes=["unit_test_recommendation_context"],
    )


def _fake_action_plan(
    context: RecommendationContext, *, confidence: str | None = None
) -> ApprovedActionPlan:
    return ApprovedActionPlan(
        daily_coaching_recommendation="Use today's approved plan and keep the session well logged.",
        workout_recommendation="Keep the workout controlled and stay within the approved RIR range.",
        nutrition_action="Keep nutrition logging complete before drawing stronger conclusions.",
        rationale="This keeps today's coaching grounded in approved context.",
        confidence=confidence or context.confidence,
        scenario=context.scenario,
        reason_codes=["unit_test_action_plan"],
    )


def _fake_workout_plan(context: RecommendationContext) -> ApprovedWorkoutPlan:
    return ApprovedWorkoutPlan(
        title="Controlled Strength Session",
        session_focus="Practice quality reps within the approved target range.",
        duration_minutes=45,
        exercises=[
            ApprovedWorkoutExercise(
                name="Goblet Squat",
                sets=3,
                reps_min=8,
                reps_max=10,
                rir_min=2,
                rir_max=4,
                notes="Keep reps controlled.",
                equipment_required=["dumbbell"],
            ),
            ApprovedWorkoutExercise(
                name="Push-Up",
                sets=3,
                reps_min=8,
                reps_max=12,
                rir_min=2,
                rir_max=4,
                notes="Stop with clean reps in reserve.",
                equipment_required=["bodyweight"],
            ),
        ],
        warmup="Use easy movement and ramp-up sets.",
        cooldown="Log effort and recovery after the session.",
        progression_guidance="Progress only when recovery and performance stay stable.",
        rationale="This workout fits today's approved training context.",
        confidence=context.confidence,
        scenario=context.scenario,
        reason_codes=["unit_test_workout_plan"],
    )


def _fake_workout_explanation(plan: ApprovedWorkoutPlan) -> ApprovedWorkoutExplanation:
    return ApprovedWorkoutExplanation(
        session_summary="This is a controlled strength session based on the approved plan.",
        why_this_fits_today="It matches the current training and recovery context.",
        focus_cue="Focus on clean execution and honest effort logging.",
        recovery_context="The session is designed to stay manageable.",
        nutrition_or_logging_context="Complete logging will make the next review more useful.",
        confidence=plan.confidence,
    )


def _build_components(
    health_state: UserHealthState | None = None,
    summary: TrainingExecutionSummary | None = None,
    *,
    scenario: str | None = None,
    confidence: str = "Moderate",
):
    health_state = health_state or _no_recovery_health_state()
    summary = summary or _summary(completed_execution_count=0)
    recommendation_context = _fake_recommendation_context(
        health_state,
        summary,
        scenario=scenario,
        confidence=confidence,
    )
    approved_action_plan = _fake_action_plan(recommendation_context)
    approved_workout_plan = _fake_workout_plan(recommendation_context)
    approved_workout_explanation = _fake_workout_explanation(approved_workout_plan)
    return {
        "health_state": health_state,
        "recommendation_context": recommendation_context,
        "approved_action_plan": approved_action_plan,
        "approved_workout_plan": approved_workout_plan,
        "approved_workout_explanation": approved_workout_explanation,
        "training_execution_summary": recommendation_context.training_execution_summary,
    }


def _comparison(
    nutrient: str,
    *,
    status: str = TARGET_STATUS_UNAVAILABLE,
    available: bool = False,
    actual: float | None = None,
    reason_codes: list[str] | None = None,
) -> NutritionTargetComparison:
    return NutritionTargetComparison(
        nutrient=nutrient,
        actual=actual,
        target_min=100 if available else None,
        target_max=150 if available else None,
        delta_min=-20 if available else None,
        delta_max=-70 if available else None,
        percent_of_target=80 if available else None,
        target_status=status,
        comparison_available=available,
        confidence="Moderate" if available else "Limited",
        reason_codes=reason_codes or [],
        limitations=[] if available else [f"{nutrient} comparison is unavailable."],
    )


def _nutrition_summary_and_guidance(
    *,
    completeness: str = LOGGING_COMPLETENESS_NO_LOGS,
    confidence: str = "Limited",
    protein_status: str = TARGET_STATUS_UNAVAILABLE,
    protein_available: bool = False,
    calories_available: bool = False,
    macros_available: bool = False,
) -> tuple[TargetVsActualNutritionSummary, ApprovedNutritionGuidance]:
    actuals = NutritionActuals(
        user_id=999,
        logging_date="2026-06-05",
        logging_window="calendar_day",
        logged_calories=1800 if calories_available else None,
        logged_protein=90 if protein_available else None,
        logged_carbs=200 if macros_available else None,
        logged_fat=65 if macros_available else None,
        logged_meal_count=0 if completeness == LOGGING_COMPLETENESS_NO_LOGS else 2,
        entry_count=0 if completeness == LOGGING_COMPLETENESS_NO_LOGS else 2,
        source_count=0 if completeness == LOGGING_COMPLETENESS_NO_LOGS else 2,
        reason_codes=[],
    )
    logging_summary = NutritionLoggingSummary(
        user_id=999,
        logging_date="2026-06-05",
        logging_completeness=completeness,
        confidence=confidence,
        logged_meal_count=actuals.logged_meal_count,
        entry_count=actuals.entry_count,
        missing_nutrient_fields=(
            [] if macros_available else ["calories", "carbohydrates", "fat"]
        ),
        reason_codes=[],
        limitations=[],
    )
    comparisons = {
        "calories": _comparison(
            "calories",
            status=(
                TARGET_STATUS_NEAR if calories_available else TARGET_STATUS_UNAVAILABLE
            ),
            available=calories_available,
            actual=1800 if calories_available else None,
            reason_codes=(
                ["calorie_target_available"]
                if calories_available
                else ["calorie_delta_not_available"]
            ),
        ),
        "protein": _comparison(
            "protein",
            status=protein_status,
            available=protein_available,
            actual=90 if protein_available else None,
            reason_codes=(
                ["protein_target_available"]
                if protein_available
                else ["protein_delta_not_available"]
            ),
        ),
        "carbs": _comparison(
            "carbs",
            status=(
                TARGET_STATUS_NEAR if macros_available else TARGET_STATUS_UNAVAILABLE
            ),
            available=macros_available,
            actual=200 if macros_available else None,
        ),
        "fat": _comparison(
            "fat",
            status=(
                TARGET_STATUS_NEAR if macros_available else TARGET_STATUS_UNAVAILABLE
            ),
            available=macros_available,
            actual=65 if macros_available else None,
        ),
    }
    reason_codes = ["nutrition_target_vs_actual_fixture"]
    if completeness == LOGGING_COMPLETENESS_NO_LOGS:
        reason_codes.append("no_nutrition_logs_today")
    if protein_available and protein_status == TARGET_STATUS_BELOW:
        reason_codes.append("logged_protein_below_target")
    if protein_available and protein_status == TARGET_STATUS_NEAR:
        reason_codes.append("logged_intake_near_protein_target")

    summary = TargetVsActualNutritionSummary(
        user_id=999,
        date="2026-06-05",
        nutrition_actuals=actuals,
        logging_summary=logging_summary,
        comparisons=comparisons,
        logging_completeness=completeness,
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=[],
    )
    guidance = ApprovedNutritionGuidance(
        user_id=999,
        date="2026-06-05",
        summary_message=(
            "No nutrition logs were found for this date."
            if completeness == LOGGING_COMPLETENESS_NO_LOGS
            else (
                "Nutrition logging is incomplete, so conclusions should stay limited."
                if completeness
                in {
                    LOGGING_COMPLETENESS_PARTIAL_DAY,
                    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
                }
                else "Logged nutrition can be compared cautiously with approved targets."
            )
        ),
        protein_guidance=(
            "Based on logged meals, protein is below today's target."
            if protein_available and protein_status == TARGET_STATUS_BELOW
            else (
                "Protein is close to target based on current logs."
                if protein_available and protein_status == TARGET_STATUS_NEAR
                else "Protein comparison is limited until approved protein targets and logged protein are available."
            )
        ),
        calorie_guidance=(
            "Logged calories are near the approved range based on complete-enough logs."
            if calories_available
            else "Nutrition logging is incomplete, so calorie conclusions should stay limited."
        ),
        macro_guidance=(
            "Carbohydrate and fat logs can be compared cautiously against approved ranges."
            if macros_available
            else "Macro comparisons are limited until logging is more complete."
        ),
        logging_guidance=(
            "No nutrition logs were found for this date, so guidance should stay limited."
            if completeness == LOGGING_COMPLETENESS_NO_LOGS
            else "Logged intake is incomplete, so avoid making bigger nutrition changes from this day alone."
        ),
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=[],
    )
    return summary, guidance


def _food_suggestions(
    *,
    primary_gap: str | None = "protein_g",
    confidence: str = "Moderate",
    with_suggestions: bool = True,
    reason_codes: list[str] | None = None,
    limitations: list[str] | None = None,
) -> ApprovedNutritionFoodSuggestions:
    macro_name = primary_gap or "protein_g"
    unit = "kcal" if macro_name == "calories" else "g"
    macro_gaps = [
        NutritionMacroGap(
            macro_name=macro_name,
            target_value=2000 if macro_name == "calories" else 150,
            actual_value=1700 if macro_name == "calories" else 100,
            gap_value=300 if macro_name == "calories" else 50,
            unit=unit,
            target_status=TARGET_STATUS_BELOW,
            display_allowed=True,
            confidence=confidence,
            reason_codes=[f"{macro_name}_gap_available"],
            limitations=[],
        )
    ]
    suggestions = []
    if with_suggestions:
        display_name = {
            "protein_g": "Chicken Breast, Cooked, Skinless",
            "carbohydrate_g": "White Rice, Cooked",
            "calories": "Oats, Dry",
            "fat_g": "Olive Oil",
        }.get(macro_name, "Chicken Breast, Cooked, Skinless")
        suggestions.append(
            ApprovedFoodSuggestion(
                canonical_food_id=101,
                display_name=display_name,
                suggested_grams=150 if macro_name != "fat_g" else 10,
                estimated_calories=250,
                estimated_protein_g=35 if macro_name == "protein_g" else 4,
                estimated_carbohydrate_g=45 if macro_name == "carbohydrate_g" else 8,
                estimated_fat_g=10 if macro_name == "fat_g" else 3,
                macro_gap_addressed=macro_name,
                suggestion_summary="The Nutrition tab has an approved food option.",
                confidence=confidence,
                reason_codes=["canonical_food_nutrients_available"],
                limitations=[],
            )
        )

    return ApprovedNutritionFoodSuggestions(
        user_id=999,
        suggestion_date="2026-06-05",
        primary_gap=primary_gap,
        macro_gaps=macro_gaps,
        suggestions=suggestions,
        confidence=confidence,
        reason_codes=reason_codes
        or (
            ["food_suggestions_available"]
            if suggestions
            else ["no_supported_suggestion_gap_available"]
        ),
        limitations=limitations
        or (
            []
            if suggestions
            else ["No approved supported suggestion gap is available."]
        ),
    )


def _with_nutrition(
    components: dict,
    summary: TargetVsActualNutritionSummary,
    guidance: ApprovedNutritionGuidance,
) -> dict:
    updated = dict(components)
    updated["nutrition_target_vs_actual_summary"] = summary
    updated["approved_nutrition_guidance"] = guidance
    return updated


def test_no_recovery_checkin_available_returns_safe_limitation_language():
    components = _build_components(
        _no_recovery_health_state(),
        _summary(completed_execution_count=0),
    )

    synthesis = build_daily_coach_synthesis_from_components(**components)
    violations = validate_daily_coach_synthesis(
        synthesis,
        recommendation_context=components["recommendation_context"],
        approved_workout_plan=components["approved_workout_plan"],
        training_execution_summary=components["training_execution_summary"],
    )

    assert violations == []
    assert "recovery check-in data is limited" in synthesis.recovery_signal.lower()
    assert "recovery_checkin_missing_or_limited" in synthesis.limitations


def test_no_completed_planned_workouts_produces_no_execution_trend_claims():
    components = _build_components(summary=_summary(completed_execution_count=0))

    synthesis = build_daily_coach_synthesis_from_components(**components)

    assert "no completed planned workouts" in synthesis.execution_context.lower()
    assert "trend" not in synthesis.execution_context.lower()
    assert "no_completed_planned_workout_execution_data" in synthesis.limitations


def test_one_completed_planned_workout_does_not_create_trend_claims():
    components = _build_components(
        summary=_summary(
            completed_execution_count=1,
            confidence="Low",
            execution_quality="limited_execution_data",
            average_rir_deviation=-0.5,
        )
    )

    synthesis = build_daily_coach_synthesis_from_components(**components)
    violations = validate_daily_coach_synthesis(
        synthesis,
        recommendation_context=components["recommendation_context"],
        approved_workout_plan=components["approved_workout_plan"],
        training_execution_summary=components["training_execution_summary"],
    )

    assert violations == []
    assert "one completed planned workout" in synthesis.execution_context.lower()
    assert "trend" not in synthesis.execution_context.lower()


def test_multiple_completed_workouts_can_produce_cautious_pattern_language():
    components = _build_components(
        summary=_summary(
            completed_execution_count=3,
            confidence="Moderate",
            execution_quality="consistently_completed",
            execution_effort_trend="close_to_plan",
        )
    )

    synthesis = build_daily_coach_synthesis_from_components(**components)

    assert "recent completed workouts" in synthesis.execution_context.lower()
    assert "generally close to the plan" in synthesis.execution_context.lower()
    assert "automatic" not in synthesis.execution_context.lower()


def test_incomplete_logging_produces_limitation_language():
    components = _build_components(
        summary=_summary(
            completed_execution_count=3,
            confidence="Low",
            execution_quality="mostly_completed",
            incomplete_logging_count=2,
        )
    )

    synthesis = build_daily_coach_synthesis_from_components(**components)

    assert "incomplete" in synthesis.execution_context.lower()
    assert "limits" in synthesis.execution_context.lower()
    assert "incomplete_actual_set_logging_limits_inference" in synthesis.limitations


def test_low_confidence_produces_soft_contextual_copy_only():
    components = _build_components(
        _no_recovery_health_state(),
        _summary(completed_execution_count=0, confidence="Limited"),
        confidence="Low",
    )
    recommendation_context = components["recommendation_context"]
    approved_action_plan = _fake_action_plan(recommendation_context, confidence="Low")
    components["approved_action_plan"] = approved_action_plan

    synthesis = build_daily_coach_synthesis_from_components(**components)
    violations = validate_daily_coach_synthesis(
        synthesis,
        recommendation_context=recommendation_context,
        approved_action_plan=approved_action_plan,
        approved_workout_plan=components["approved_workout_plan"],
        training_execution_summary=components["training_execution_summary"],
    )

    assert violations == []
    assert synthesis.confidence == "Low"
    assert "limited" in " ".join(synthesis.limitations)
    assert "must" not in synthesis.to_dict()["today_summary"].lower()


def test_harder_than_planned_effort_anchors_to_rir_without_overtraining_or_deload():
    components = _build_components(
        summary=_summary(
            completed_execution_count=3,
            confidence="Moderate",
            execution_quality="mostly_completed",
            execution_effort_trend="harder_than_planned",
            average_rir_deviation=-1.0,
        )
    )

    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = (
        " ".join(synthesis.to_dict().values())
        if False
        else str(synthesis.to_dict()).lower()
    )

    assert "harder than planned" in synthesis.execution_context.lower()
    assert "rir target" in synthesis.execution_context.lower()
    assert "overtraining" not in combined
    assert "deload" not in combined


def test_easier_than_planned_effort_does_not_produce_progression_or_load_increase():
    components = _build_components(
        summary=_summary(
            completed_execution_count=3,
            confidence="Moderate",
            execution_quality="mostly_completed",
            execution_effort_trend="easier_than_planned",
            average_rir_deviation=1.0,
        )
    )

    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = str(synthesis.to_dict()).lower()

    assert "easier than planned" in synthesis.execution_context.lower()
    assert "automatic progression" not in combined
    assert "increase load" not in combined
    assert "add weight" not in combined


def test_substitutions_and_skips_use_plan_fit_context_not_adherence_language():
    components = _build_components(
        summary=_summary(
            completed_execution_count=3,
            confidence="Moderate",
            execution_quality="plan_fit_review_signal",
            skipped_exercise_count=2,
            substituted_exercise_count=1,
        )
    )

    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = str(synthesis.to_dict()).lower()

    assert "plan fit" in synthesis.plan_fit_note.lower()
    assert "poor adherence" not in combined
    assert "discipline" not in combined
    assert "failed" not in combined


def test_data_quality_limited_avoids_nutrition_adequacy_supplement_and_stalled_claims():
    _health_state = _no_recovery_health_state()
    components = _build_components(_health_state, _summary(completed_execution_count=0))
    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = str(synthesis.to_dict()).lower()

    assert synthesis.scenario == "data_quality_limited"
    assert "logging" in combined
    assert "supplement" not in combined
    assert "nutrition is inadequate" not in combined
    assert "stalled" not in combined


def test_synthesis_does_not_change_approved_workout_exercises_sets_reps_or_rir():
    components = _build_components(summary=_summary(completed_execution_count=0))
    approved_plan = components["approved_workout_plan"]

    before = [
        (
            exercise.name,
            exercise.sets,
            exercise.reps_min,
            exercise.reps_max,
            exercise.rir_min,
            exercise.rir_max,
        )
        for exercise in approved_plan.exercises
    ]
    synthesis = build_daily_coach_synthesis_from_components(**components)
    after = [
        (
            exercise.name,
            exercise.sets,
            exercise.reps_min,
            exercise.reps_max,
            exercise.rir_min,
            exercise.rir_max,
        )
        for exercise in approved_plan.exercises
    ]

    assert before == after
    assert "approved plan as written" in synthesis.workout_guidance.lower()


def test_synthesis_does_not_change_nutrition_targets():
    components = _build_components(summary=_summary(completed_execution_count=0))
    targets_before = components["recommendation_context"].nutrition_targets

    build_daily_coach_synthesis_from_components(**components)

    targets_after = components["recommendation_context"].nutrition_targets
    assert targets_after == targets_before


@pytest.mark.parametrize("user_id", QA_USER_IDS)
def test_seeded_users_produce_safe_scenario_aligned_synthesis(
    user_id, tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    synthesis = build_daily_coach_synthesis(user_id)
    combined = str(synthesis.to_dict()).lower()

    assert synthesis.user_id == user_id
    assert synthesis.scenario in {
        "recovery_limited",
        "aligned_managed",
        "nutrition_training_mismatch",
        "improving_after_deload",
        "data_quality_limited",
    }
    assert synthesis.today_summary
    assert synthesis.workout_guidance
    assert "overtraining" not in combined
    assert "poor adherence" not in combined
    assert "lack of discipline" not in combined
    assert "automatic deload" not in combined
    assert "automatic progression" not in combined


def test_no_logs_nutrition_adds_safe_limitation_and_no_macro_claims():
    components = _build_components(summary=_summary(completed_execution_count=0))
    nutrition_summary, guidance = _nutrition_summary_and_guidance(
        completeness=LOGGING_COMPLETENESS_NO_LOGS,
        confidence="Limited",
    )
    components = _with_nutrition(components, nutrition_summary, guidance)

    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = str(synthesis.to_dict()).lower()

    assert "No nutrition logs are available for today yet." in synthesis.limitations
    assert "nutrition_no_logs_today" in synthesis.reason_codes
    assert "carbs are" not in combined
    assert "fat is" not in combined
    assert "calories are below" not in combined
    assert "calories are above" not in combined


def test_incomplete_nutrition_logging_limits_calorie_and_macro_certainty():
    components = _build_components(summary=_summary(completed_execution_count=0))
    nutrition_summary, guidance = _nutrition_summary_and_guidance(
        completeness=LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
        confidence="Low",
    )
    components = _with_nutrition(components, nutrition_summary, guidance)

    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = str(synthesis.to_dict()).lower()

    assert "nutrition_logging_incomplete" in synthesis.reason_codes
    assert "calorie conclusions" in synthesis.logging_focus.lower()
    assert "calorie conclusions are limited" in str(synthesis.limitations).lower()
    assert "calories are below" not in combined
    assert "macro comparisons are limited" in str(synthesis.limitations).lower()


def test_approved_protein_below_target_can_appear_as_focus():
    components = _build_components(summary=_summary(completed_execution_count=0))
    nutrition_summary, guidance = _nutrition_summary_and_guidance(
        completeness="complete_enough_for_guidance",
        confidence="Moderate",
        protein_status=TARGET_STATUS_BELOW,
        protein_available=True,
    )
    components = _with_nutrition(components, nutrition_summary, guidance)

    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = str(synthesis.to_dict()).lower()

    assert "protein_below_target_based_on_logs" in synthesis.reason_codes
    assert "protein-centered meal" in synthesis.recommended_focus
    assert "based on logged meals" in combined
    assert "must" not in combined


def test_approved_protein_near_target_can_appear_cautiously():
    components = _build_components(summary=_summary(completed_execution_count=0))
    nutrition_summary, guidance = _nutrition_summary_and_guidance(
        completeness="complete_enough_for_guidance",
        confidence="Moderate",
        protein_status=TARGET_STATUS_NEAR,
        protein_available=True,
    )
    components = _with_nutrition(components, nutrition_summary, guidance)

    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = str(synthesis.to_dict()).lower()

    assert "protein_near_target_based_on_logs" in synthesis.reason_codes
    assert "protein is close to target" in combined
    assert "medical" not in combined


def test_blocked_calorie_comparison_does_not_appear_as_hard_claim():
    components = _build_components(summary=_summary(completed_execution_count=0))
    nutrition_summary, guidance = _nutrition_summary_and_guidance(
        completeness=LOGGING_COMPLETENESS_PARTIAL_DAY,
        confidence="Low",
        protein_status=TARGET_STATUS_BELOW,
        protein_available=True,
        calories_available=False,
    )
    components = _with_nutrition(components, nutrition_summary, guidance)

    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = str(synthesis.to_dict()).lower()

    assert "calorie_comparison_limited" in synthesis.reason_codes
    assert "calories are below" not in combined
    assert "calories are above" not in combined
    assert (
        "calorie conclusions" in combined
        or "calorie conclusions" in str(synthesis.limitations).lower()
    )


def test_carbs_and_fats_only_appear_when_approved_by_nutrition_service():
    components = _build_components(summary=_summary(completed_execution_count=0))
    blocked_summary, blocked_guidance = _nutrition_summary_and_guidance(
        completeness=LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
        confidence="Low",
        macros_available=False,
    )
    allowed_summary, allowed_guidance = _nutrition_summary_and_guidance(
        completeness="complete_enough_for_guidance",
        confidence="Moderate",
        macros_available=True,
    )

    blocked = build_daily_coach_synthesis_from_components(
        **_with_nutrition(components, blocked_summary, blocked_guidance)
    )
    allowed = build_daily_coach_synthesis_from_components(
        **_with_nutrition(components, allowed_summary, allowed_guidance)
    )

    assert "carbohydrate and fat" not in str(blocked.to_dict()).lower()
    assert "macro_comparison_limited" in blocked.reason_codes
    assert "Carbohydrate and fat logs" in allowed.recommended_focus


def test_nutrition_training_mismatch_mentions_support_without_hard_macro_claims():
    components = _build_components(
        summary=_summary(completed_execution_count=0),
        scenario="nutrition_training_mismatch",
    )
    nutrition_summary, guidance = _nutrition_summary_and_guidance(
        completeness=LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
        confidence="Low",
    )
    components = _with_nutrition(components, nutrition_summary, guidance)

    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = str(synthesis.to_dict()).lower()

    assert synthesis.scenario == "nutrition_training_mismatch"
    assert "nutrition" in combined
    assert "logging" in combined
    assert "zero intake" not in combined
    assert "carbs are below" not in combined
    assert "fat is below" not in combined


_PUBLIC_DAILY_COACH_TOP_LEVEL_KEYS = {
    "success",
    "user_id",
    "synthesis_date",
    "scenario",
    "confidence",
    "daily_coach_synthesis",
}

_PUBLIC_DAILY_COACH_SYNTHESIS_KEYS = {
    "user_id",
    "synthesis_date",
    "scenario",
    "confidence",
    "today_summary",
    "recovery_signal",
    "training_signal",
    "workout_guidance",
    "execution_context",
    "logging_focus",
    "plan_fit_note",
    "recommended_focus",
    "reason_codes",
    "limitations",
}

_PUBLIC_DAILY_COACH_FORBIDDEN_KEYS = {
    "raw_actual_set_rows",
    "raw_notes",
    "raw_output",
    "runtime_metadata",
    "validator_internals",
    "prompt",
    "prompt_text",
    "debug_payload",
    "provider_metadata",
    "validation_errors",
}


def _collect_keys(value):
    keys = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(key)
            keys.update(_collect_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(_collect_keys(nested))
    return keys


def test_daily_coach_synthesis_endpoint_returns_public_contract_for_seeded_users(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    for user_id in QA_USER_IDS:
        response = client.get(f"/daily-coach/{user_id}/synthesis")
        payload = response.json()

        assert response.status_code == 200
        assert set(payload) == _PUBLIC_DAILY_COACH_TOP_LEVEL_KEYS
        assert payload["success"] is True
        assert payload["user_id"] == user_id
        assert payload["scenario"] in {
            "recovery_limited",
            "aligned_managed",
            "nutrition_training_mismatch",
            "improving_after_deload",
            "data_quality_limited",
        }
        assert payload["daily_coach_synthesis"]
        assert (
            set(payload["daily_coach_synthesis"]) == _PUBLIC_DAILY_COACH_SYNTHESIS_KEYS
        )
        assert payload["daily_coach_synthesis"]["user_id"] == user_id


def test_daily_coach_synthesis_endpoint_does_not_expose_debug_or_runtime_fields(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/daily-coach/102/synthesis")
    payload = response.json()

    assert response.status_code == 200
    assert not (_collect_keys(payload) & _PUBLIC_DAILY_COACH_FORBIDDEN_KEYS)
    assert "approved_workout_plan" not in payload
    assert "training_execution_summary" not in payload


def test_daily_coach_synthesis_endpoint_missing_user_returns_safe_404(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/daily-coach/999999/synthesis")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_daily_coach_synthesis_endpoint_data_quality_limited_remains_safe(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/daily-coach/105/synthesis")
    payload = response.json()
    combined = str(payload).lower()

    assert response.status_code == 200
    assert payload["scenario"] == "data_quality_limited"
    assert "logging" in combined or "verification" in combined
    assert "nutrition is inadequate" not in combined
    assert "supplement" not in combined
    assert "stalled progress" not in combined
    assert "stalled fat loss" not in combined
    assert "overtraining" not in combined


def test_daily_coach_synthesis_endpoint_recovery_limited_uses_controlled_language(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/daily-coach/101/synthesis")
    payload = response.json()
    combined = str(payload).lower()

    assert response.status_code == 200
    assert payload["scenario"] == "recovery_limited"
    assert "controlled" in combined or "recovery" in combined
    assert "overtraining" not in combined
    assert "deload" not in combined
    assert "automatic progression" not in combined


def test_daily_coach_synthesis_endpoint_keeps_recommendation_endpoint_shape_stable(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    daily_response = client.get("/recommendations/daily/102")
    debug_response = client.get("/recommendations/daily/102/debug")

    assert daily_response.status_code == 200
    assert set(daily_response.json()) == {
        "success",
        "user_id",
        "scenario",
        "confidence",
        "nutrition_targets",
        "training_constraints",
        "approved_action_plan",
        "rendered_recommendation",
    }
    assert debug_response.status_code == 200
    assert "runtime_metadata" in debug_response.json()
    assert "training_execution_summary" in debug_response.json()


def test_daily_coach_synthesis_composes_approved_food_suggestion_context():
    components = _build_components(summary=_summary(completed_execution_count=0))
    nutrition_summary, guidance = _nutrition_summary_and_guidance(
        completeness="complete_enough_for_guidance",
        confidence="Moderate",
        protein_status=TARGET_STATUS_BELOW,
        protein_available=True,
    )
    components = _with_nutrition(components, nutrition_summary, guidance)
    components["approved_food_suggestions"] = _food_suggestions()

    synthesis = build_daily_coach_synthesis_from_components(**components)
    violations = validate_daily_coach_synthesis(
        synthesis,
        recommendation_context=components["recommendation_context"],
        approved_workout_plan=components["approved_workout_plan"],
        training_execution_summary=components["training_execution_summary"],
        nutrition_target_vs_actual_summary=nutrition_summary,
        approved_nutrition_guidance=guidance,
    )

    assert violations == []
    assert "Nutrition tab" in synthesis.recommended_focus
    assert "protein-focused" in synthesis.recommended_focus
    assert "nutrition_food_suggestions_context_available" in synthesis.reason_codes
    assert "canonical_food_id" not in str(synthesis.to_dict())


@pytest.mark.parametrize(
    ("primary_gap", "expected_phrase"),
    [
        ("carbohydrate_g", "Carbohydrate suggestions are available"),
        ("calories", "approved calorie-support food options"),
        ("fat_g", "approved fat-support food options"),
    ],
)
def test_daily_coach_synthesis_references_nonprotein_food_suggestions_safely(
    primary_gap, expected_phrase
):
    components = _build_components(summary=_summary(completed_execution_count=0))
    nutrition_summary, guidance = _nutrition_summary_and_guidance(
        completeness="complete_enough_for_guidance",
        confidence="Moderate",
        calories_available=True,
        macros_available=True,
    )
    components = _with_nutrition(components, nutrition_summary, guidance)
    components["approved_food_suggestions"] = _food_suggestions(primary_gap=primary_gap)

    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = str(synthesis.to_dict()).lower()

    assert expected_phrase.lower() in synthesis.recommended_focus.lower()
    assert "canonical_food_id" not in combined
    assert "suggested_grams" not in combined
    assert "you must" not in combined


def test_low_confidence_food_suggestions_add_cautious_limitation_only():
    components = _build_components(summary=_summary(completed_execution_count=0))
    nutrition_summary, guidance = _nutrition_summary_and_guidance(
        completeness="complete_enough_for_guidance",
        confidence="Moderate",
        protein_status=TARGET_STATUS_BELOW,
        protein_available=True,
    )
    components = _with_nutrition(components, nutrition_summary, guidance)
    components["approved_food_suggestions"] = _food_suggestions(
        confidence="Low",
        limitations=["Suggestions are limited because logging appears incomplete."],
    )

    synthesis = build_daily_coach_synthesis_from_components(**components)

    assert "Food suggestions are limited" in synthesis.recommended_focus
    assert "Food suggestions are limited" in synthesis.logging_focus
    assert "approved protein-focused food options" not in synthesis.recommended_focus
    assert any("Food suggestions are limited" in item for item in synthesis.limitations)


def test_no_suggestion_state_does_not_create_negative_or_judgmental_language():
    components = _build_components(summary=_summary(completed_execution_count=0))
    nutrition_summary, guidance = _nutrition_summary_and_guidance(
        completeness="complete_enough_for_guidance",
        confidence="Moderate",
        calories_available=True,
        macros_available=True,
    )
    components = _with_nutrition(components, nutrition_summary, guidance)
    components["approved_food_suggestions"] = _food_suggestions(
        primary_gap=None,
        with_suggestions=False,
        reason_codes=["no_supported_suggestion_gap_available"],
        limitations=["No approved supported suggestion gap is available."],
    )

    synthesis = build_daily_coach_synthesis_from_components(**components)
    combined = str(synthesis.to_dict()).lower()

    assert "no approved supported gap is available" in combined
    assert "nutrition_food_suggestions_context_limited" in synthesis.reason_codes
    assert "failed" not in combined
    assert "discipline" not in combined
    assert "must" not in combined


def test_daily_coach_synthesis_rejects_food_suggestion_internal_fields():
    components = _build_components(summary=_summary(completed_execution_count=0))
    synthesis = build_daily_coach_synthesis_from_components(**components)
    bad_synthesis = DailyCoachSynthesis(
        **{
            **synthesis.to_dict(),
            "recommended_focus": "Use canonical_food_id 101 and suggested_grams from the food suggestion payload.",
        }
    )

    violations = validate_daily_coach_synthesis(bad_synthesis)

    assert any("food suggestion internals" in violation for violation in violations)
