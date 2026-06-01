import json
from dataclasses import asdict, replace

import pytest
from fastapi.testclient import TestClient

import database
import services.post_workout_review_service as post_workout_review_service
import services.workout_plan_service as workout_plan_service
from api.main import app
from models.exercise_catalog_models import ExerciseCatalogEntry
from models.training_constraint_models import TrainingConstraints
from models.workout_constraint_models import WorkoutConstraints
from models.workout_plan_models import WorkoutContext
from scripts.seed_qa_scenarios import QA_USER_IDS, seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.exercise_catalog_service import find_catalog_entry_by_name
from services.post_workout_review_service import (
    approve_candidate_post_workout_review_summary,
    approve_post_workout_review_summary_provider_or_fallback_with_metadata,
    build_configured_post_workout_review_summary_with_metadata,
    build_post_workout_review_context,
    parse_candidate_post_workout_review_summary_json,
    validate_candidate_post_workout_review_summary,
)
from services.user_state_service import build_user_health_state
from services.workout_plan_persistence_service import (
    complete_workout_plan,
    log_actual_set,
    select_current_workout_plan,
    start_selected_workout_plan,
)
from services.workout_plan_service import (
    WorkoutCandidateParseError,
    _crewai_workout_llm_kwargs,
    _select_exercise,
    approve_candidate_workout_explanation,
    approve_candidate_workout_plan,
    approve_workout_candidate_provider_or_fallback_with_metadata,
    approve_workout_explanation_provider_or_fallback_with_metadata,
    build_approved_workout_plan,
    build_approved_workout_plan_from_candidate_output,
    build_configured_approved_workout_plan_with_metadata,
    build_configured_workout_explanation_with_metadata,
    build_crewai_candidate_workout_plan_prompt,
    build_crewai_workout_explanation_prompt,
    build_deterministic_workout_explanation,
    build_workout_context,
    generate_candidate_workout_plan,
    parse_candidate_workout_explanation_json,
    parse_candidate_workout_plan_json,
    render_approved_workout_plan,
    validate_candidate_workout_explanation,
    validate_candidate_workout_plan,
    workout_context_to_llm_json,
)

EXPECTED_SCENARIOS = {
    101: "recovery_limited",
    102: "aligned_managed",
    103: "nutrition_training_mismatch",
    104: "improving_after_deload",
    105: "data_quality_limited",
}


USER_HOME_GYM_EQUIPMENT = [
    "adjustable_bench",
    "barbell",
    "bike",
    "bodyweight",
    "cable",
    "dumbbell",
    "exercise_ball",
    "ez_bar",
    "plates",
    "pull_up_bar",
    "rack",
    "resistance_band",
    "rope_cable_attachment",
    "treadmill",
]


def _movement_patterns_for_plan(approved):
    patterns = []
    for exercise in approved.exercises:
        entry = find_catalog_entry_by_name(exercise.name)
        if entry is not None:
            patterns.append(entry.movement_pattern)
    return patterns


def _seeded_health_states(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    return {user_id: build_user_health_state(user_id) for user_id in QA_USER_IDS}


def test_seeded_users_build_valid_approved_workout_plans(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)

    for user_id, health_state in health_states.items():
        context = build_workout_context(health_state)
        candidate = generate_candidate_workout_plan(context)
        violations = validate_candidate_workout_plan(candidate, context)
        approved = approve_candidate_workout_plan(candidate, context)
        rendered = render_approved_workout_plan(approved)

        assert context.scenario == EXPECTED_SCENARIOS[user_id]
        assert violations == []
        assert approved.scenario == EXPECTED_SCENARIOS[user_id]
        assert approved.exercises
        assert "Workout Plan Preview" in rendered
        assert "RIR" in rendered


def test_recovery_limited_workout_is_recovery_aware(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_workout_plan(health_states[101])
    rendered = render_approved_workout_plan(approved).lower()

    assert approved.scenario == "recovery_limited"
    assert "recovery" in rendered
    assert "rir 2-3" in rendered
    assert "max effort" not in rendered
    assert "to failure" not in rendered
    assert all(exercise.rir_min >= 2 for exercise in approved.exercises)
    assert all(exercise.rir_max <= 3 for exercise in approved.exercises)


def test_aligned_managed_workout_avoids_unnecessary_intervention(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_workout_plan(health_states[102])
    rendered = render_approved_workout_plan(approved).lower()

    assert approved.scenario == "aligned_managed"
    assert "gradual" in rendered or "progress" in rendered
    assert "deload" not in rendered
    assert "reduce intensity" not in rendered
    assert "cut volume" not in rendered


def test_nutrition_training_mismatch_workout_stays_controlled(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_workout_plan(health_states[103])
    rendered = render_approved_workout_plan(approved).lower()

    assert approved.scenario == "nutrition_training_mismatch"
    assert "nutrition" in rendered
    assert "controlled" in rendered
    assert "0 kcal" not in rendered


def test_improving_after_deload_workout_uses_controlled_progression(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_workout_plan(health_states[104])
    rendered = render_approved_workout_plan(approved).lower()

    assert approved.scenario == "improving_after_deload"
    assert "controlled" in rendered or "gradual" in rendered
    assert "ramping too quickly" in rendered or "jumping back" in rendered


def test_data_quality_limited_workout_uses_manageable_baseline_language(
    tmp_path, monkeypatch
):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    approved = build_approved_workout_plan(health_states[105])
    rendered = render_approved_workout_plan(approved).lower()

    assert approved.scenario == "data_quality_limited"
    assert "logging" in rendered
    assert "baseline" in rendered or "manageable" in rendered
    assert "overtraining" not in rendered
    assert "stalled progress" not in rendered
    assert "stalled fat loss" not in rendered


def test_workout_validator_rejects_invalid_and_unsafe_candidate(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_workout_context(health_states[101])
    candidate = generate_candidate_workout_plan(context)
    candidate.exercises[0].rir_min = 0
    candidate.exercises[0].rir_max = 1
    candidate.progression_guidance = "Use max effort sets to failure."

    violations = validate_candidate_workout_plan(candidate, context)

    assert violations
    assert any(
        "RIR" in violation or "max-effort" in violation for violation in violations
    )


def test_workout_context_includes_workout_constraints(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_workout_context(health_states[105])

    assert context.workout_constraints.available_equipment
    assert context.workout_constraints.recent_exercises
    assert "safe_default_equipment_assumptions" in context.reason_codes


def test_workout_generator_respects_unavailable_equipment(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_workout_context(health_states[102])
    restricted_context = replace(
        context,
        workout_constraints=WorkoutConstraints(
            available_equipment=["dumbbell", "bodyweight"],
            unavailable_equipment=["barbell", "machine", "cable"],
            confidence="Low",
            reason_codes=["test_equipment_restricted"],
        ),
    )

    candidate = generate_candidate_workout_plan(restricted_context)
    violations = validate_candidate_workout_plan(candidate, restricted_context)
    exercise_names = " ".join(exercise.name for exercise in candidate.exercises).lower()

    assert violations == []
    assert "barbell" not in exercise_names
    assert all(
        "barbell" not in exercise.equipment_required for exercise in candidate.exercises
    )


def test_workout_validator_rejects_unavailable_equipment(tmp_path, monkeypatch):
    health_states = _seeded_health_states(tmp_path, monkeypatch)
    context = build_workout_context(health_states[102])
    restricted_context = replace(
        context,
        workout_constraints=WorkoutConstraints(
            available_equipment=["dumbbell", "bodyweight"],
            unavailable_equipment=["barbell"],
            confidence="Low",
            reason_codes=["test_equipment_restricted"],
        ),
    )
    candidate = generate_candidate_workout_plan(restricted_context)
    candidate.exercises[0].name = "Barbell Squat"
    candidate.exercises[0].equipment_required = ["barbell"]

    violations = validate_candidate_workout_plan(candidate, restricted_context)

    assert any("equipment" in violation.lower() for violation in violations)


def test_workout_plan_preview_endpoint_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    client = TestClient(app)
    response = client.get("/workout-plans/preview/105")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 105
    assert payload["scenario"] == "data_quality_limited"
    assert payload["confidence"] == "Low"
    assert payload["training_constraints"]["recommended_rir_min"] == 2
    assert "workout_constraints" in payload
    assert payload["workout_constraints"]["available_equipment"]
    assert payload["approved_workout_plan"]["exercises"]
    assert "Workout Plan Preview" in payload["rendered_workout_plan"]


def test_scored_selection_penalizes_recent_exact_exercises(tmp_path, monkeypatch):
    _seeded_health_states(tmp_path, monkeypatch)
    workout_constraints = WorkoutConstraints(
        available_equipment=[
            "bodyweight",
            "barbell",
            "dumbbell",
            "plates",
            "rack",
        ],
        unavailable_equipment=["machine"],
        recent_exercises=["Romanian Deadlift"],
        confidence="High",
        reason_codes=["test_recent_history"],
    )

    name, equipment_required = _select_exercise(
        workout_constraints,
        [
            ("Romanian Deadlift", ["barbell"]),
            ("Goblet Squat", ["dumbbell"]),
        ],
    )

    assert name == "Goblet Squat"
    assert equipment_required == ["dumbbell"]


def test_scored_selection_uses_deterministic_top_k_rotation_by_user(
    tmp_path, monkeypatch
):
    _seeded_health_states(tmp_path, monkeypatch)
    workout_constraints = WorkoutConstraints(
        available_equipment=[
            "bodyweight",
            "barbell",
            "cable",
            "dumbbell",
            "rope_cable_attachment",
        ],
        unavailable_equipment=["machine"],
        confidence="High",
        reason_codes=["test_home_gym_rotation"],
    )
    options = [
        ("Romanian Deadlift", ["barbell"]),
        ("Goblet Squat", ["dumbbell"]),
        ("Cable Pull-Through", ["cable", "rope_cable_attachment"]),
        ("Bodyweight Squat", ["bodyweight"]),
    ]

    user_101_selection = _select_exercise(
        workout_constraints, options, user_id=101, slot_key="lower_body"
    )
    user_102_selection = _select_exercise(
        workout_constraints, options, user_id=102, slot_key="lower_body"
    )

    assert user_101_selection != user_102_selection
    assert user_101_selection[0] in {name for name, _equipment in options}
    assert user_102_selection[0] in {name for name, _equipment in options}


def test_home_gym_repeated_selected_previews_use_broader_pool(tmp_path, monkeypatch):
    _seeded_health_states(tmp_path, monkeypatch)
    save_equipment_profile(
        user_id=102,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    exercise_names: set[str] = set()
    equipment_modalities: set[str] = set()
    for _index in range(5):
        approved = build_approved_workout_plan(build_user_health_state(102))
        exercise_names.update(exercise.name for exercise in approved.exercises)
        for exercise in approved.exercises:
            equipment_modalities.update(exercise.equipment_required)
            assert "machine" not in exercise.equipment_required
        select_current_workout_plan(102)

    assert len(exercise_names) >= 12
    assert {"barbell", "cable", "dumbbell"}.issubset(equipment_modalities)
    assert equipment_modalities & {
        "bodyweight",
        "pull_up_bar",
        "resistance_band",
        "ez_bar",
    }


def test_home_gym_preview_rotates_after_recent_planned_history(tmp_path, monkeypatch):
    _seeded_health_states(tmp_path, monkeypatch)
    save_equipment_profile(
        user_id=102,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    first_plan = build_approved_workout_plan(build_user_health_state(102))
    select_current_workout_plan(102)
    second_plan = build_approved_workout_plan(build_user_health_state(102))

    first_names = [exercise.name for exercise in first_plan.exercises]
    second_names = [exercise.name for exercise in second_plan.exercises]

    assert second_names != first_names
    assert any(name not in first_names for name in second_names)
    assert all(
        "machine" not in exercise.equipment_required
        for exercise in second_plan.exercises
    )


def test_home_gym_preview_rotates_movement_patterns_after_recent_trio(
    tmp_path, monkeypatch
):
    _seeded_health_states(tmp_path, monkeypatch)
    save_equipment_profile(
        user_id=102,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    select_current_workout_plan(102)
    second_plan = build_approved_workout_plan(build_user_health_state(102))
    patterns = set(_movement_patterns_for_plan(second_plan))

    assert "squat" in patterns or "hinge" in patterns
    assert "horizontal_push" in patterns or "vertical_push" in patterns
    assert "horizontal_pull" in patterns or "vertical_pull" in patterns


def test_home_gym_ten_preview_select_cycles_do_not_converge_to_same_plan(
    tmp_path, monkeypatch
):
    _seeded_health_states(tmp_path, monkeypatch)
    save_equipment_profile(
        user_id=102,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )

    plan_name_lists: list[tuple[str, ...]] = []
    distinct_exercises: set[str] = set()
    equipment_modalities: set[str] = set()

    for _index in range(10):
        approved = build_approved_workout_plan(build_user_health_state(102))
        names = tuple(exercise.name for exercise in approved.exercises)
        plan_name_lists.append(names)
        distinct_exercises.update(names)

        for exercise in approved.exercises:
            equipment_modalities.update(exercise.equipment_required)
            assert "machine" not in exercise.equipment_required
            assert exercise.rir_min >= 2
            assert exercise.rir_max <= 4

        select_current_workout_plan(102)

    for index in range(2, len(plan_name_lists)):
        assert not (
            plan_name_lists[index]
            == plan_name_lists[index - 1]
            == plan_name_lists[index - 2]
        )

    assert len(distinct_exercises) >= 15
    assert len(equipment_modalities) >= 5
    assert len(set(plan_name_lists[-3:])) > 1


def _approved_fallback_title(context):
    fallback = approve_candidate_workout_plan(
        generate_candidate_workout_plan(context),
        context,
    )
    return fallback.title


_LIGHTWEIGHT_CATALOG = {
    "Goblet Squat": ExerciseCatalogEntry(
        1,
        "Goblet Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["dumbbell"],
        "beginner",
    ),
    "Dumbbell Bench Press": ExerciseCatalogEntry(
        2,
        "Dumbbell Bench Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    "Barbell Squat": ExerciseCatalogEntry(
        3,
        "Barbell Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    "Leg Press": ExerciseCatalogEntry(
        4,
        "Leg Press",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["machine"],
        "beginner",
    ),
}


def _patch_lightweight_catalog(monkeypatch):
    def fake_find_catalog_entry_by_name(name: str):
        return _LIGHTWEIGHT_CATALOG.get(name)

    monkeypatch.setattr(
        "services.workout_plan_service.find_catalog_entry_by_name",
        fake_find_catalog_entry_by_name,
    )


def _lightweight_workout_context(
    *,
    scenario: str = "aligned_managed",
    available_equipment: list[str] | None = None,
    unavailable_equipment: list[str] | None = None,
    rir_min: int = 2,
    rir_max: int = 4,
) -> WorkoutContext:
    return WorkoutContext(
        user_id=999,
        scenario=scenario,
        primary_goal="strength_and_recomposition",
        training_load="moderate",
        recovery_demand="normal",
        avg_rir=2.5,
        workout_count=4,
        training_constraints=TrainingConstraints(
            recommended_rir_min=rir_min,
            recommended_rir_max=rir_max,
            low_rir_guidance="Keep most working sets controlled.",
            progression_guidance="Progress gradually when recovery is stable.",
            recovery_constraint="normal",
            confidence="Moderate",
            reason_codes=["unit_test_training_constraints"],
        ),
        workout_constraints=WorkoutConstraints(
            available_equipment=available_equipment
            or [
                "bodyweight",
                "dumbbell",
                "adjustable_bench",
                "barbell",
                "rack",
                "plates",
            ],
            unavailable_equipment=unavailable_equipment or ["machine"],
            confidence="Moderate",
            reason_codes=["unit_test_workout_constraints"],
        ),
        confidence="Moderate",
        reason_codes=["unit_test_context"],
    )


def _candidate_payload_for_entry(
    entry_name: str,
    *,
    title: str = "CrewAI Candidate Strength Session",
    notes: str = "Keep reps controlled and leave room in reserve.",
    progression_guidance: str = "Progress only when recovery and performance stay stable.",
    confidence: str = "Moderate",
) -> dict:
    selected_names = []
    for name in [entry_name, "Goblet Squat", "Dumbbell Bench Press", "Barbell Squat"]:
        if name not in selected_names:
            selected_names.append(name)
        if len(selected_names) == 3:
            break

    exercises = []
    for index, name in enumerate(selected_names):
        entry = _LIGHTWEIGHT_CATALOG[name]
        assert entry.id is not None
        exercises.append(
            {
                "exercise_name": entry.name,
                "catalog_exercise_id": entry.id,
                "movement_pattern": entry.movement_pattern,
                "target_zone": "main" if index == 0 else "accessory",
                "sets": 3,
                "reps_min": 8,
                "reps_max": 10,
                "target_rir_min": 2,
                "target_rir_max": 3,
                "required_equipment": entry.equipment_required,
                "notes": notes,
            }
        )

    return {
        "title": title,
        "session_focus": "Use a controlled strength session.",
        "duration_minutes": 45,
        "warmup": "Use easy movement and ramp-up sets before work sets.",
        "exercises": exercises,
        "cooldown": "Log performance, soreness, and energy after training.",
        "progression_guidance": progression_guidance,
        "rationale": "This plan stays within today's training limits.",
        "confidence": confidence,
    }


def _context_for_user_102_home_gym(tmp_path, monkeypatch):
    _seeded_health_states(tmp_path, monkeypatch)
    save_equipment_profile(
        user_id=102,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    return build_workout_context(build_user_health_state(102))


def test_candidate_workout_plan_json_parses_and_approves(monkeypatch):
    _patch_lightweight_catalog(monkeypatch)
    context = _lightweight_workout_context()
    raw_output = json.dumps(_candidate_payload_for_entry("Goblet Squat"))

    candidate = parse_candidate_workout_plan_json(raw_output)
    approved = approve_candidate_workout_plan(candidate, context)

    assert candidate.title == "CrewAI Candidate Strength Session"
    assert approved.title == "CrewAI Candidate Strength Session"
    assert approved.exercises[0].name == "Goblet Squat"
    assert approved.exercises[0].equipment_required == ["dumbbell"]


def test_malformed_candidate_json_is_rejected_without_full_fallback():
    with pytest.raises(WorkoutCandidateParseError):
        parse_candidate_workout_plan_json("not-json")


def test_markdown_wrapped_candidate_json_is_rejected_without_full_fallback():
    raw_output = (
        "```json\n" + json.dumps(_candidate_payload_for_entry("Goblet Squat")) + "\n```"
    )

    with pytest.raises(WorkoutCandidateParseError):
        parse_candidate_workout_plan_json(raw_output)


def test_candidate_missing_required_field_is_rejected_without_full_fallback():
    payload = _candidate_payload_for_entry("Goblet Squat")
    payload.pop("rationale")

    with pytest.raises(WorkoutCandidateParseError):
        parse_candidate_workout_plan_json(json.dumps(payload))


def test_candidate_extra_field_is_rejected_under_strict_parsing():
    payload = _candidate_payload_for_entry("Goblet Squat")
    payload["debug_reason_codes"] = ["not_allowed"]

    with pytest.raises(WorkoutCandidateParseError):
        parse_candidate_workout_plan_json(json.dumps(payload))


def test_candidate_wrapped_in_workout_plan_is_rejected_under_strict_parsing():
    payload = {"workout_plan": [_candidate_payload_for_entry("Goblet Squat")]}

    with pytest.raises(WorkoutCandidateParseError):
        parse_candidate_workout_plan_json(json.dumps(payload))


@pytest.mark.parametrize(
    "bad_key, replacement_value, removed_keys",
    [
        ("equipment", ["dumbbell"], ["required_equipment"]),
        ("reps", "8-10", ["reps_min", "reps_max"]),
        ("rir_target", 3, ["target_rir_min", "target_rir_max"]),
    ],
)
def test_candidate_wrong_exercise_schema_keys_are_rejected_under_strict_parsing(
    bad_key, replacement_value, removed_keys
):
    payload = _candidate_payload_for_entry("Goblet Squat")
    exercise = payload["exercises"][0]
    for key in removed_keys:
        exercise.pop(key)
    exercise[bad_key] = replacement_value

    with pytest.raises(WorkoutCandidateParseError):
        parse_candidate_workout_plan_json(json.dumps(payload))


def test_candidate_invalid_confidence_is_rejected_without_full_fallback():
    payload = _candidate_payload_for_entry("Goblet Squat")
    payload["confidence"] = "Pretty Good"

    with pytest.raises(WorkoutCandidateParseError):
        parse_candidate_workout_plan_json(json.dumps(payload))


def test_malformed_candidate_output_falls_back_deterministically(tmp_path, monkeypatch):
    context = _context_for_user_102_home_gym(tmp_path, monkeypatch)

    approved = build_approved_workout_plan_from_candidate_output(
        "not-json",
        context,
    )

    assert approved.title == _approved_fallback_title(context)


def test_unknown_catalog_exercise_candidate_is_rejected_by_validator(monkeypatch):
    _patch_lightweight_catalog(monkeypatch)
    context = _lightweight_workout_context()
    payload = _candidate_payload_for_entry("Goblet Squat")
    payload["exercises"][0]["exercise_name"] = "Imaginary Cable Machine Squat"
    payload["exercises"][0]["catalog_exercise_id"] = None
    candidate = parse_candidate_workout_plan_json(json.dumps(payload))

    violations = validate_candidate_workout_plan(candidate, context)

    assert any("exercise catalog" in violation for violation in violations)


def test_catalog_exercise_id_name_mismatch_is_rejected_by_validator(monkeypatch):
    _patch_lightweight_catalog(monkeypatch)
    context = _lightweight_workout_context()
    payload = _candidate_payload_for_entry("Goblet Squat")
    payload["exercises"][0]["catalog_exercise_id"] = _LIGHTWEIGHT_CATALOG[
        "Dumbbell Bench Press"
    ].id
    candidate = parse_candidate_workout_plan_json(json.dumps(payload))

    violations = validate_candidate_workout_plan(candidate, context)

    assert any("catalog_exercise_id" in violation for violation in violations)


def test_unavailable_equipment_candidate_is_rejected_by_validator(monkeypatch):
    _patch_lightweight_catalog(monkeypatch)
    context = _lightweight_workout_context(
        available_equipment=["bodyweight", "dumbbell"],
        unavailable_equipment=["barbell", "machine", "cable", "pull_up_bar"],
    )
    candidate = parse_candidate_workout_plan_json(
        json.dumps(_candidate_payload_for_entry("Barbell Squat"))
    )

    violations = validate_candidate_workout_plan(candidate, context)

    assert any("equipment" in violation.lower() for violation in violations)


def test_machine_candidate_is_rejected_when_machine_unavailable(monkeypatch):
    _patch_lightweight_catalog(monkeypatch)
    context = _lightweight_workout_context(
        available_equipment=["bodyweight", "dumbbell"],
        unavailable_equipment=["machine"],
    )
    candidate = parse_candidate_workout_plan_json(
        json.dumps(_candidate_payload_for_entry("Leg Press"))
    )

    violations = validate_candidate_workout_plan(candidate, context)

    assert any("equipment" in violation.lower() for violation in violations)


def test_candidate_rir_outside_training_constraints_is_rejected(monkeypatch):
    _patch_lightweight_catalog(monkeypatch)
    context = _lightweight_workout_context(rir_min=2, rir_max=4)
    payload = _candidate_payload_for_entry("Goblet Squat")
    payload["exercises"][0]["target_rir_min"] = 0
    payload["exercises"][0]["target_rir_max"] = 1
    candidate = parse_candidate_workout_plan_json(json.dumps(payload))

    violations = validate_candidate_workout_plan(candidate, context)

    assert any("RIR" in violation for violation in violations)


def test_recovery_limited_max_effort_candidate_is_rejected(monkeypatch):
    _patch_lightweight_catalog(monkeypatch)
    context = _lightweight_workout_context(
        scenario="recovery_limited", rir_min=2, rir_max=3
    )
    payload = _candidate_payload_for_entry(
        "Goblet Squat",
        notes="Use max effort sets to failure.",
    )
    candidate = parse_candidate_workout_plan_json(json.dumps(payload))

    violations = validate_candidate_workout_plan(candidate, context)

    assert any("max-effort" in violation for violation in violations)


def test_data_quality_limited_overtraining_candidate_is_rejected(monkeypatch):
    _patch_lightweight_catalog(monkeypatch)
    context = _lightweight_workout_context(scenario="data_quality_limited")
    payload = _candidate_payload_for_entry(
        "Goblet Squat",
        notes="This avoids overtraining and stalled progress.",
    )
    candidate = parse_candidate_workout_plan_json(json.dumps(payload))

    violations = validate_candidate_workout_plan(candidate, context)

    assert any("overconfident" in violation for violation in violations)


def test_automatic_load_increase_candidate_is_rejected(monkeypatch):
    _patch_lightweight_catalog(monkeypatch)
    context = _lightweight_workout_context()
    payload = _candidate_payload_for_entry(
        "Goblet Squat",
        progression_guidance="Use an automatic load increase every session.",
    )
    candidate = parse_candidate_workout_plan_json(json.dumps(payload))

    violations = validate_candidate_workout_plan(candidate, context)

    assert any("forbidden workout guidance" in violation for violation in violations)


def _provider_payload_from_candidate(candidate) -> dict:
    exercises = []
    for exercise in candidate.exercises:
        entry = find_catalog_entry_by_name(exercise.name)
        assert entry is not None
        exercises.append(
            {
                "exercise_name": entry.name,
                "catalog_exercise_id": entry.id,
                "movement_pattern": entry.movement_pattern,
                "target_zone": exercise.target_zone or "main",
                "sets": exercise.sets,
                "reps_min": exercise.reps_min,
                "reps_max": exercise.reps_max,
                "target_rir_min": exercise.rir_min,
                "target_rir_max": exercise.rir_max,
                "required_equipment": entry.equipment_required,
                "notes": exercise.notes,
            }
        )

    return {
        "title": candidate.title,
        "session_focus": candidate.session_focus,
        "duration_minutes": candidate.duration_minutes,
        "warmup": candidate.warmup,
        "exercises": exercises,
        "cooldown": candidate.cooldown,
        "progression_guidance": candidate.progression_guidance,
        "rationale": candidate.rationale,
        "confidence": candidate.confidence,
    }


def _valid_provider_json_for_context(context: WorkoutContext) -> str:
    candidate = generate_candidate_workout_plan(context)
    return json.dumps(_provider_payload_from_candidate(candidate))


def test_workout_context_to_llm_json_is_bounded_and_safe(tmp_path, monkeypatch):
    context = _context_for_user_102_home_gym(tmp_path, monkeypatch)

    payload = workout_context_to_llm_json(context)

    assert payload["scenario"] == "aligned_managed"
    assert payload["allowed_rir_range"]["target_rir_min"] >= 0
    assert payload["exercise_count"] == {"min": 3, "target": 4, "max": 5}
    assert payload["duration_minutes"] == {"min": 30, "target": 45, "max": 60}
    assert payload["available_equipment"]
    assert payload["allowed_exercises"]
    assert 8 <= len(payload["allowed_exercises"]) <= 12
    assert payload["execution_summary"]
    assert payload["movement_pattern_targets"]
    assert payload["safety_constraints"]
    assert payload["required_top_level_keys"] == [
        "title",
        "session_focus",
        "duration_minutes",
        "exercises",
        "warmup",
        "cooldown",
        "progression_guidance",
        "rationale",
        "confidence",
    ]
    assert "training_constraints" not in payload
    assert "workout_constraints" not in payload
    assert "reason_codes" not in payload
    assert "raw_actual_set_rows" not in payload
    assert "actual_sets" not in payload
    assert all("notes" not in exercise for exercise in payload["allowed_exercises"])
    assert all(
        set(exercise)
        == {
            "catalog_exercise_id",
            "exercise_name",
            "movement_pattern",
            "required_equipment",
            "target_zone",
        }
        for exercise in payload["allowed_exercises"]
    )


def test_workout_context_to_llm_json_is_compact(tmp_path, monkeypatch):
    context = _context_for_user_102_home_gym(tmp_path, monkeypatch)

    payload = workout_context_to_llm_json(context)
    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    assert len(serialized) < 6500
    assert len(payload["allowed_exercises"]) <= 12
    assert "training_execution_summary" not in payload
    assert "recent_exercises" not in payload


def test_crewai_workout_prompt_requires_raw_json_only(tmp_path, monkeypatch):
    context = _context_for_user_102_home_gym(tmp_path, monkeypatch)

    prompt = build_crewai_candidate_workout_plan_prompt(context)

    assert "raw JSON object only" in prompt
    assert "no_think" in prompt.lower()
    assert "Do not think aloud" in prompt
    assert "markdown" in prompt.lower()
    assert "allowed_exercises" in prompt
    assert "automatic load increase" in prompt
    assert "Use this exact top-level key set only" in prompt
    assert "Never use these top-level wrapper keys" in prompt
    assert "workout_plan, plan, response, result, data" in prompt
    assert "Each exercise must use this exact key set only" in prompt
    assert "Never use these exercise keys" in prompt
    assert "equipment, reps, rir_target, rir, exercise, name" in prompt
    assert "Choose only from allowed_exercises" in prompt
    assert "training_constraints" not in prompt
    assert "workout_constraints" not in prompt
    assert "reason_codes" not in prompt


def test_crewai_workout_llm_kwargs_disable_thinking_by_default(monkeypatch):
    monkeypatch.delenv("CREWAI_WORKOUT_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("CREWAI_WORKOUT_DISABLE_THINKING", raising=False)
    monkeypatch.delenv("CREWAI_WORKOUT_JSON_RESPONSE_FORMAT", raising=False)

    llm_kwargs = _crewai_workout_llm_kwargs()

    assert llm_kwargs["model"] == "ollama/qwen3:8b"
    assert llm_kwargs["base_url"] == "http://localhost:11434"
    assert llm_kwargs["temperature"] == 0
    assert llm_kwargs["response_format"] == {"type": "json_object"}
    assert llm_kwargs["think"] is False
    assert llm_kwargs["options"] == {"think": False}
    assert llm_kwargs["extra_body"] == {
        "think": False,
        "options": {"think": False},
    }
    assert llm_kwargs["additional_params"] == {
        "think": False,
        "options": {"think": False},
    }


def test_crewai_workout_llm_kwargs_allow_no_think_disable_override(monkeypatch):
    monkeypatch.setenv("CREWAI_WORKOUT_MODEL", "ollama/qwen3:8b")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://windows-host:11434")
    monkeypatch.setenv("CREWAI_WORKOUT_DISABLE_THINKING", "false")
    monkeypatch.setenv("CREWAI_WORKOUT_JSON_RESPONSE_FORMAT", "false")

    llm_kwargs = _crewai_workout_llm_kwargs()

    assert llm_kwargs == {
        "model": "ollama/qwen3:8b",
        "base_url": "http://windows-host:11434",
        "temperature": 0,
    }


def test_configured_workout_provider_defaults_to_deterministic(tmp_path, monkeypatch):
    monkeypatch.delenv("WORKOUT_CANDIDATE_PROVIDER", raising=False)
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.approved_workout_plan.exercises
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.crewai_attempted is False
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.final_plan_source == "deterministic"


def test_mocked_crewai_workout_provider_valid_json_approves(tmp_path, monkeypatch):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    raw_json = _valid_provider_json_for_context(context)

    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_candidate_workout_plan_json",
        lambda provided_context: raw_json,
    )

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.runtime_metadata.selected_provider == "crewai"
    assert result.runtime_metadata.crewai_attempted is True
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "success"
    assert result.runtime_metadata.final_plan_source == "crewai_approved"


def test_mocked_crewai_workout_provider_malformed_json_falls_back(
    tmp_path, monkeypatch
):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]

    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_candidate_workout_plan_json",
        lambda provided_context: "not-json",
    )

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.approved_workout_plan.exercises
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "malformed_json"
    assert result.runtime_metadata.candidate_parse_status == "failed"
    assert result.runtime_metadata.final_plan_source == "deterministic_fallback"


def test_mocked_crewai_workout_provider_thinking_prefixed_output_falls_back(
    tmp_path, monkeypatch
):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    raw_json = _valid_provider_json_for_context(context)

    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_candidate_workout_plan_json",
        lambda provided_context: (
            "_numpy <think> I should reason about the plan first. " + raw_json
        ),
    )

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.approved_workout_plan.exercises
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "malformed_json"
    assert result.runtime_metadata.candidate_parse_status == "failed"
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"
    assert result.runtime_metadata.final_plan_source == "deterministic_fallback"
    assert result.runtime_metadata.raw_output_preview_truncated.startswith(
        "_numpy <think>"
    )


def test_mocked_crewai_workout_provider_markdown_json_falls_back(tmp_path, monkeypatch):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    raw_json = _valid_provider_json_for_context(context)

    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_candidate_workout_plan_json",
        lambda provided_context: f"```json\n{raw_json}\n```",
    )

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.markdown_wrapper_detected is True
    assert result.runtime_metadata.candidate_parse_status == "failed"


def test_mocked_crewai_workout_provider_extra_fields_fall_back(tmp_path, monkeypatch):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    payload = json.loads(_valid_provider_json_for_context(context))
    payload["debug_reason_codes"] = ["not_allowed"]

    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_candidate_workout_plan_json",
        lambda provided_context: json.dumps(payload),
    )

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "schema_mismatch"
    assert result.runtime_metadata.candidate_parse_status == "failed"


def test_mocked_crewai_workout_provider_missing_fields_fall_back(tmp_path, monkeypatch):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    payload = json.loads(_valid_provider_json_for_context(context))
    payload.pop("rationale")

    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_candidate_workout_plan_json",
        lambda provided_context: json.dumps(payload),
    )

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "schema_mismatch"


def test_mocked_crewai_workout_provider_wrapped_workout_plan_falls_back(
    tmp_path, monkeypatch
):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    payload = json.loads(_valid_provider_json_for_context(context))
    wrapped_payload = {"workout_plan": payload["exercises"]}

    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_candidate_workout_plan_json",
        lambda provided_context: json.dumps(wrapped_payload),
    )

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "schema_mismatch"
    assert result.runtime_metadata.candidate_parse_status == "failed"
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"
    assert result.runtime_metadata.final_plan_source == "deterministic_fallback"


@pytest.mark.parametrize(
    "bad_key, replacement_value, removed_keys",
    [
        ("equipment", ["dumbbell"], ["required_equipment"]),
        ("reps", "8-10", ["reps_min", "reps_max"]),
        ("rir_target", 3, ["target_rir_min", "target_rir_max"]),
    ],
)
def test_mocked_crewai_workout_provider_wrong_exercise_schema_keys_fall_back(
    tmp_path, monkeypatch, bad_key, replacement_value, removed_keys
):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    payload = json.loads(_valid_provider_json_for_context(context))
    exercise = payload["exercises"][0]
    for key in removed_keys:
        exercise.pop(key)
    exercise[bad_key] = replacement_value

    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_candidate_workout_plan_json",
        lambda provided_context: json.dumps(payload),
    )

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "schema_mismatch"
    assert result.runtime_metadata.candidate_parse_status == "failed"
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"


def test_mocked_crewai_aligned_managed_deload_candidate_falls_back(
    tmp_path, monkeypatch
):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    payload = json.loads(_valid_provider_json_for_context(context))
    payload["progression_guidance"] = (
        "Deload and reduce intensity despite stable recovery."
    )

    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_candidate_workout_plan_json",
        lambda provided_context: json.dumps(payload),
    )

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "validation_failure"
    assert any(
        "intervention" in violation.lower()
        for violation in result.runtime_metadata.validation_errors
    )


def test_mocked_crewai_workout_provider_unsafe_candidate_falls_back(
    tmp_path, monkeypatch
):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[105]
    context = build_workout_context(health_state)
    payload = json.loads(_valid_provider_json_for_context(context))
    payload["progression_guidance"] = "This prevents overtraining and stalled progress."

    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_candidate_workout_plan_json",
        lambda provided_context: json.dumps(payload),
    )

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "validation_failure"
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "failed"


def test_mocked_crewai_workout_provider_confidence_above_context_falls_back(
    tmp_path, monkeypatch
):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[105]
    context = build_workout_context(health_state)
    payload = json.loads(_valid_provider_json_for_context(context))
    payload["confidence"] = "High"

    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_candidate_workout_plan_json",
        lambda provided_context: json.dumps(payload),
    )

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "validation_failure"
    assert any(
        "confidence" in violation.lower()
        for violation in result.runtime_metadata.validation_errors
    )


def test_workout_candidate_provider_exception_falls_back(tmp_path, monkeypatch):
    context = _context_for_user_102_home_gym(tmp_path, monkeypatch)

    def broken_provider(provided_context):
        raise RuntimeError("provider exploded")

    result = approve_workout_candidate_provider_or_fallback_with_metadata(
        broken_provider,
        context,
    )

    assert result.approved_workout_plan.exercises
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "provider_exception"
    assert result.runtime_metadata.candidate_parse_status == "not_attempted"


def test_workout_candidate_provider_non_string_output_falls_back(tmp_path, monkeypatch):
    context = _context_for_user_102_home_gym(tmp_path, monkeypatch)

    result = approve_workout_candidate_provider_or_fallback_with_metadata(
        lambda provided_context: {"not": "a string"},
        context,
    )

    assert result.approved_workout_plan.exercises
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "provider_non_string_output"
    assert result.runtime_metadata.candidate_parse_status == "not_attempted"


def test_workout_preview_debug_endpoint_returns_runtime_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "deterministic")

    client = TestClient(app)
    response = client.get("/workout-plans/preview/105/debug")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 105
    assert payload["approved_workout_plan"]["exercises"]
    assert payload["runtime_metadata"]["selected_provider"] == "deterministic"
    assert payload["runtime_metadata"]["crewai_attempted"] is False


def test_normal_workout_preview_response_shape_does_not_expose_runtime_metadata(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "crewai")

    client = TestClient(app)
    response = client.get("/workout-plans/preview/105")

    assert response.status_code == 200
    payload = response.json()
    assert "runtime_metadata" not in payload
    assert set(payload) == {
        "success",
        "user_id",
        "scenario",
        "confidence",
        "training_constraints",
        "workout_constraints",
        "approved_workout_plan",
        "rendered_workout_plan",
    }


def test_invalid_workout_candidate_provider_falls_back_to_deterministic(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("WORKOUT_CANDIDATE_PROVIDER", "banana")
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]

    result = build_configured_approved_workout_plan_with_metadata(health_state)

    assert result.approved_workout_plan.exercises
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "invalid_provider"


def _valid_explanation_payload(
    *, confidence: str = "Moderate", focus_cue: str | None = None
) -> dict:
    return {
        "session_summary": "This is a controlled strength session based on today's approved plan.",
        "why_this_fits_today": "It matches the current equipment and training context without adding unnecessary stress.",
        "focus_cue": focus_cue
        or "Keep execution clean and log effort honestly after the session.",
        "recovery_context": "The plan supports consistency while respecting current recovery signals.",
        "nutrition_or_logging_context": "Clear logging today will make the next recommendation more useful.",
        "confidence": confidence,
    }


def _lightweight_approved_plan(monkeypatch):
    _patch_lightweight_catalog(monkeypatch)
    context = _lightweight_workout_context()
    candidate = parse_candidate_workout_plan_json(
        json.dumps(_candidate_payload_for_entry("Goblet Squat"))
    )
    approved_plan = approve_candidate_workout_plan(candidate, context)
    return approved_plan, context


def test_candidate_workout_explanation_json_parses_and_approves(monkeypatch):
    approved_plan, context = _lightweight_approved_plan(monkeypatch)
    raw_output = json.dumps(_valid_explanation_payload())

    candidate = parse_candidate_workout_explanation_json(raw_output)
    approved = approve_candidate_workout_explanation(candidate, approved_plan, context)

    assert approved.session_summary.startswith("This is a controlled")
    assert approved.confidence == "Moderate"


def test_candidate_workout_explanation_rejects_markdown(monkeypatch):
    _lightweight_approved_plan(monkeypatch)
    raw_output = "```json\n" + json.dumps(_valid_explanation_payload()) + "\n```"

    with pytest.raises(WorkoutCandidateParseError):
        parse_candidate_workout_explanation_json(raw_output)


def test_candidate_workout_explanation_rejects_extra_fields(monkeypatch):
    _lightweight_approved_plan(monkeypatch)
    payload = _valid_explanation_payload()
    payload["exercise_changes"] = ["not allowed"]

    with pytest.raises(WorkoutCandidateParseError):
        parse_candidate_workout_explanation_json(json.dumps(payload))


def test_workout_explanation_validator_rejects_plan_changes(monkeypatch):
    approved_plan, context = _lightweight_approved_plan(monkeypatch)
    candidate = parse_candidate_workout_explanation_json(
        json.dumps(
            _valid_explanation_payload(
                focus_cue="Ignore the approved plan and swap the exercise today."
            )
        )
    )

    violations = validate_candidate_workout_explanation(
        candidate, approved_plan, context
    )

    assert any(
        "forbidden" in violation.lower() or "change" in violation.lower()
        for violation in violations
    )


def test_workout_explanation_validator_rejects_unsafe_claims(monkeypatch):
    approved_plan, context = _lightweight_approved_plan(monkeypatch)
    candidate = parse_candidate_workout_explanation_json(
        json.dumps(
            _valid_explanation_payload(
                focus_cue="This prevents overtraining and stalled progress."
            )
        )
    )

    violations = validate_candidate_workout_explanation(
        candidate, approved_plan, context
    )

    assert any("forbidden" in violation.lower() for violation in violations)


def test_deterministic_workout_explanation_preserves_approved_plan(monkeypatch):
    approved_plan, context = _lightweight_approved_plan(monkeypatch)
    before = asdict(approved_plan)

    explanation = build_deterministic_workout_explanation(approved_plan, context)

    assert asdict(approved_plan) == before
    assert explanation.session_summary
    assert explanation.confidence == approved_plan.confidence


def test_crewai_workout_explanation_prompt_is_secondary_to_plan(monkeypatch):
    approved_plan, context = _lightweight_approved_plan(monkeypatch)

    prompt = build_crewai_workout_explanation_prompt(approved_plan, context)

    assert "Explain the already-approved workout plan" in prompt
    assert "Do not change the plan" in prompt
    assert "session_summary" in prompt
    assert "No markdown" in prompt
    assert (
        "exercises"
        not in prompt.split("Use this exact key set only:", 1)[1].split(
            "Each field", 1
        )[0]
    )


def test_mocked_crewai_workout_explanation_valid_json_approves(tmp_path, monkeypatch):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    approved_plan = build_approved_workout_plan(health_state)

    result = approve_workout_explanation_provider_or_fallback_with_metadata(
        lambda provided_plan, provided_context: json.dumps(
            _valid_explanation_payload()
        ),
        approved_plan,
        context,
    )

    assert result.runtime_metadata.crewai_attempted is True
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "success"
    assert result.runtime_metadata.final_explanation_source == "crewai_approved"


def test_mocked_crewai_workout_explanation_malformed_json_falls_back(
    tmp_path, monkeypatch
):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    approved_plan = build_approved_workout_plan(health_state)

    result = approve_workout_explanation_provider_or_fallback_with_metadata(
        lambda provided_plan, provided_context: "not-json",
        approved_plan,
        context,
    )

    assert result.approved_workout_explanation.session_summary
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "malformed_json"
    assert result.runtime_metadata.candidate_parse_status == "failed"


def test_mocked_crewai_workout_explanation_provider_exception_is_diagnostic(
    tmp_path, monkeypatch
):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    approved_plan = build_approved_workout_plan(health_state)
    long_message = "No module named 'crewai_tools' " + ("x" * 500)

    def broken_provider(provided_plan, provided_context):
        raise ImportError(long_message)

    result = approve_workout_explanation_provider_or_fallback_with_metadata(
        broken_provider,
        approved_plan,
        context,
    )

    assert result.approved_workout_explanation.session_summary
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "provider_exception"
    assert result.runtime_metadata.candidate_parse_status == "not_attempted"
    assert result.runtime_metadata.candidate_validation_status == "not_attempted"
    assert len(result.runtime_metadata.validation_errors) == 1
    error = result.runtime_metadata.validation_errors[0]
    assert error.startswith("ImportError: No module named 'crewai_tools'")
    assert len(error) <= len("ImportError: ") + 300


def test_mocked_crewai_workout_explanation_unsafe_copy_falls_back(
    tmp_path, monkeypatch
):
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    approved_plan = build_approved_workout_plan(health_state)

    result = approve_workout_explanation_provider_or_fallback_with_metadata(
        lambda provided_plan, provided_context: json.dumps(
            _valid_explanation_payload(
                focus_cue="Use an automatic deload because progress has stalled."
            )
        ),
        approved_plan,
        context,
    )

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "validation_failure"
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "failed"


def test_configured_workout_explanation_defaults_to_deterministic(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("WORKOUT_EXPLANATION_PROVIDER", raising=False)
    health_state = _seeded_health_states(tmp_path, monkeypatch)[102]
    context = build_workout_context(health_state)
    approved_plan = build_approved_workout_plan(health_state)

    result = build_configured_workout_explanation_with_metadata(approved_plan, context)

    assert result.approved_workout_explanation.session_summary
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.crewai_attempted is False
    assert result.runtime_metadata.fallback_used is False


def test_workout_explanation_debug_endpoint_returns_debug_only_metadata(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    monkeypatch.setenv("WORKOUT_EXPLANATION_PROVIDER", "deterministic")

    client = TestClient(app)
    response = client.get("/workout-plans/preview/102/explanation/debug")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["approved_workout_plan"]["exercises"]
    assert payload["approved_workout_explanation"]["session_summary"]
    assert (
        payload["explanation_runtime_metadata"]["selected_provider"] == "deterministic"
    )
    assert payload["explanation_runtime_metadata"]["crewai_attempted"] is False


def test_normal_workout_preview_response_shape_does_not_expose_explanation(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    client = TestClient(app)
    response = client.get("/workout-plans/preview/102")

    assert response.status_code == 200
    payload = response.json()
    assert "approved_workout_explanation" not in payload
    assert "explanation_runtime_metadata" not in payload


def test_public_workout_explanation_endpoint_returns_approved_explanation(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    monkeypatch.setenv("WORKOUT_EXPLANATION_PROVIDER", "deterministic")

    client = TestClient(app)
    response = client.get("/workout-plans/preview/102/explanation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 102
    assert payload["scenario"] == "aligned_managed"
    assert payload["approved_workout_explanation"]["session_summary"]
    assert "approved_workout_plan" not in payload
    assert "explanation_runtime_metadata" not in payload
    assert "runtime_metadata" not in payload
    assert "raw_output" not in payload


def test_public_workout_explanation_endpoint_uses_mocked_crewai_when_valid(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    monkeypatch.setenv("WORKOUT_EXPLANATION_PROVIDER", "crewai")

    payload = _valid_explanation_payload()
    payload["session_summary"] = "This is a controlled CrewAI-approved explanation."

    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_workout_explanation_json",
        lambda approved_plan, context: json.dumps(payload),
    )

    client = TestClient(app)
    response = client.get("/workout-plans/preview/102/explanation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["approved_workout_explanation"]["session_summary"].startswith(
        "This is a controlled"
    )
    assert "explanation_runtime_metadata" not in payload
    assert "approved_workout_plan" not in payload


def test_public_workout_explanation_endpoint_falls_back_on_malformed_crewai(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    monkeypatch.setenv("WORKOUT_EXPLANATION_PROVIDER", "crewai")
    monkeypatch.setattr(
        workout_plan_service,
        "generate_crewai_workout_explanation_json",
        lambda provided_plan, provided_context: "not-json",
    )

    client = TestClient(app)
    response = client.get("/workout-plans/preview/102/explanation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["approved_workout_explanation"]["session_summary"]
    assert "explanation_runtime_metadata" not in payload
    assert "runtime_metadata" not in payload


def _completed_workout_execution(tmp_path, monkeypatch) -> tuple[int, int]:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    selected = select_current_workout_plan(102)
    plan_instance_id = selected["workout_plan_instance"].id
    started = start_selected_workout_plan(plan_instance_id)

    for exercise in started["planned_exercises"]:
        for set_number in range(1, exercise.sets + 1):
            log_actual_set(
                plan_instance_id,
                {
                    "planned_workout_exercise_id": exercise.id,
                    "exercise_name": exercise.name,
                    "set_number": set_number,
                    "actual_reps": exercise.reps_min,
                    "actual_weight": 25,
                    "actual_rir": exercise.rir_min,
                    "completed": True,
                    "skipped": False,
                },
            )

    completed = complete_workout_plan(plan_instance_id)
    return completed["execution_session"].id, plan_instance_id


def _valid_post_workout_review_payload(
    *, confidence: str = "Low", next_time_focus: str | None = None
) -> dict:
    return {
        "session_summary": "You completed the approved workout and logged enough detail to review it.",
        "completion_reflection": "Most of the planned work was completed, and any differences are useful session context.",
        "effort_reflection": "Logged effort stayed close to the planned RIR range.",
        "reps_or_volume_reflection": "Completed sets and reps mostly matched the approved plan.",
        "substitutions_or_skips_context": "No major substitution pattern needs emphasis from this session.",
        "logging_quality_note": "Set-level logging was complete enough for a useful review.",
        "next_time_focus": next_time_focus
        or "For the next logged session, keep reps, weight, and RIR as complete as possible.",
        "confidence": confidence,
    }


def test_post_workout_review_context_uses_completed_summary(tmp_path, monkeypatch):
    execution_id, plan_instance_id = _completed_workout_execution(tmp_path, monkeypatch)

    context = build_post_workout_review_context(execution_id)

    assert context.execution_id == execution_id
    assert context.plan_instance_id == plan_instance_id
    assert context.completion_status == "completed"
    assert context.completed_sets == context.planned_sets
    assert context.approved_workout_plan.exercises
    assert (
        context.planned_vs_actual_summary.completed_set_count == context.completed_sets
    )


def test_candidate_post_workout_review_json_parses_and_approves(tmp_path, monkeypatch):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )
    context = build_post_workout_review_context(execution_id)

    candidate = parse_candidate_post_workout_review_summary_json(
        json.dumps(_valid_post_workout_review_payload())
    )
    approved = approve_candidate_post_workout_review_summary(candidate, context)

    assert approved.session_summary.startswith("You completed")
    assert approved.confidence == "Low"


def test_candidate_post_workout_review_rejects_markdown(tmp_path, monkeypatch):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )
    build_post_workout_review_context(execution_id)
    raw_output = (
        "```json\n" + json.dumps(_valid_post_workout_review_payload()) + "\n```"
    )

    with pytest.raises(WorkoutCandidateParseError):
        parse_candidate_post_workout_review_summary_json(raw_output)


def test_post_workout_review_validator_rejects_unsafe_programming(
    tmp_path, monkeypatch
):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )
    context = build_post_workout_review_context(execution_id)
    candidate = parse_candidate_post_workout_review_summary_json(
        json.dumps(
            _valid_post_workout_review_payload(
                next_time_focus="Next workout should add weight automatically."
            )
        )
    )

    violations = validate_candidate_post_workout_review_summary(candidate, context)

    assert any("programming" in violation.lower() for violation in violations)


def test_configured_post_workout_review_defaults_to_deterministic(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("POST_WORKOUT_REVIEW_PROVIDER", raising=False)
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )

    result = build_configured_post_workout_review_summary_with_metadata(execution_id)

    assert result.approved_post_workout_review_summary.session_summary
    assert result.runtime_metadata.selected_provider == "deterministic"
    assert result.runtime_metadata.crewai_attempted is False
    assert result.runtime_metadata.fallback_used is False


def test_deterministic_post_workout_review_copy_uses_session_counts(
    tmp_path, monkeypatch
):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )

    result = build_configured_post_workout_review_summary_with_metadata(execution_id)
    review = result.approved_post_workout_review_summary

    assert "planned sets" in review.session_summary
    assert "failure" not in review.completion_reflection.lower()
    assert "policy" not in review.completion_reflection.lower()


def _post_workout_context_with_set_counts(
    tmp_path,
    monkeypatch,
    *,
    planned_sets: int,
    completed_sets: int,
    skipped_exercises: int = 0,
    substitutions: int = 0,
):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )
    context = build_post_workout_review_context(execution_id)
    context.planned_sets = planned_sets
    context.completed_sets = completed_sets
    context.skipped_exercise_count = skipped_exercises
    context.substitution_count = substitutions
    context.planned_vs_actual_summary.planned_set_count = planned_sets
    context.planned_vs_actual_summary.completed_set_count = completed_sets
    context.planned_vs_actual_summary.skipped_exercise_count = skipped_exercises
    context.planned_vs_actual_summary.substituted_exercise_count = substitutions
    context.planned_vs_actual_summary.completion_percentage = (
        (completed_sets / planned_sets) * 100 if planned_sets else 0
    )
    return context


def test_deterministic_post_workout_review_exact_plan_completion_language(
    tmp_path, monkeypatch
):
    context = _post_workout_context_with_set_counts(
        tmp_path,
        monkeypatch,
        planned_sets=11,
        completed_sets=11,
    )

    review = (
        post_workout_review_service.build_deterministic_post_workout_review_summary(
            context
        )
    )

    assert "completed all 11 planned sets" in review.session_summary.lower()
    assert "extra" not in review.session_summary.lower()
    assert "12 of 11" not in review.session_summary


def test_deterministic_post_workout_review_partial_completion_language(
    tmp_path, monkeypatch
):
    context = _post_workout_context_with_set_counts(
        tmp_path,
        monkeypatch,
        planned_sets=11,
        completed_sets=8,
    )

    review = (
        post_workout_review_service.build_deterministic_post_workout_review_summary(
            context
        )
    )

    assert "8 of 11 planned sets" in review.session_summary.lower()
    assert "part of the planned work" in review.completion_reflection.lower()
    assert "increase" not in str(review).lower()


def test_deterministic_post_workout_review_extra_sets_use_extra_set_language(
    tmp_path, monkeypatch
):
    context = _post_workout_context_with_set_counts(
        tmp_path,
        monkeypatch,
        planned_sets=11,
        completed_sets=12,
    )

    review = (
        post_workout_review_service.build_deterministic_post_workout_review_summary(
            context
        )
    )
    combined = str(review).lower()

    assert "12 of 11" not in review.session_summary
    assert "completed the planned work" in review.session_summary.lower()
    assert "1 extra set" in review.session_summary.lower()
    assert "slightly above the written plan" in review.reps_or_volume_reflection.lower()
    assert "not a new target" in review.completion_reflection.lower()
    assert "note why" in review.next_time_focus.lower()
    assert "increase volume" not in combined
    assert "increase weight" not in combined
    assert "overtraining" not in combined
    assert "failed" not in combined


def test_deterministic_post_workout_review_extra_sets_pluralize_cleanly(
    tmp_path, monkeypatch
):
    context = _post_workout_context_with_set_counts(
        tmp_path,
        monkeypatch,
        planned_sets=10,
        completed_sets=13,
    )

    review = (
        post_workout_review_service.build_deterministic_post_workout_review_summary(
            context
        )
    )

    assert "3 extra sets" in review.session_summary.lower()
    assert "13 of 10" not in review.session_summary


def test_deterministic_post_workout_review_handles_missing_planned_set_count(
    tmp_path, monkeypatch
):
    context = _post_workout_context_with_set_counts(
        tmp_path,
        monkeypatch,
        planned_sets=0,
        completed_sets=3,
    )

    review = (
        post_workout_review_service.build_deterministic_post_workout_review_summary(
            context
        )
    )

    assert "approved workout session" in review.session_summary.lower()
    assert "0 planned" not in review.session_summary.lower()
    assert "0 planned" not in review.reps_or_volume_reflection.lower()


def test_deterministic_post_workout_review_substitutions_and_skips_stay_neutral(
    tmp_path, monkeypatch
):
    context = _post_workout_context_with_set_counts(
        tmp_path,
        monkeypatch,
        planned_sets=11,
        completed_sets=12,
        skipped_exercises=1,
        substitutions=1,
    )

    review = (
        post_workout_review_service.build_deterministic_post_workout_review_summary(
            context
        )
    )
    combined = str(review).lower()

    assert (
        "substitutions and skipped work"
        in review.substitutions_or_skips_context.lower()
    )
    assert "poor adherence" not in combined
    assert "discipline" not in combined
    assert "failed" not in combined


def test_post_workout_review_validator_rejects_old_over_plan_ratio_copy(
    tmp_path, monkeypatch
):
    context = _post_workout_context_with_set_counts(
        tmp_path,
        monkeypatch,
        planned_sets=11,
        completed_sets=12,
    )
    payload = _valid_post_workout_review_payload(
        next_time_focus="Keep noting anything extra so reviews have context."
    )
    payload["session_summary"] = (
        "You completed 12 of 11 planned sets from the approved workout."
    )
    candidate = parse_candidate_post_workout_review_summary_json(json.dumps(payload))

    violations = validate_candidate_post_workout_review_summary(candidate, context)

    assert any("extra-set language" in violation for violation in violations)


def test_deterministic_post_workout_review_next_time_focus_is_logging_focused(
    tmp_path, monkeypatch
):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )

    result = build_configured_post_workout_review_summary_with_metadata(execution_id)
    focus = result.approved_post_workout_review_summary.next_time_focus.lower()

    assert "reps" in focus
    assert "weight" in focus
    assert "rir" in focus
    assert "increase" not in focus
    assert "deload" not in focus
    assert "next workout should" not in focus


def test_post_workout_review_validator_rejects_prescriptive_and_judgmental_copy(
    tmp_path, monkeypatch
):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )
    context = build_post_workout_review_context(execution_id)
    candidate = parse_candidate_post_workout_review_summary_json(
        json.dumps(
            _valid_post_workout_review_payload(
                next_time_focus="Next workout should increase weight because this proves progress."
            )
        )
    )

    violations = validate_candidate_post_workout_review_summary(candidate, context)

    assert violations
    assert any("programming" in violation.lower() for violation in violations)


def test_mocked_crewai_post_workout_review_valid_json_approves(tmp_path, monkeypatch):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )
    context = build_post_workout_review_context(execution_id)

    result = approve_post_workout_review_summary_provider_or_fallback_with_metadata(
        lambda provided_context: json.dumps(_valid_post_workout_review_payload()),
        context,
    )

    assert result.runtime_metadata.crewai_attempted is True
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "success"
    assert result.runtime_metadata.final_review_source == "crewai_approved"


def test_mocked_crewai_post_workout_review_malformed_json_falls_back(
    tmp_path, monkeypatch
):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )
    context = build_post_workout_review_context(execution_id)

    result = approve_post_workout_review_summary_provider_or_fallback_with_metadata(
        lambda provided_context: "not-json",
        context,
    )

    assert result.approved_post_workout_review_summary.session_summary
    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "malformed_json"
    assert result.runtime_metadata.candidate_parse_status == "failed"


def test_mocked_crewai_post_workout_review_unsafe_copy_falls_back(
    tmp_path, monkeypatch
):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )
    context = build_post_workout_review_context(execution_id)

    result = approve_post_workout_review_summary_provider_or_fallback_with_metadata(
        lambda provided_context: json.dumps(
            _valid_post_workout_review_payload(
                next_time_focus="Use an automatic deload because progress has stalled."
            )
        ),
        context,
    )

    assert result.runtime_metadata.fallback_used is True
    assert result.runtime_metadata.fallback_reason == "validation_failure"
    assert result.runtime_metadata.candidate_parse_status == "success"
    assert result.runtime_metadata.candidate_validation_status == "failed"


def test_post_workout_review_debug_endpoint_returns_runtime_metadata(
    tmp_path, monkeypatch
):
    execution_id, plan_instance_id = _completed_workout_execution(tmp_path, monkeypatch)
    monkeypatch.setenv("POST_WORKOUT_REVIEW_PROVIDER", "deterministic")

    client = TestClient(app)
    response = client.get(
        f"/workout-executions/{execution_id}/post-workout-summary/debug"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["execution_id"] == execution_id
    assert payload["plan_instance_id"] == plan_instance_id
    assert payload["approved_workout_plan"]["exercises"]
    assert payload["planned_vs_actual_summary"]["completed_set_count"] > 0
    assert payload["approved_post_workout_review_summary"]["session_summary"]
    assert (
        payload["post_workout_review_runtime_metadata"]["selected_provider"]
        == "deterministic"
    )
    assert payload["post_workout_review_runtime_metadata"]["crewai_attempted"] is False


def test_public_post_workout_review_endpoint_returns_approved_summary_only(
    tmp_path, monkeypatch
):
    execution_id, plan_instance_id = _completed_workout_execution(tmp_path, monkeypatch)
    monkeypatch.setenv("POST_WORKOUT_REVIEW_PROVIDER", "deterministic")

    client = TestClient(app)
    response = client.get(f"/workout-executions/{execution_id}/post-workout-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["execution_id"] == execution_id
    assert payload["plan_instance_id"] == plan_instance_id
    assert payload["approved_post_workout_review_summary"]["session_summary"]
    assert "approved_workout_plan" not in payload
    assert "planned_vs_actual_summary" not in payload
    assert "post_workout_review_runtime_metadata" not in payload
    assert "runtime_metadata" not in payload
    assert "raw_output" not in payload
    assert "validation_errors" not in payload
    assert "fallback_reason" not in payload


def test_public_post_workout_review_endpoint_rejects_missing_execution(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()

    client = TestClient(app)
    response = client.get("/workout-executions/999999/post-workout-summary")

    assert response.status_code == 404


def test_public_post_workout_review_endpoint_rejects_non_completed_execution(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    selected = select_current_workout_plan(102)
    execution_id = selected["execution_session"].id

    client = TestClient(app)
    response = client.get(f"/workout-executions/{execution_id}/post-workout-summary")

    assert response.status_code == 400


def test_public_post_workout_review_endpoint_uses_mocked_crewai_when_valid(
    tmp_path, monkeypatch
):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )
    monkeypatch.setenv("POST_WORKOUT_REVIEW_PROVIDER", "crewai")
    monkeypatch.setattr(
        post_workout_review_service,
        "generate_crewai_post_workout_review_summary_json",
        lambda provided_context: json.dumps(
            _valid_post_workout_review_payload(confidence=provided_context.confidence)
        ),
    )

    client = TestClient(app)
    response = client.get(f"/workout-executions/{execution_id}/post-workout-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["approved_post_workout_review_summary"][
        "session_summary"
    ].startswith("You completed")
    assert "post_workout_review_runtime_metadata" not in payload
    assert "approved_workout_plan" not in payload


def test_public_post_workout_review_endpoint_falls_back_on_unsafe_crewai_output(
    tmp_path, monkeypatch
):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )
    monkeypatch.setenv("POST_WORKOUT_REVIEW_PROVIDER", "crewai")
    monkeypatch.setattr(
        post_workout_review_service,
        "generate_crewai_post_workout_review_summary_json",
        lambda provided_context: json.dumps(
            _valid_post_workout_review_payload(
                confidence=provided_context.confidence,
                next_time_focus="Use an automatic deload because progress has stalled.",
            )
        ),
    )

    client = TestClient(app)
    response = client.get(f"/workout-executions/{execution_id}/post-workout-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["approved_post_workout_review_summary"]["session_summary"]
    assert "post_workout_review_runtime_metadata" not in payload
    assert "fallback_reason" not in payload


def test_configured_post_workout_review_uses_mocked_crewai_provider(
    tmp_path, monkeypatch
):
    execution_id, _plan_instance_id = _completed_workout_execution(
        tmp_path, monkeypatch
    )
    monkeypatch.setenv("POST_WORKOUT_REVIEW_PROVIDER", "crewai")
    monkeypatch.setattr(
        post_workout_review_service,
        "generate_crewai_post_workout_review_summary_json",
        lambda context: json.dumps(_valid_post_workout_review_payload()),
    )

    result = build_configured_post_workout_review_summary_with_metadata(execution_id)

    assert result.runtime_metadata.selected_provider == "crewai"
    assert result.runtime_metadata.crewai_attempted is True
    assert result.runtime_metadata.fallback_used is False
    assert result.runtime_metadata.final_review_source == "crewai_approved"
