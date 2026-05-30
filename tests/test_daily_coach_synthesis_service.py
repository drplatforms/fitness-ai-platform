from __future__ import annotations

import pytest

import database
from models.coaching_decision_models import CoachingDecision
from models.nutrition_target_models import NutritionTargets
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
