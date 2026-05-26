from __future__ import annotations

from collections.abc import Mapping
from statistics import mean
from typing import Any

from database import get_connection
from models.training_execution_summary_models import TrainingExecutionSummary

RECENT_COMPLETED_EXECUTION_LIMIT = 5


def build_training_execution_summary(
    user_id: int,
    limit: int = RECENT_COMPLETED_EXECUTION_LIMIT,
) -> TrainingExecutionSummary:
    """Build a conservative, read-only summary of completed planned workouts.

    This layer intentionally does not read manual workout logs and does not feed
    recommendations, progression, CoachingDecision, or full reports yet.
    """

    plan_instance_ids = _get_recent_completed_plan_instance_ids(user_id, limit)

    if not plan_instance_ids:
        return _empty_summary(user_id)

    planned_vs_actual_summaries = [
        _load_planned_vs_actual_summary(plan_instance_id)
        for plan_instance_id in plan_instance_ids
    ]

    return _aggregate_summaries(
        user_id=user_id,
        plan_instance_ids=plan_instance_ids,
        summaries=planned_vs_actual_summaries,
    )


def _empty_summary(user_id: int) -> TrainingExecutionSummary:
    return TrainingExecutionSummary(
        user_id=user_id,
        completed_execution_count=0,
        recent_plan_instance_ids=[],
        average_completion_percentage=None,
        average_planned_rir=None,
        average_actual_rir=None,
        average_rir_deviation=None,
        skipped_exercise_count=0,
        substituted_exercise_count=0,
        sets_below_planned_reps=0,
        sets_inside_planned_reps=0,
        sets_above_planned_reps=0,
        incomplete_logging_count=0,
        missing_actual_rir_count=0,
        missing_actual_reps_count=0,
        execution_quality="no_planned_execution_data",
        execution_effort_trend="no_planned_execution_data",
        execution_completion_trend="no_planned_execution_data",
        confidence="Limited",
        reason_codes=[
            "no_completed_planned_executions",
            "manual_workout_logs_not_used_for_planned_vs_actual",
        ],
    )


def _get_recent_completed_plan_instance_ids(user_id: int, limit: int) -> list[int]:
    _ensure_workout_plan_execution_schema()
    conn = get_connection()
    cursor = conn.cursor()

    rows = cursor.execute(
        """
        SELECT id
        FROM workout_plan_instances
        WHERE user_id = ?
          AND status = 'completed'
        ORDER BY COALESCE(completed_at, selected_at, created_at) DESC,
                 id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()

    conn.close()

    return [int(row["id"]) for row in rows]


def _ensure_workout_plan_execution_schema() -> None:
    """Ensure workout execution tables/columns exist before read-only queries.

    RecommendationContext construction can happen after only the base database
    initializer has run. That initializer may create an older workout plan table
    shape, so the passive summary reader must not fail before workout execution
    workflows have touched the persistence service.
    """

    try:
        from services.workout_plan_persistence_service import (
            ensure_workout_plan_persistence_tables,
        )
    except ImportError:
        return

    ensure_workout_plan_persistence_tables()


def _load_planned_vs_actual_summary(plan_instance_id: int) -> Any:
    """Load the existing dynamic planned-vs-actual summary when available.

    The accepted design says TrainingExecutionSummary should read completed
    planned workout executions through the dynamic planned-vs-actual summary
    layer. The direct-table fallback is intentionally narrow and exists only so
    this read-only service remains defensive if the summary service location
    changes during local development.
    """

    try:
        from services.workout_plan_persistence_service import (
            build_planned_vs_actual_summary,
        )
    except ImportError:
        return _build_raw_planned_vs_actual_summary(plan_instance_id)

    return build_planned_vs_actual_summary(plan_instance_id)


def _aggregate_summaries(
    user_id: int,
    plan_instance_ids: list[int],
    summaries: list[Any],
) -> TrainingExecutionSummary:
    completion_percentages = [
        value
        for summary in summaries
        if (value := _get_number(summary, "completion_percentage")) is not None
    ]
    planned_rirs = [
        value
        for summary in summaries
        if (value := _get_number(summary, "average_planned_rir")) is not None
    ]
    actual_rirs = [
        value
        for summary in summaries
        if (value := _get_number(summary, "average_actual_rir")) is not None
    ]
    rir_deviations = [
        value
        for summary in summaries
        if (value := _get_number(summary, "rir_deviation")) is not None
    ]

    skipped_exercise_count = _sum_int(summaries, "skipped_exercise_count")
    substituted_exercise_count = _sum_int(summaries, "substituted_exercise_count")
    sets_below_planned_reps = _sum_int(summaries, "sets_below_planned_reps")
    sets_inside_planned_reps = _sum_int(summaries, "sets_inside_planned_reps")
    sets_above_planned_reps = _sum_int(summaries, "sets_above_planned_reps")
    missing_actual_rir_count = _sum_int(summaries, "missing_actual_rir_count")
    missing_actual_reps_count = _sum_int(summaries, "missing_actual_reps_count")

    incomplete_logging_count = sum(
        1
        for summary in summaries
        if _summary_has_flag(summary, "incomplete_logging")
        or _summary_has_flag(summary, "empty_completion")
    )

    average_completion_percentage = _round_mean(completion_percentages)
    average_planned_rir = _round_mean(planned_rirs)
    average_actual_rir = _round_mean(actual_rirs)

    if rir_deviations:
        average_rir_deviation = _round_mean(rir_deviations)
    elif average_planned_rir is not None and average_actual_rir is not None:
        average_rir_deviation = round(average_actual_rir - average_planned_rir, 2)
    else:
        average_rir_deviation = None

    execution_effort_trend = _classify_effort_trend(
        completed_execution_count=len(summaries),
        average_rir_deviation=average_rir_deviation,
    )
    execution_completion_trend = _classify_completion_trend(completion_percentages)
    execution_quality = _classify_execution_quality(
        completed_execution_count=len(summaries),
        average_completion_percentage=average_completion_percentage,
        incomplete_logging_count=incomplete_logging_count,
        skipped_exercise_count=skipped_exercise_count,
        substituted_exercise_count=substituted_exercise_count,
    )
    confidence = _classify_confidence(
        completed_execution_count=len(summaries),
        average_completion_percentage=average_completion_percentage,
        incomplete_logging_count=incomplete_logging_count,
        missing_actual_rir_count=missing_actual_rir_count,
        missing_actual_reps_count=missing_actual_reps_count,
    )
    reason_codes = _build_reason_codes(
        completed_execution_count=len(summaries),
        average_completion_percentage=average_completion_percentage,
        incomplete_logging_count=incomplete_logging_count,
        missing_actual_rir_count=missing_actual_rir_count,
        missing_actual_reps_count=missing_actual_reps_count,
        skipped_exercise_count=skipped_exercise_count,
        substituted_exercise_count=substituted_exercise_count,
        sets_below_planned_reps=sets_below_planned_reps,
        sets_above_planned_reps=sets_above_planned_reps,
        execution_effort_trend=execution_effort_trend,
    )

    return TrainingExecutionSummary(
        user_id=user_id,
        completed_execution_count=len(summaries),
        recent_plan_instance_ids=plan_instance_ids,
        average_completion_percentage=average_completion_percentage,
        average_planned_rir=average_planned_rir,
        average_actual_rir=average_actual_rir,
        average_rir_deviation=average_rir_deviation,
        skipped_exercise_count=skipped_exercise_count,
        substituted_exercise_count=substituted_exercise_count,
        sets_below_planned_reps=sets_below_planned_reps,
        sets_inside_planned_reps=sets_inside_planned_reps,
        sets_above_planned_reps=sets_above_planned_reps,
        incomplete_logging_count=incomplete_logging_count,
        missing_actual_rir_count=missing_actual_rir_count,
        missing_actual_reps_count=missing_actual_reps_count,
        execution_quality=execution_quality,
        execution_effort_trend=execution_effort_trend,
        execution_completion_trend=execution_completion_trend,
        confidence=confidence,
        reason_codes=reason_codes,
    )


def _classify_execution_quality(
    completed_execution_count: int,
    average_completion_percentage: float | None,
    incomplete_logging_count: int,
    skipped_exercise_count: int,
    substituted_exercise_count: int,
) -> str:
    if completed_execution_count == 0:
        return "no_planned_execution_data"

    if completed_execution_count == 1:
        return "limited_execution_data"

    if average_completion_percentage is None:
        return "limited_execution_data"

    if skipped_exercise_count or substituted_exercise_count:
        return "plan_fit_review_signal"

    if incomplete_logging_count:
        return "incomplete_logging_limited"

    if completed_execution_count >= 3 and average_completion_percentage >= 95:
        return "consistently_completed"

    if average_completion_percentage >= 80:
        return "mostly_completed"

    if average_completion_percentage >= 50:
        return "partially_completed"

    return "limited_execution_data"


def _classify_effort_trend(
    completed_execution_count: int,
    average_rir_deviation: float | None,
) -> str:
    if completed_execution_count == 0:
        return "no_planned_execution_data"

    if average_rir_deviation is None:
        return "limited_effort_data"

    if average_rir_deviation <= -1:
        return "harder_than_planned"

    if average_rir_deviation >= 1:
        return "easier_than_planned"

    return "as_planned"


def _classify_completion_trend(completion_percentages: list[float]) -> str:
    if not completion_percentages:
        return "no_planned_execution_data"

    if len(completion_percentages) == 1:
        return "limited_completion_data"

    recent_average = mean(completion_percentages[:2])
    older_average = (
        mean(completion_percentages[2:])
        if len(completion_percentages) > 2
        else mean(completion_percentages[1:])
    )

    if recent_average - older_average >= 10:
        return "improving_completion"

    if older_average - recent_average >= 10:
        return "declining_completion"

    overall_average = mean(completion_percentages)

    if overall_average >= 90:
        return "consistently_completed"

    if overall_average >= 75:
        return "mostly_completed"

    return "mixed_completion"


def _classify_confidence(
    completed_execution_count: int,
    average_completion_percentage: float | None,
    incomplete_logging_count: int,
    missing_actual_rir_count: int,
    missing_actual_reps_count: int,
) -> str:
    if completed_execution_count == 0:
        return "Limited"

    if completed_execution_count == 1:
        return "Limited" if incomplete_logging_count else "Low"

    if (
        incomplete_logging_count
        or missing_actual_rir_count
        or missing_actual_reps_count
    ):
        return "Low"

    if (
        average_completion_percentage is not None
        and average_completion_percentage >= 85
    ):
        return "Moderate"

    return "Low"


def _build_reason_codes(
    completed_execution_count: int,
    average_completion_percentage: float | None,
    incomplete_logging_count: int,
    missing_actual_rir_count: int,
    missing_actual_reps_count: int,
    skipped_exercise_count: int,
    substituted_exercise_count: int,
    sets_below_planned_reps: int,
    sets_above_planned_reps: int,
    execution_effort_trend: str,
) -> list[str]:
    reason_codes = ["completed_planned_executions_only"]

    if completed_execution_count == 1:
        reason_codes.append("single_completed_execution_limited_confidence")

    if completed_execution_count > 1:
        reason_codes.append("multiple_completed_executions_available")

    if (
        average_completion_percentage is not None
        and average_completion_percentage >= 85
    ):
        reason_codes.append("high_completion_rate")

    if incomplete_logging_count:
        reason_codes.append("incomplete_logging_lowers_confidence")

    if missing_actual_rir_count:
        reason_codes.append("missing_actual_rir_lowers_confidence")

    if missing_actual_reps_count:
        reason_codes.append("missing_actual_reps_lowers_confidence")

    if skipped_exercise_count:
        reason_codes.append("skipped_exercises_plan_fit_review_signal")

    if substituted_exercise_count:
        reason_codes.append("substitutions_plan_fit_review_signal")

    if sets_below_planned_reps:
        reason_codes.append("sets_below_planned_reps")

    if sets_above_planned_reps:
        reason_codes.append("sets_above_planned_reps")

    if execution_effort_trend == "harder_than_planned":
        reason_codes.append("actual_effort_harder_than_planned")

    if execution_effort_trend == "easier_than_planned":
        reason_codes.append("actual_effort_easier_than_planned")

    reason_codes.append("manual_workout_logs_not_used_for_planned_vs_actual")

    return reason_codes


def _summary_has_flag(summary: Any, flag: str) -> bool:
    deviation_flags = _get_value(summary, "deviation_flags") or []

    return flag in deviation_flags


def _sum_int(summaries: list[Any], field_name: str) -> int:
    return sum(int(_get_number(summary, field_name) or 0) for summary in summaries)


def _round_mean(values: list[float]) -> float | None:
    if not values:
        return None

    return round(mean(values), 2)


def _get_number(summary: Any, field_name: str) -> float | None:
    value = _get_value(summary, field_name)

    if value is None:
        return None

    return float(value)


def _get_value(summary: Any, field_name: str) -> Any:
    if isinstance(summary, Mapping):
        return summary.get(field_name)

    return getattr(summary, field_name, None)


def _build_raw_planned_vs_actual_summary(plan_instance_id: int) -> dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    planned_rows = _safe_fetchall(
        cursor,
        """
        SELECT *
        FROM planned_workout_exercises
        WHERE workout_plan_instance_id = ?
        ORDER BY id
        """,
        (plan_instance_id,),
    )

    execution_session = _safe_fetchone(
        cursor,
        """
        SELECT *
        FROM workout_execution_sessions
        WHERE workout_plan_instance_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (plan_instance_id,),
    )

    actual_rows = []
    if execution_session:
        actual_rows = _safe_fetchall(
            cursor,
            """
            SELECT *
            FROM workout_execution_set_actuals
            WHERE workout_execution_session_id = ?
            ORDER BY id
            """,
            (execution_session["id"],),
        )

    conn.close()

    planned_set_count = sum(_planned_set_count(row) for row in planned_rows)
    completed_rows = [row for row in actual_rows if _is_completed(row)]
    skipped_rows = [row for row in actual_rows if _is_truthy(_row_get(row, "skipped"))]

    actual_set_count = len(completed_rows)
    completion_percentage = (
        round((actual_set_count / planned_set_count) * 100, 2)
        if planned_set_count
        else 0.0
    )

    planned_rirs = [
        _planned_rir(row)
        for row in planned_rows
        for _ in range(_planned_set_count(row))
    ]
    actual_rirs = [
        float(_row_get(row, "actual_rir"))
        for row in completed_rows
        if _row_get(row, "actual_rir") is not None
    ]

    sets_below = 0
    sets_inside = 0
    sets_above = 0
    missing_actual_reps = 0
    missing_actual_rir = 0

    for row in completed_rows:
        actual_reps = _row_get(row, "actual_reps")
        actual_rir = _row_get(row, "actual_rir")

        if actual_reps is None:
            missing_actual_reps += 1
        else:
            reps_min = _row_get(row, "planned_reps_min")
            reps_max = _row_get(row, "planned_reps_max")
            if reps_min is not None and actual_reps < reps_min:
                sets_below += 1
            elif reps_max is not None and actual_reps > reps_max:
                sets_above += 1
            else:
                sets_inside += 1

        if actual_rir is None:
            missing_actual_rir += 1

    average_planned_rir = _round_mean(
        [value for value in planned_rirs if value is not None]
    )
    average_actual_rir = _round_mean(actual_rirs)
    rir_deviation = (
        round(average_actual_rir - average_planned_rir, 2)
        if average_planned_rir is not None and average_actual_rir is not None
        else None
    )

    deviation_flags = []
    if not actual_rows:
        deviation_flags.append("empty_completion")
    if actual_set_count < planned_set_count:
        deviation_flags.append("incomplete_logging")
    if skipped_rows:
        deviation_flags.append("skipped_exercises_present")
    if any(
        _row_get(row, "substitution_for_planned_exercise_id") for row in actual_rows
    ):
        deviation_flags.append("substitutions_present")
    if missing_actual_rir:
        deviation_flags.append("missing_actual_rir")
    if missing_actual_reps:
        deviation_flags.append("missing_actual_reps")
    if sets_below:
        deviation_flags.append("reps_below_plan")
    if sets_above:
        deviation_flags.append("reps_above_plan")
    if rir_deviation is not None and rir_deviation <= -1:
        deviation_flags.append("actual_effort_harder_than_planned")
    if rir_deviation is not None and rir_deviation >= 1:
        deviation_flags.append("actual_effort_easier_than_planned")

    return {
        "planned_exercise_count": len(planned_rows),
        "completed_exercise_count": len(
            {
                _row_get(row, "planned_workout_exercise_id")
                for row in completed_rows
                if _row_get(row, "planned_workout_exercise_id") is not None
            }
        ),
        "skipped_exercise_count": len(
            {
                _row_get(row, "planned_workout_exercise_id")
                for row in skipped_rows
                if _row_get(row, "planned_workout_exercise_id") is not None
            }
        ),
        "substituted_exercise_count": len(
            [
                row
                for row in actual_rows
                if _row_get(row, "substitution_for_planned_exercise_id") is not None
            ]
        ),
        "planned_set_count": planned_set_count,
        "actual_set_count": actual_set_count,
        "completed_set_count": actual_set_count,
        "skipped_set_count": len(skipped_rows),
        "completion_percentage": completion_percentage,
        "average_planned_rir": average_planned_rir,
        "average_actual_rir": average_actual_rir,
        "rir_deviation": rir_deviation,
        "sets_below_planned_reps": sets_below,
        "sets_inside_planned_reps": sets_inside,
        "sets_above_planned_reps": sets_above,
        "missing_actual_rir_count": missing_actual_rir,
        "missing_actual_reps_count": missing_actual_reps,
        "deviation_flags": deviation_flags,
    }


def _safe_fetchone(cursor: Any, query: str, params: tuple[Any, ...]) -> Any | None:
    try:
        return cursor.execute(query, params).fetchone()
    except Exception:
        return None


def _safe_fetchall(cursor: Any, query: str, params: tuple[Any, ...]) -> list[Any]:
    try:
        return cursor.execute(query, params).fetchall()
    except Exception:
        return []


def _planned_set_count(row: Any) -> int:
    value = (
        _row_get(row, "sets")
        or _row_get(row, "set_count")
        or _row_get(row, "planned_sets")
        or 1
    )

    return int(value)


def _planned_rir(row: Any) -> float | None:
    rir_min = _row_get(row, "rir_min") or _row_get(row, "planned_rir_min")
    rir_max = _row_get(row, "rir_max") or _row_get(row, "planned_rir_max")

    if rir_min is None and rir_max is None:
        return None

    if rir_min is None:
        return float(rir_max)

    if rir_max is None:
        return float(rir_min)

    return (float(rir_min) + float(rir_max)) / 2


def _is_completed(row: Any) -> bool:
    return _is_truthy(_row_get(row, "completed")) and not _is_truthy(
        _row_get(row, "skipped")
    )


def _is_truthy(value: Any) -> bool:
    return value in (True, 1, "1", "true", "True", "yes", "Yes")


def _row_get(row: Any, field_name: str) -> Any:
    try:
        return row[field_name]
    except (KeyError, IndexError, TypeError):
        return None
