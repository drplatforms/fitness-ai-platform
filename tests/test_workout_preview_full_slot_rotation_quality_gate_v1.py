"""Diagnostic quality gate for full-slot preview rotation.

This test intentionally targets the real local runtime database/user that exposed
smoke failures.  It should fail on the current failed-smoke branch before the
next implementation patch is applied.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from dataclasses import dataclass
from typing import Any

import pytest

from api.routes.workout_plans import workout_plan_preview
from services.exercise_catalog_service import find_catalog_entry_by_name

QUALITY_GATE_USER_ID = 1
SIZES = ("quick", "standard", "full")
VARIATIONS = (0, 1, 2, 3, 4)


@dataclass(frozen=True)
class ExerciseInfo:
    name: str
    movement_pattern: str
    equipment_required: tuple[str, ...]


def _exercise_info(exercise: dict[str, Any]) -> ExerciseInfo:
    name = exercise.get("name") or exercise.get("exercise_name") or "<missing-name>"
    catalog_entry = find_catalog_entry_by_name(name)
    movement_pattern = (
        catalog_entry.movement_pattern
        if catalog_entry is not None
        else "<missing-pattern>"
    )
    equipment = exercise.get("equipment_required") or []
    return ExerciseInfo(
        name=name,
        movement_pattern=movement_pattern,
        equipment_required=tuple(str(item) for item in equipment),
    )


def _preview_exercises(size: str, variation_index: int) -> list[ExerciseInfo]:
    try:
        result = workout_plan_preview(
            user_id=QUALITY_GATE_USER_ID,
            workout_size_preference=size,
            preview_variation_index=variation_index,
        )
    except sqlite3.OperationalError as exc:
        pytest.skip(
            f"local runtime database is not initialized for diagnostic gate: {exc}"
        )

    plan = result.get("approved_workout_plan") or {}
    return [_exercise_info(exercise) for exercise in plan.get("exercises") or []]


def _name_list(exercises: list[ExerciseInfo]) -> list[str]:
    return [exercise.name for exercise in exercises]


def _diagnostic_for_repeat(
    *,
    size: str,
    slot_index: int,
    previous: ExerciseInfo,
    refreshed: ExerciseInfo,
    variations: dict[int, list[ExerciseInfo]],
    valid_alternatives: list[ExerciseInfo],
) -> str:
    return "\n".join(
        [
            f"size={size}",
            "transition=variation 0 -> variation 1",
            f"slot_index={slot_index}",
            f"selected_exercise={refreshed.name}",
            f"previous_same_slot_exercise={previous.name}",
            f"movement_pattern={refreshed.movement_pattern}",
            f"equipment_requirements={list(refreshed.equipment_required)}",
            f"candidate_count_observed_across_variations={len(valid_alternatives) + 1}",
            "valid_alternatives_observed="
            + str(
                [
                    {
                        "name": alternative.name,
                        "movement_pattern": alternative.movement_pattern,
                        "equipment_required": list(alternative.equipment_required),
                    }
                    for alternative in valid_alternatives
                ]
            ),
            "reason_previous_exercise_won=unknown: current selector chose the previous same-slot exercise even though later variations prove valid alternatives are reachable",
            "previous_slot_penalty_applied=not exposed by current diagnostics",
            "previous_preview_penalty_applied=not exposed by current diagnostics",
            "all_variation_names="
            + str(
                {
                    variation_index: _name_list(exercises)
                    for variation_index, exercises in variations.items()
                }
            ),
        ]
    )


def test_first_refresh_rejects_same_slot_repeats_when_observed_alternatives_exist() -> (
    None
):
    """Quality gate for the real smoke failure: variation 0 -> variation 1.

    The current failed branch repeats Dumbbell Single-Leg RDL in slot 1 and can
    repeat later accessory slots even though later variation indexes prove valid
    alternatives are reachable.  This test must fail before the implementation
    patch and pass after the selector refuses previous same-slot winners when an
    alternative exists.
    """

    failures: list[str] = []

    for size in SIZES:
        variations = {
            variation_index: _preview_exercises(size, variation_index)
            for variation_index in VARIATIONS
        }
        previous = variations[0]
        refreshed = variations[1]
        overlap = min(len(previous), len(refreshed))

        duplicate_names = sorted(
            name for name, count in Counter(_name_list(refreshed)).items() if count > 1
        )
        if duplicate_names:
            failures.append(
                f"size={size}\nexact_duplicate_exercise_names={duplicate_names}"
            )

        for index in range(overlap):
            previous_exercise = previous[index]
            refreshed_exercise = refreshed[index]
            if previous_exercise.name != refreshed_exercise.name:
                continue

            valid_alternatives: list[ExerciseInfo] = []
            for variation_index in VARIATIONS[2:]:
                exercises = variations[variation_index]
                if index >= len(exercises):
                    continue
                alternative = exercises[index]
                if alternative.name != previous_exercise.name:
                    valid_alternatives.append(alternative)

            if valid_alternatives:
                failures.append(
                    _diagnostic_for_repeat(
                        size=size,
                        slot_index=index + 1,
                        previous=previous_exercise,
                        refreshed=refreshed_exercise,
                        variations=variations,
                        valid_alternatives=valid_alternatives,
                    )
                )

    assert not failures, "\n\n".join(failures)
