import json
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

import database
import services.workout_plan_service as workout_plan_service
from api.main import app
from models.exercise_catalog_models import ExerciseCatalogEntry
from models.training_constraint_models import TrainingConstraints
from models.workout_constraint_models import WorkoutConstraints
from models.workout_plan_models import WorkoutContext
from scripts.seed_qa_scenarios import QA_USER_IDS, seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.exercise_catalog_service import find_catalog_entry_by_name
from services.user_state_service import build_user_health_state
from services.workout_plan_persistence_service import select_current_workout_plan
from services.workout_plan_service import (
    WorkoutCandidateParseError,
    _select_exercise,
    approve_candidate_workout_plan,
    approve_workout_candidate_provider_or_fallback_with_metadata,
    build_approved_workout_plan,
    build_approved_workout_plan_from_candidate_output,
    build_configured_approved_workout_plan_with_metadata,
    build_crewai_candidate_workout_plan_prompt,
    build_workout_context,
    generate_candidate_workout_plan,
    parse_candidate_workout_plan_json,
    render_approved_workout_plan,
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
    assert payload["training_constraints"]
    assert payload["workout_constraints"]["available_equipment"]
    assert payload["allowed_exercises"]
    assert len(payload["allowed_exercises"]) <= 80
    assert payload["training_execution_summary"]
    assert payload["movement_pattern_targets"]
    assert payload["safety_constraints"]
    assert "raw_actual_set_rows" not in payload
    assert "actual_sets" not in payload
    assert all("notes" not in exercise for exercise in payload["allowed_exercises"])


def test_crewai_workout_prompt_requires_raw_json_only(tmp_path, monkeypatch):
    context = _context_for_user_102_home_gym(tmp_path, monkeypatch)

    prompt = build_crewai_candidate_workout_plan_prompt(context)

    assert "raw JSON object only" in prompt
    assert "markdown" in prompt.lower()
    assert "allowed_exercises" in prompt
    assert "automatic load-increase" in prompt


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
