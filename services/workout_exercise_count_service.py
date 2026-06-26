from __future__ import annotations

from dataclasses import dataclass

MIN_WORKOUT_EXERCISE_COUNT = 3
MAX_WORKOUT_EXERCISE_COUNT = 7
DEFAULT_WORKOUT_SIZE_PREFERENCE = "standard"

_WORKOUT_SIZE_RANGES = {
    "quick": (3, 4),
    "standard": (4, 5),
    "full": (6, 7),
}
_ALLOWED_SIZE_PREFERENCES = set(_WORKOUT_SIZE_RANGES)


@dataclass(frozen=True)
class ResolvedWorkoutExerciseCount:
    requested_size: str
    requested_count: int
    final_count: int
    min_allowed: int
    max_allowed: int
    clamp_reason: str
    user_safe_reason: str


def normalize_workout_size_preference(value: str | None) -> str:
    normalized = (value or DEFAULT_WORKOUT_SIZE_PREFERENCE).strip().lower()
    if normalized not in _ALLOWED_SIZE_PREFERENCES:
        return DEFAULT_WORKOUT_SIZE_PREFERENCE
    return normalized


def _clamp_requested_count(value: int | None, min_count: int, max_count: int) -> int:
    if value is None:
        return min_count
    return max(min_count, min(max_count, int(value)))


def _deterministic_count_in_range(
    *,
    requested_size: str,
    min_count: int,
    max_count: int,
    user_id: int | None,
    scenario: str | None,
    preview_variation_index: int | None,
) -> int:
    if min_count >= max_count:
        return min_count

    del requested_size, user_id, scenario

    range_width = (max_count - min_count) + 1
    variation_offset = max(0, int(preview_variation_index or 0)) % range_width
    return max_count - variation_offset


def _user_safe_reason(requested_size: str, final_count: int, clamp_reason: str) -> str:
    if clamp_reason == "available_exercises_limited":
        return (
            f"Built as a {final_count}-exercise session because the current "
            "equipment and safety constraints limited the valid options."
        )
    if clamp_reason == "data_quality_limited":
        return f"Built as a {final_count}-exercise session while the coach keeps the plan easy to review."
    if requested_size == "quick":
        return f"Built as a quick {final_count}-exercise session within the 3-4 exercise range."
    if requested_size == "full":
        return f"Built as a fuller {final_count}-exercise session within the 6-7 exercise range."
    return f"Built as a standard {final_count}-exercise session within the 4-5 exercise range."


def resolve_workout_exercise_count(
    *,
    requested_size: str | None = None,
    requested_target_count: int | None = None,
    scenario: str | None = None,
    confidence: str | None = None,
    available_candidate_count: int | None = None,
    user_id: int | None = None,
    preview_variation_index: int | None = 0,
) -> ResolvedWorkoutExerciseCount:
    """Resolve a user-facing workout size into a safe deterministic count range.

    Quick/Standard/Full are treated as intent ranges, not fixed constants. The
    selected count is deterministic for the same user/context/variation key.
    Hard safety or candidate-availability constraints may reduce the final
    count, but reductions are reflected in the user-safe reason.
    """

    normalized_size = normalize_workout_size_preference(requested_size)
    min_count, max_count = _WORKOUT_SIZE_RANGES[normalized_size]

    if requested_target_count is None:
        requested_count = _deterministic_count_in_range(
            requested_size=normalized_size,
            min_count=min_count,
            max_count=max_count,
            user_id=user_id,
            scenario=scenario,
            preview_variation_index=preview_variation_index,
        )
    else:
        requested_count = _clamp_requested_count(
            requested_target_count, min_count, max_count
        )

    final_count = requested_count
    clamp_reason = f"{normalized_size}_session"

    normalized_scenario = (scenario or "").strip().lower()
    normalized_confidence = (confidence or "").strip().lower()

    if normalized_scenario == "data_quality_limited" and final_count > 5:
        final_count = 5
        clamp_reason = "data_quality_limited"
    elif normalized_confidence == "limited" and final_count > 5:
        final_count = 5
        clamp_reason = "data_quality_limited"

    if available_candidate_count is not None:
        candidate_count = max(0, int(available_candidate_count))
        if candidate_count < final_count:
            final_count = candidate_count
            clamp_reason = "available_exercises_limited"

    final_count = max(
        MIN_WORKOUT_EXERCISE_COUNT,
        min(MAX_WORKOUT_EXERCISE_COUNT, final_count),
    )

    return ResolvedWorkoutExerciseCount(
        requested_size=normalized_size,
        requested_count=requested_count,
        final_count=final_count,
        min_allowed=min_count,
        max_allowed=max_count,
        clamp_reason=clamp_reason,
        user_safe_reason=_user_safe_reason(normalized_size, final_count, clamp_reason),
    )
