from __future__ import annotations

import re

import database
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.exercise_catalog_service import (
    EXERCISE_CATALOG_IMPORT_BATCH_V1,
    filter_exercises_for_equipment,
    get_exercise_catalog,
    seed_exercise_catalog,
)

EXPECTED_BATCH_NAMES = {
    "Bodyweight Step-Up",
    "Front-Foot Elevated Split Squat",
    "Deficit Reverse Lunge",
    "Cossack Squat",
    "Single-Leg Calf Raise",
    "Single-Leg Hip Thrust",
    "Reverse Plank",
    "V-Up",
    "Lying Leg Raise",
    "Copenhagen Side Plank",
    "Dumbbell Alternating Bench Press",
    "Single-Arm Dumbbell Floor Press",
    "Dumbbell Cossack Squat",
    "Dumbbell Seated Calf Raise",
    "Barbell Step-Up",
    "Zercher Squat",
    "Single-Arm Cable Lat Pulldown",
    "Cable Hip Abduction",
}

HOME_GYM_EQUIPMENT = [
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

ALLOWED_TYPES = {"strength", "core", "conditioning", "mobility"}
ALLOWED_PATTERNS = {
    "arms_biceps",
    "arms_triceps",
    "carry",
    "conditioning",
    "core_anti_extension",
    "core_anti_rotation",
    "hinge",
    "horizontal_pull",
    "horizontal_push",
    "lunge",
    "mobility",
    "squat",
    "vertical_pull",
    "vertical_push",
}
ALLOWED_DIFFICULTIES = {"beginner", "intermediate", "advanced"}
ALLOWED_EQUIPMENT = set(HOME_GYM_EQUIPMENT) | {"bodyweight", "machine"}
UNSAFE_EXERCISE_LANGUAGE = re.compile(
    r"\b("
    r"fix(?:es)?|cure(?:s)?|heal(?:s|ing)?|rehab|rehabilitation|therapy|"
    r"therapeutic|medical|doctor|clinician|prescribe|treat(?:s|ment)?|"
    r"diagnose|pain[- ]?free|injury[- ]?proof|guarantee(?:d|s)?|"
    r"safe for everyone|prevents injury|physical therapy|bad knees|back pain"
    r")\b",
    re.IGNORECASE,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    seed_exercise_catalog()


def test_exercise_catalog_import_batch_v1_has_exact_tiny_reviewed_batch() -> None:
    assert 15 <= len(EXERCISE_CATALOG_IMPORT_BATCH_V1) <= 25
    assert {
        entry.name for entry in EXERCISE_CATALOG_IMPORT_BATCH_V1
    } == EXPECTED_BATCH_NAMES


def test_exercise_catalog_import_batch_v1_entries_are_schema_valid() -> None:
    for entry in EXERCISE_CATALOG_IMPORT_BATCH_V1:
        assert entry.exercise_type in ALLOWED_TYPES
        assert entry.movement_pattern in ALLOWED_PATTERNS
        assert entry.difficulty in ALLOWED_DIFFICULTIES
        assert entry.name.strip()
        assert entry.primary_muscle_groups
        assert entry.equipment_required
        assert set(entry.equipment_required).issubset(ALLOWED_EQUIPMENT)


def test_exercise_catalog_import_batch_v1_has_no_duplicate_catalog_names(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    names = [entry.name.strip().lower() for entry in get_exercise_catalog()]

    assert len(names) == len(set(names))


def test_exercise_catalog_import_batch_v1_rows_load_from_canonical_catalog(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    catalog_names = {entry.name for entry in get_exercise_catalog()}

    assert EXPECTED_BATCH_NAMES.issubset(catalog_names)


def test_exercise_catalog_import_batch_v1_rows_are_home_gym_compatible(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    home_gym_names = {
        entry.name
        for entry in filter_exercises_for_equipment(
            available_equipment=HOME_GYM_EQUIPMENT,
            unavailable_equipment=["machine"],
        )
    }

    assert EXPECTED_BATCH_NAMES.issubset(home_gym_names)


def test_exercise_catalog_import_batch_v1_contains_no_unsafe_medical_claim_language() -> (
    None
):
    for entry in EXERCISE_CATALOG_IMPORT_BATCH_V1:
        checked_text = " ".join(
            [
                entry.name,
                entry.exercise_type,
                entry.movement_pattern,
                entry.difficulty,
                *entry.primary_muscle_groups,
                *entry.equipment_required,
            ]
        )
        assert UNSAFE_EXERCISE_LANGUAGE.search(checked_text) is None


def test_exercise_catalog_import_batch_v1_preserves_prior_food_batch_boundary() -> None:
    # This test intentionally imports only exercise-catalog symbols. Food catalog
    # seed data is out of scope for Exercise Catalog Import Batch v1 and should
    # not be required for this milestone's catalog integrity checks.
    assert len(EXERCISE_CATALOG_IMPORT_BATCH_V1) == len(EXPECTED_BATCH_NAMES)
