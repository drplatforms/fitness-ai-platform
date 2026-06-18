from __future__ import annotations

import json
from dataclasses import asdict

import database
from database import get_connection
from models.exercise_catalog_models import ExerciseCatalogEntry

_CATALOG_CACHE_BY_DB_PATH: dict[str, list[ExerciseCatalogEntry]] = {}


def clear_exercise_catalog_cache() -> None:
    """Clear the in-process exercise catalog cache.

    The catalog itself is deterministic and database-backed. Tests frequently
    monkeypatch database.DB_PATH, so the cache is keyed by the current DB path
    and can be cleared explicitly after reseeding.
    """

    _CATALOG_CACHE_BY_DB_PATH.clear()


def _exercise_catalog_cache_key() -> str:
    return str(database.DB_PATH)


CURATED_EXERCISE_CATALOG: list[ExerciseCatalogEntry] = [
    # Bodyweight
    ExerciseCatalogEntry(
        None,
        "Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Incline Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight", "adjustable_bench"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Bodyweight Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Reverse Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Split Squat",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Glute Bridge",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Plank",
        "core",
        "core_anti_extension",
        ["core"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Side Plank",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dead Bug",
        "core",
        "core_anti_extension",
        ["core"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Mountain Climber",
        "conditioning",
        "conditioning",
        ["core", "conditioning"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Inverted Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["bodyweight"],
        "intermediate",
    ),
    # Dumbbell / bench
    ExerciseCatalogEntry(
        None,
        "Dumbbell Bench Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Incline Dumbbell Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Shoulder Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "One-Arm Dumbbell Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["dumbbell", "adjustable_bench"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Chest-Supported Dumbbell Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Chest-Supported Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell RDL",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "back"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Goblet Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Split Squat",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Reverse Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Lateral Raise",
        "strength",
        "vertical_push",
        ["shoulders"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Triceps Extension",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Farmer Carry",
        "conditioning",
        "carry",
        ["grip", "traps", "core"],
        ["dumbbell"],
        "beginner",
    ),
    # Barbell / rack / plates
    ExerciseCatalogEntry(
        None,
        "Barbell Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Back Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Front Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["barbell", "rack", "plates"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Bench Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["barbell", "rack", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Overhead Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Romanian Deadlift",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "back"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Conventional Deadlift",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "back"],
        ["barbell", "plates"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Hip Thrust",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["barbell", "plates", "adjustable_bench"],
        "intermediate",
    ),
    # EZ bar
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["ez_bar", "plates"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Skull Crusher",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["ez_bar", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Close-Grip Press",
        "strength",
        "horizontal_push",
        ["triceps", "chest"],
        ["ez_bar", "plates", "adjustable_bench"],
        "intermediate",
    ),
    # Pull-up bar
    ExerciseCatalogEntry(
        None,
        "Pull-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["pull_up_bar"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Chin-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["pull_up_bar"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Band-Assisted Pull-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["pull_up_bar", "resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Hanging Knee Raise",
        "core",
        "core_anti_extension",
        ["core", "hip_flexors"],
        ["pull_up_bar"],
        "intermediate",
    ),
    # Bands
    ExerciseCatalogEntry(
        None,
        "Band Pull-Apart",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Face Pull",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Triceps Pressdown",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band External Rotation",
        "mobility",
        "horizontal_pull",
        ["rotator_cuff"],
        ["resistance_band"],
        "beginner",
    ),
    # Cable
    ExerciseCatalogEntry(
        None,
        "Cable Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Lat Pulldown",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Lat Pulldown",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Face Pull",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Triceps Pressdown",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None, "Cable Curl", "strength", "arms_biceps", ["biceps"], ["cable"], "beginner"
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Lateral Raise",
        "strength",
        "vertical_push",
        ["shoulders"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Woodchop",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["cable"],
        "beginner",
    ),
    # Machines retained for commercial gym users only
    ExerciseCatalogEntry(
        None,
        "Leg Press",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["machine"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Machine Chest Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["machine"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Machine Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["machine"],
        "beginner",
    ),
    # Cardio
    ExerciseCatalogEntry(
        None,
        "Treadmill Walk",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Incline Walk",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Intervals",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Steady State",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Intervals",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "intermediate",
    ),
    # Expanded home-gym catalog
    ExerciseCatalogEntry(
        None,
        "Bear Crawl",
        "conditioning",
        "conditioning",
        ["core", "shoulders", "conditioning"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Bird Dog",
        "core",
        "core_anti_rotation",
        ["core", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Hollow Body Hold",
        "core",
        "core_anti_extension",
        ["core"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Hollow Rock",
        "core",
        "core_anti_extension",
        ["core"],
        ["bodyweight"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Superman Hold",
        "core",
        "hinge",
        ["lower_back", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Walking Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Lateral Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes", "adductors"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Wall Sit",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Standing Calf Raise",
        "strength",
        "conditioning",
        ["calves"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Single-Leg Glute Bridge",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Pike Push-Up",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Close-Grip Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Tempo Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Decline Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Bench Dip",
        "strength",
        "arms_triceps",
        ["triceps", "chest"],
        ["bodyweight", "adjustable_bench"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Floor Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Fly",
        "strength",
        "horizontal_push",
        ["chest", "shoulders"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Incline Dumbbell Fly",
        "strength",
        "horizontal_push",
        ["chest", "shoulders"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Pullover",
        "strength",
        "horizontal_pull",
        ["lats", "chest", "core"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Arnold Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Seated Dumbbell Shoulder Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Front Raise",
        "strength",
        "vertical_push",
        ["shoulders"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Rear Delt Fly",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Chest-Supported Rear Delt Fly",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["dumbbell", "adjustable_bench"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Shrug",
        "strength",
        "horizontal_pull",
        ["traps", "upper_back"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Upright Row",
        "strength",
        "vertical_push",
        ["shoulders", "traps"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Hammer Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Concentration Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Zottman Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Kickback",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["dumbbell", "adjustable_bench"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Skull Crusher",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Close-Grip Press",
        "strength",
        "horizontal_push",
        ["triceps", "chest"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Step-Up",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Lateral Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes", "adductors"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Bulgarian Split Squat",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Sumo Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "adductors"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Front Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Single-Leg RDL",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "core"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Hip Thrust",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Suitcase Carry",
        "conditioning",
        "carry",
        ["grip", "core", "obliques"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Waiter Carry",
        "conditioning",
        "carry",
        ["shoulders", "core", "grip"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Front Rack Carry",
        "conditioning",
        "carry",
        ["core", "upper_back", "grip"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Calf Raise",
        "strength",
        "conditioning",
        ["calves"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Pause Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Box Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["barbell", "rack", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Reverse Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Split Squat",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Good Morning",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "lower_back"],
        ["barbell", "rack", "plates"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Glute Bridge",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Floor Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Close-Grip Bench Press",
        "strength",
        "horizontal_push",
        ["triceps", "chest", "shoulders"],
        ["barbell", "rack", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Incline Barbell Bench Press",
        "strength",
        "horizontal_push",
        ["chest", "shoulders", "triceps"],
        ["barbell", "rack", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Push Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps", "quadriceps"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Pendlay Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps", "upper_back"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell High Pull",
        "strength",
        "horizontal_pull",
        ["upper_back", "traps", "shoulders"],
        ["barbell", "plates"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["barbell", "plates"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Rollout",
        "core",
        "core_anti_extension",
        ["core", "shoulders"],
        ["barbell", "plates"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Plate Front Raise",
        "strength",
        "vertical_push",
        ["shoulders"],
        ["plates"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Plate Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["plates"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Plate Pinch Carry",
        "conditioning",
        "carry",
        ["grip", "forearms", "core"],
        ["plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Reverse Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["ez_bar", "plates"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Preacher-Style Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["ez_bar", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Overhead Triceps Extension",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["ez_bar", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Upright Row",
        "strength",
        "vertical_push",
        ["shoulders", "traps"],
        ["ez_bar", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Neutral-Grip Pull-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["pull_up_bar"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Negative Pull-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["pull_up_bar"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Scapular Pull-Up",
        "strength",
        "vertical_pull",
        ["lats", "lower_traps"],
        ["pull_up_bar"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Commando Pull-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps", "core"],
        ["pull_up_bar"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Dead Hang",
        "mobility",
        "vertical_pull",
        ["grip", "shoulders"],
        ["pull_up_bar"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Hanging Leg Raise",
        "core",
        "core_anti_extension",
        ["core", "hip_flexors"],
        ["pull_up_bar"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Hanging Oblique Knee Raise",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["pull_up_bar"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Biceps Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Hammer Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Overhead Triceps Extension",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Lateral Raise",
        "strength",
        "vertical_push",
        ["shoulders"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Shoulder Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Lat Pulldown",
        "strength",
        "vertical_pull",
        ["lats", "biceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Straight-Arm Pulldown",
        "strength",
        "vertical_pull",
        ["lats"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Pull-Through",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Good Morning",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "lower_back"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Resisted Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight", "resistance_band"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Pallof Press",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Woodchop",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Lateral Walk",
        "strength",
        "lunge",
        ["glutes", "hips"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Monster Walk",
        "strength",
        "lunge",
        ["glutes", "hips"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Glute Bridge",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["bodyweight", "resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Single-Arm Cable Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable High Row",
        "strength",
        "horizontal_pull",
        ["upper_back", "rear_delts", "biceps"],
        ["cable"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Reverse Fly",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Chest Fly",
        "strength",
        "horizontal_push",
        ["chest", "shoulders"],
        ["cable"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Single-Arm Cable Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "core"],
        ["cable"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Upright Row",
        "strength",
        "vertical_push",
        ["shoulders", "traps"],
        ["cable"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Y Raise",
        "strength",
        "vertical_push",
        ["shoulders", "lower_traps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable External Rotation",
        "strength",
        "horizontal_pull",
        ["rotator_cuff", "shoulders"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Internal Rotation",
        "strength",
        "horizontal_pull",
        ["rotator_cuff", "shoulders"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Pull-Through",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["cable", "rope_cable_attachment"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Crunch",
        "core",
        "core_anti_extension",
        ["core"],
        ["cable", "rope_cable_attachment"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Pallof Press",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Rope Triceps Pressdown",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["cable", "rope_cable_attachment"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Rope Overhead Triceps Extension",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["cable", "rope_cable_attachment"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Rope Hammer Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["cable", "rope_cable_attachment"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Rope Face Pull",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["cable", "rope_cable_attachment"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Straight-Arm Cable Pulldown",
        "strength",
        "vertical_pull",
        ["lats"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Hamstring Curl",
        "strength",
        "hinge",
        ["hamstrings", "glutes"],
        ["exercise_ball"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Rollout",
        "core",
        "core_anti_extension",
        ["core", "shoulders"],
        ["exercise_ball"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Plank",
        "core",
        "core_anti_extension",
        ["core"],
        ["bodyweight", "exercise_ball"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Stir-the-Pot",
        "core",
        "core_anti_extension",
        ["core", "shoulders"],
        ["exercise_ball"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Wall Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["exercise_ball"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Dead Bug",
        "core",
        "core_anti_extension",
        ["core"],
        ["exercise_ball"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Easy Jog",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Hill Intervals",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Tempo Run",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Recovery Ride",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Tempo Ride",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Hill Intervals",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "intermediate",
    ),
]


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_display_name(value: str) -> str:
    return " ".join(value.strip().replace("-", " ").split()).title()


def _normalize_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return list(
        dict.fromkeys(_normalize_token(str(value)) for value in values if value)
    )


def _encode_json_list(values: list[str]) -> str:
    return json.dumps(_normalize_list(values))


def _decode_json_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    try:
        decoded = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(decoded, list):
        return []
    return _normalize_list([str(value) for value in decoded])


def ensure_exercise_catalog_tables() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercise_catalog_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        exercise_type TEXT NOT NULL,
        movement_pattern TEXT NOT NULL,
        primary_muscle_groups_json TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercise_equipment_requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_id INTEGER NOT NULL,
        equipment TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        UNIQUE(exercise_id, equipment),
        FOREIGN KEY (exercise_id) REFERENCES exercise_catalog_exercises(id)
    )
    """)

    conn.commit()
    conn.close()


def _entry_to_legacy_exercise_row(
    entry: ExerciseCatalogEntry,
) -> tuple[str, str, str, str]:
    return (
        entry.name,
        ", ".join(
            group.replace("_", " ").title() for group in entry.primary_muscle_groups
        ),
        entry.exercise_type.replace("_", " ").title(),
        ", ".join(
            equipment.replace("_", " ").title()
            for equipment in entry.equipment_required
        ),
    )


def seed_exercise_catalog() -> list[ExerciseCatalogEntry]:
    """Seed the local curated exercise catalog.

    This is intentionally deterministic and local. It also mirrors each entry
    into the existing exercises table so manual workout logging keeps using the
    same simple exercise list endpoint until a richer catalog API is added.
    """

    ensure_exercise_catalog_tables()
    conn = get_connection()
    cursor = conn.cursor()

    for entry in CURATED_EXERCISE_CATALOG:
        normalized_equipment = _normalize_list(entry.equipment_required)
        normalized_groups = _normalize_list(entry.primary_muscle_groups)

        cursor.execute(
            """
            INSERT INTO exercise_catalog_exercises (
                name,
                exercise_type,
                movement_pattern,
                primary_muscle_groups_json,
                difficulty,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                exercise_type = excluded.exercise_type,
                movement_pattern = excluded.movement_pattern,
                primary_muscle_groups_json = excluded.primary_muscle_groups_json,
                difficulty = excluded.difficulty,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                entry.name,
                _normalize_token(entry.exercise_type),
                _normalize_token(entry.movement_pattern),
                json.dumps(normalized_groups),
                _normalize_token(entry.difficulty),
            ),
        )

        cursor.execute(
            "SELECT id FROM exercise_catalog_exercises WHERE name = ?",
            (entry.name,),
        )
        exercise_id = cursor.fetchone()["id"]

        cursor.execute(
            """
            DELETE FROM exercise_equipment_requirements
            WHERE exercise_id = ?
            """,
            (exercise_id,),
        )

        for equipment in normalized_equipment:
            cursor.execute(
                """
                INSERT OR IGNORE INTO exercise_equipment_requirements (
                    exercise_id,
                    equipment
                )
                VALUES (?, ?)
                """,
                (exercise_id, equipment),
            )

        legacy_name, muscle_group, movement_type, equipment = (
            _entry_to_legacy_exercise_row(
                ExerciseCatalogEntry(
                    id=exercise_id,
                    name=entry.name,
                    exercise_type=entry.exercise_type,
                    movement_pattern=entry.movement_pattern,
                    primary_muscle_groups=normalized_groups,
                    equipment_required=normalized_equipment,
                    difficulty=entry.difficulty,
                )
            )
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO exercises (
                name,
                muscle_group,
                movement_type,
                equipment
            )
            VALUES (?, ?, ?, ?)
            """,
            (legacy_name, muscle_group, movement_type, equipment),
        )

    conn.commit()
    conn.close()
    _CATALOG_CACHE_BY_DB_PATH.pop(_exercise_catalog_cache_key(), None)
    return list(CURATED_EXERCISE_CATALOG)


def _row_to_catalog_entry(row, equipment_required: list[str]) -> ExerciseCatalogEntry:
    return ExerciseCatalogEntry(
        id=row["id"],
        name=row["name"],
        exercise_type=row["exercise_type"],
        movement_pattern=row["movement_pattern"],
        primary_muscle_groups=_decode_json_list(row["primary_muscle_groups_json"]),
        equipment_required=_normalize_list(equipment_required),
        difficulty=row["difficulty"],
    )


def get_exercise_catalog() -> list[ExerciseCatalogEntry]:
    cache_key = _exercise_catalog_cache_key()
    cached_entries = _CATALOG_CACHE_BY_DB_PATH.get(cache_key)
    if cached_entries is not None:
        return list(cached_entries)

    seed_exercise_catalog()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM exercise_catalog_exercises
    ORDER BY id
    """)
    rows = cursor.fetchall()

    entries: list[ExerciseCatalogEntry] = []
    for row in rows:
        cursor.execute(
            """
            SELECT equipment
            FROM exercise_equipment_requirements
            WHERE exercise_id = ?
            ORDER BY equipment
            """,
            (row["id"],),
        )
        equipment_rows = cursor.fetchall()
        entries.append(
            _row_to_catalog_entry(
                row,
                [equipment_row["equipment"] for equipment_row in equipment_rows],
            )
        )

    conn.close()
    _CATALOG_CACHE_BY_DB_PATH[cache_key] = entries
    return list(entries)


def get_exercise_catalog_dicts() -> list[dict]:
    return [asdict(entry) for entry in get_exercise_catalog()]


def _equipment_allowed(
    equipment_required: list[str],
    available_equipment: list[str],
    unavailable_equipment: list[str],
) -> bool:
    required = set(_normalize_list(equipment_required))
    available = set(_normalize_list(available_equipment))
    unavailable = set(_normalize_list(unavailable_equipment))

    if required & unavailable:
        return False

    if available and not required.issubset(available):
        return False

    return True


def filter_exercises_for_equipment(
    available_equipment: list[str],
    unavailable_equipment: list[str] | None = None,
    movement_patterns: list[str] | None = None,
) -> list[ExerciseCatalogEntry]:
    patterns = set(_normalize_list(movement_patterns))
    unavailable_equipment = unavailable_equipment or []

    matches: list[ExerciseCatalogEntry] = []
    for entry in get_exercise_catalog():
        if patterns and _normalize_token(entry.movement_pattern) not in patterns:
            continue

        if _equipment_allowed(
            entry.equipment_required,
            available_equipment,
            unavailable_equipment,
        ):
            matches.append(entry)

    return matches


def find_catalog_entry_by_name(name: str) -> ExerciseCatalogEntry | None:
    normalized_name = _normalize_display_name(name)
    for entry in get_exercise_catalog():
        if _normalize_display_name(entry.name) == normalized_name:
            return entry
    return None
