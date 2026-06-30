from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from statistics import mean
from typing import Any

from database import get_connection
from models.workout_set_intelligence_models import (
    WorkoutExerciseSetIndicator,
    WorkoutSetIntelligenceSummary,
    WorkoutSetSessionSummary,
)

WORKOUT_SET_INTELLIGENCE_MODEL_VERSION = "workout_set_intelligence_v1"
DEFAULT_RECENT_COMPLETED_LIMIT = 5
LOAD_DELTA_THRESHOLD_LB = 2.5
SOURCE_TABLES = [
    "workout_plan_instances",
    "planned_workout_exercises",
    "workout_execution_sessions",
    "workout_execution_set_actuals",
]
FORBIDDEN_COACH_LANGUAGE = (
    "overtraining",
    "injury",
    "medical",
    "failed",
    "failure",
    "lack of discipline",
    "poor adherence",
    "automatic deload",
    "must deload",
    "add weight automatically",
    "increase load automatically",
    "programming failure",
)


@dataclass(frozen=True)
class _PlanInstanceRow:
    id: int
    workout_date: str | None
    workout_title: str | None
    date_source: str
    date_source_limited: bool


@dataclass(frozen=True)
class _SessionBuildResult:
    summary: WorkoutSetSessionSummary
    planned_rows: list[dict[str, Any]]
    actual_rows: list[dict[str, Any]]
    plan: _PlanInstanceRow


@dataclass(frozen=True)
class _ExerciseAccumulator:
    exercise_name: str
    plan_instance_ids: set[int]
    planned_set_count: int
    completed_set_count: int
    skipped_set_count: int
    planned_rirs: list[float]
    actual_rirs: list[float]
    actual_reps: list[float]
    set_dates_and_weights: list[tuple[str, float]]
    sets_below: int
    sets_inside: int
    sets_above: int
    missing_actual_reps: int
    missing_actual_rir: int
    missing_actual_weight: int
    reason_codes: list[str]
    limitations: list[str]


def build_workout_set_intelligence(
    user_id: int,
    target_date: str | None = None,
    recent_completed_limit: int = DEFAULT_RECENT_COMPLETED_LIMIT,
) -> WorkoutSetIntelligenceSummary:
    """Build read-only set-aware training intelligence for Daily Coach.

    This service reads completed planned workout executions only. It does not
    use unlinked manual workout logs as planned-vs-actual evidence and does not
    mutate the database.
    """

    target = _parse_date(target_date) if target_date else date.today()
    limit = max(1, int(recent_completed_limit))
    plan_instances = _load_recent_completed_plan_instances(
        user_id=user_id,
        target_date=target,
        limit=limit,
    )

    if not plan_instances:
        return _empty_summary(user_id=user_id, target_date=target.isoformat())

    session_results = [_build_session_summary(plan) for plan in plan_instances]
    session_summaries = [result.summary for result in session_results]
    exercise_indicators = _build_exercise_indicators(session_results)
    overall_completion = _classify_overall_completion(session_summaries)
    overall_effort = _classify_overall_effort(session_summaries)
    overall_rep_range = _classify_overall_rep_range(session_summaries)
    overall_logging = _classify_overall_logging_quality(session_summaries)
    confidence = _classify_summary_confidence(session_summaries)
    reason_codes = _build_summary_reason_codes(
        plan_instances=plan_instances,
        session_summaries=session_summaries,
        exercise_indicators=exercise_indicators,
        confidence=confidence,
    )
    limitations = _build_summary_limitations(session_summaries, confidence)
    source_facts = _build_source_facts(
        completed_execution_count=len(plan_instances),
        overall_completion=overall_completion,
        overall_effort=overall_effort,
        overall_rep_range=overall_rep_range,
        overall_logging=overall_logging,
        confidence=confidence,
    )
    coach_safe_summary = _build_coach_safe_summary(
        completion=overall_completion,
        effort=overall_effort,
        rep_range=overall_rep_range,
        logging_quality=overall_logging,
    )
    _guard_safe_text([coach_safe_summary, *source_facts])

    return WorkoutSetIntelligenceSummary(
        user_id=user_id,
        target_date=target.isoformat(),
        generated_at=datetime.now(UTC).isoformat(),
        source_tables=list(SOURCE_TABLES),
        model_version=WORKOUT_SET_INTELLIGENCE_MODEL_VERSION,
        completed_execution_count=len(plan_instances),
        recent_plan_instance_ids=[plan.id for plan in plan_instances],
        session_summaries=session_summaries,
        exercise_indicators=exercise_indicators,
        overall_completion_indicator=overall_completion,
        overall_effort_indicator=overall_effort,
        overall_rep_range_indicator=overall_rep_range,
        overall_logging_quality=overall_logging,
        confidence=confidence,
        source_facts=source_facts,
        coach_safe_summary=coach_safe_summary,
        reason_codes=_unique(reason_codes),
        limitations=_unique(limitations),
    )


def _empty_summary(user_id: int, target_date: str) -> WorkoutSetIntelligenceSummary:
    return WorkoutSetIntelligenceSummary(
        user_id=user_id,
        target_date=target_date,
        generated_at=datetime.now(UTC).isoformat(),
        source_tables=list(SOURCE_TABLES),
        model_version=WORKOUT_SET_INTELLIGENCE_MODEL_VERSION,
        completed_execution_count=0,
        recent_plan_instance_ids=[],
        session_summaries=[],
        exercise_indicators=[],
        overall_completion_indicator="no_planned_execution_data",
        overall_effort_indicator="unknown",
        overall_rep_range_indicator="unknown",
        overall_logging_quality="unknown",
        confidence="Limited",
        source_facts=[
            "No completed planned workout executions were available for set-aware training indicators."
        ],
        coach_safe_summary=(
            "Recent planned workout execution data is unavailable, so the training read should stay limited."
        ),
        reason_codes=[
            "no_completed_planned_executions",
            "manual_workout_logs_not_used_for_planned_vs_actual",
        ],
        limitations=[
            "No completed planned workout executions were available up to the target date."
        ],
    )


def _load_recent_completed_plan_instances(
    *, user_id: int, target_date: date, limit: int
) -> list[_PlanInstanceRow]:
    conn = get_connection()
    cursor = conn.cursor()
    if not _required_tables_exist(cursor):
        conn.close()
        return []

    wpi_columns = _column_names(cursor, "workout_plan_instances")
    plan_completed_select = (
        "wpi.completed_at AS plan_completed_at"
        if "completed_at" in wpi_columns
        else "NULL AS plan_completed_at"
    )
    rows = cursor.execute(
        f"""
        SELECT wpi.id AS plan_instance_id,
               wpi.title AS workout_title,
               {plan_completed_select},
               wpi.selected_at AS selected_at,
               wpi.created_at AS plan_created_at,
               wes.id AS workout_execution_session_id,
               wes.completed_at AS execution_completed_at,
               ws.workout_date AS workout_session_date
        FROM workout_plan_instances wpi
        LEFT JOIN workout_execution_sessions wes
          ON wes.workout_plan_instance_id = wpi.id
        LEFT JOIN workout_sessions ws
          ON ws.id = wes.workout_session_id
        WHERE wpi.user_id = ?
          AND wpi.status = 'completed'
        ORDER BY wpi.id DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    plans = [_plan_instance_from_row(dict(row)) for row in rows]
    filtered = [
        plan
        for plan in plans
        if plan.workout_date is not None
        and _parse_date(plan.workout_date) <= target_date
    ]
    return sorted(
        filtered,
        key=lambda plan: (plan.workout_date or "", plan.id),
        reverse=True,
    )[:limit]


def _column_names(cursor: Any, table_name: str) -> set[str]:
    rows = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def _required_tables_exist(cursor: Any) -> bool:
    table_names = set(_table_names(cursor))
    return set(SOURCE_TABLES).issubset(table_names)


def _table_names(cursor: Any) -> list[str]:
    rows = cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """).fetchall()
    return [str(row["name"]) for row in rows]


def _plan_instance_from_row(row: dict[str, Any]) -> _PlanInstanceRow:
    fields = [
        ("plan_completed_at", row.get("plan_completed_at"), False),
        ("execution_completed_at", row.get("execution_completed_at"), False),
        ("workout_session_date", row.get("workout_session_date"), True),
        ("selected_at", row.get("selected_at"), True),
        ("plan_created_at", row.get("plan_created_at"), True),
    ]
    for name, value, limited in fields:
        if value:
            return _PlanInstanceRow(
                id=int(row["plan_instance_id"]),
                workout_date=_date_part(value),
                workout_title=row.get("workout_title") or None,
                date_source=name,
                date_source_limited=limited,
            )
    return _PlanInstanceRow(
        id=int(row["plan_instance_id"]),
        workout_date=None,
        workout_title=row.get("workout_title") or None,
        date_source="unknown",
        date_source_limited=True,
    )


def _build_session_summary(plan: _PlanInstanceRow) -> _SessionBuildResult:
    planned_rows = _load_planned_rows(plan.id)
    execution_session = _load_execution_session(plan.id)
    actual_rows = (
        _load_actual_rows(int(execution_session["id"])) if execution_session else []
    )
    summary = _summarize_session(
        plan=plan,
        execution_session=execution_session,
        planned_rows=planned_rows,
        actual_rows=actual_rows,
    )
    return _SessionBuildResult(
        summary=summary,
        planned_rows=planned_rows,
        actual_rows=actual_rows,
        plan=plan,
    )


def _load_planned_rows(plan_instance_id: int) -> list[dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id,
               name,
               sets,
               reps_min,
               reps_max,
               rir_min,
               rir_max
        FROM planned_workout_exercises
        WHERE workout_plan_instance_id = ?
        ORDER BY exercise_order ASC, id ASC
        """,
        (plan_instance_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _load_execution_session(plan_instance_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT id,
               workout_plan_instance_id,
               user_id,
               status,
               workout_session_id,
               completed_at,
               created_at
        FROM workout_execution_sessions
        WHERE workout_plan_instance_id = ?
        ORDER BY COALESCE(completed_at, created_at, '') DESC, id DESC
        LIMIT 1
        """,
        (plan_instance_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _load_actual_rows(workout_execution_session_id: int) -> list[dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id,
               workout_execution_session_id,
               planned_workout_exercise_id,
               workout_session_id,
               workout_set_id,
               exercise_name,
               set_number,
               planned_reps_min,
               planned_reps_max,
               planned_rir_min,
               planned_rir_max,
               actual_reps,
               actual_weight,
               actual_rir,
               completed,
               skipped,
               substitution_for_planned_exercise_id,
               created_at
        FROM workout_execution_set_actuals
        WHERE workout_execution_session_id = ?
        ORDER BY planned_workout_exercise_id ASC, set_number ASC, id ASC
        """,
        (workout_execution_session_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _summarize_session(
    *,
    plan: _PlanInstanceRow,
    execution_session: dict[str, Any] | None,
    planned_rows: list[dict[str, Any]],
    actual_rows: list[dict[str, Any]],
) -> WorkoutSetSessionSummary:
    planned_set_count = sum(_safe_int(row.get("sets")) for row in planned_rows)
    completed_rows = [row for row in actual_rows if _is_completed(row)]
    skipped_rows = [row for row in actual_rows if _is_truthy(row.get("skipped"))]
    completed_set_count = len(completed_rows)
    skipped_set_count = len(skipped_rows)
    completion_percentage = (
        round((completed_set_count / planned_set_count) * 100, 2)
        if planned_set_count
        else None
    )
    planned_rirs = _planned_rirs_for_session(planned_rows, actual_rows)
    actual_rirs = [_safe_float(row.get("actual_rir")) for row in completed_rows]
    actual_rirs = [value for value in actual_rirs if value is not None]
    avg_planned_rir = _round_mean(planned_rirs)
    avg_actual_rir = _round_mean(actual_rirs)
    rir_delta = (
        round(avg_actual_rir - avg_planned_rir, 2)
        if avg_actual_rir is not None and avg_planned_rir is not None
        else None
    )
    rep_counts = _rep_counts(completed_rows)
    missing_reps = sum(1 for row in completed_rows if row.get("actual_reps") is None)
    missing_rir = sum(1 for row in completed_rows if row.get("actual_rir") is None)
    missing_weight = sum(
        1 for row in completed_rows if row.get("actual_weight") is None
    )
    completion_indicator = _classify_completion(
        completion_percentage=completion_percentage,
        completed_execution_count=1,
        planned_set_count=planned_set_count,
        skipped_count=skipped_set_count,
        missing_rows=max(planned_set_count - completed_set_count, 0),
    )
    effort_indicator = _classify_effort(rir_delta, missing_rir, completed_set_count)
    rep_range_indicator = _classify_rep_range(
        below=rep_counts["below"],
        inside=rep_counts["inside"],
        above=rep_counts["above"],
        missing_actual_reps=missing_reps,
        completed_set_count=completed_set_count,
    )
    logging_quality = _classify_logging_quality(
        planned_set_count=planned_set_count,
        completed_set_count=completed_set_count,
        missing_actual_reps=missing_reps,
        missing_actual_rir=missing_rir,
        missing_actual_weight=missing_weight,
    )
    reason_codes = _session_reason_codes(
        plan=plan,
        execution_session=execution_session,
        planned_set_count=planned_set_count,
        completed_set_count=completed_set_count,
        skipped_set_count=skipped_set_count,
        missing_actual_reps=missing_reps,
        missing_actual_rir=missing_rir,
        missing_actual_weight=missing_weight,
        rep_counts=rep_counts,
        effort_indicator=effort_indicator,
    )
    limitations = _session_limitations(
        execution_session=execution_session,
        planned_set_count=planned_set_count,
        completed_set_count=completed_set_count,
        missing_actual_reps=missing_reps,
        missing_actual_rir=missing_rir,
        missing_actual_weight=missing_weight,
        date_source_limited=plan.date_source_limited,
    )
    return WorkoutSetSessionSummary(
        workout_plan_instance_id=plan.id,
        workout_execution_session_id=(
            int(execution_session["id"]) if execution_session else None
        ),
        workout_date=plan.workout_date,
        workout_title=plan.workout_title,
        planned_exercise_count=len(planned_rows),
        planned_set_count=planned_set_count,
        completed_set_count=completed_set_count,
        skipped_set_count=skipped_set_count,
        completion_percentage=completion_percentage,
        average_planned_rir=avg_planned_rir,
        average_actual_rir=avg_actual_rir,
        rir_delta=rir_delta,
        sets_below_planned_reps=rep_counts["below"],
        sets_inside_planned_reps=rep_counts["inside"],
        sets_above_planned_reps=rep_counts["above"],
        missing_actual_reps_count=missing_reps,
        missing_actual_rir_count=missing_rir,
        missing_actual_weight_count=missing_weight,
        completion_indicator=completion_indicator,
        effort_indicator=effort_indicator,
        rep_range_indicator=rep_range_indicator,
        logging_quality=logging_quality,
        reason_codes=reason_codes,
        limitations=limitations,
    )


def _planned_rirs_for_session(
    planned_rows: list[dict[str, Any]], actual_rows: list[dict[str, Any]]
) -> list[float]:
    if actual_rows:
        values = []
        for row in actual_rows:
            midpoint = _planned_rir_midpoint(row)
            if midpoint is not None:
                values.append(midpoint)
        if values:
            return values
    values = []
    for row in planned_rows:
        midpoint = _planned_rir_midpoint(row)
        if midpoint is not None:
            values.extend([midpoint] * _safe_int(row.get("sets")))
    return values


def _rep_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"below": 0, "inside": 0, "above": 0}
    for row in rows:
        actual = _safe_float(row.get("actual_reps"))
        if actual is None:
            continue
        reps_min = _safe_float(row.get("planned_reps_min"))
        reps_max = _safe_float(row.get("planned_reps_max"))
        if reps_min is not None and actual < reps_min:
            counts["below"] += 1
        elif reps_max is not None and actual > reps_max:
            counts["above"] += 1
        else:
            counts["inside"] += 1
    return counts


def _build_exercise_indicators(
    session_results: list[_SessionBuildResult],
) -> list[WorkoutExerciseSetIndicator]:
    accumulators: dict[str, dict[str, Any]] = {}
    for result in session_results:
        for planned in result.planned_rows:
            name = str(planned.get("name") or "Unknown exercise")
            acc = _exercise_accumulator(accumulators, name)
            acc["plan_instance_ids"].add(result.plan.id)
            acc["planned_set_count"] += _safe_int(planned.get("sets"))
            midpoint = _planned_rir_midpoint(planned)
            if midpoint is not None:
                acc["planned_rirs"].extend([midpoint] * _safe_int(planned.get("sets")))
        for actual in result.actual_rows:
            name = str(actual.get("exercise_name") or "Unknown exercise")
            acc = _exercise_accumulator(accumulators, name)
            acc["plan_instance_ids"].add(result.plan.id)
            if _is_truthy(actual.get("skipped")):
                acc["skipped_set_count"] += 1
            if not _is_completed(actual):
                continue
            acc["completed_set_count"] += 1
            actual_reps = _safe_float(actual.get("actual_reps"))
            actual_rir = _safe_float(actual.get("actual_rir"))
            actual_weight = _safe_float(actual.get("actual_weight"))
            planned_rir = _planned_rir_midpoint(actual)
            if actual_reps is None:
                acc["missing_actual_reps"] += 1
            else:
                acc["actual_reps"].append(actual_reps)
            if actual_rir is None:
                acc["missing_actual_rir"] += 1
            else:
                acc["actual_rirs"].append(actual_rir)
            if actual_weight is None:
                acc["missing_actual_weight"] += 1
            else:
                acc["set_dates_and_weights"].append(
                    (result.plan.workout_date or "", actual_weight)
                )
            if planned_rir is not None:
                acc["planned_rirs"].append(planned_rir)
            rep_counts = _rep_counts([actual])
            acc["sets_below"] += rep_counts["below"]
            acc["sets_inside"] += rep_counts["inside"]
            acc["sets_above"] += rep_counts["above"]
            if actual.get("substitution_for_planned_exercise_id") is not None:
                acc["reason_codes"].append("substitution_present_for_exercise")

    indicators = []
    for name in sorted(accumulators):
        indicators.append(_build_exercise_indicator(name, accumulators[name]))
    return indicators


def _exercise_accumulator(
    accumulators: dict[str, dict[str, Any]], name: str
) -> dict[str, Any]:
    if name not in accumulators:
        accumulators[name] = {
            "plan_instance_ids": set(),
            "planned_set_count": 0,
            "completed_set_count": 0,
            "skipped_set_count": 0,
            "planned_rirs": [],
            "actual_rirs": [],
            "actual_reps": [],
            "set_dates_and_weights": [],
            "sets_below": 0,
            "sets_inside": 0,
            "sets_above": 0,
            "missing_actual_reps": 0,
            "missing_actual_rir": 0,
            "missing_actual_weight": 0,
            "reason_codes": [],
            "limitations": [],
        }
    return accumulators[name]


def _build_exercise_indicator(
    name: str, acc: dict[str, Any]
) -> WorkoutExerciseSetIndicator:
    planned_set_count = int(acc["planned_set_count"])
    completed_set_count = int(acc["completed_set_count"])
    skipped_set_count = int(acc["skipped_set_count"])
    completion_percentage = (
        round((completed_set_count / planned_set_count) * 100, 2)
        if planned_set_count
        else None
    )
    avg_actual_reps = _round_mean(acc["actual_reps"])
    avg_actual_rir = _round_mean(acc["actual_rirs"])
    avg_planned_rir = _round_mean(acc["planned_rirs"])
    rir_delta = (
        round(avg_actual_rir - avg_planned_rir, 2)
        if avg_actual_rir is not None and avg_planned_rir is not None
        else None
    )
    latest_weight, prior_weight, weight_delta = _load_comparison(
        acc["set_dates_and_weights"]
    )
    completion_indicator = _classify_completion(
        completion_percentage=completion_percentage,
        completed_execution_count=len(acc["plan_instance_ids"]),
        planned_set_count=planned_set_count,
        skipped_count=skipped_set_count,
        missing_rows=max(planned_set_count - completed_set_count, 0),
    )
    effort_indicator = _classify_effort(
        rir_delta,
        int(acc["missing_actual_rir"]),
        completed_set_count,
    )
    rep_range_indicator = _classify_rep_range(
        below=int(acc["sets_below"]),
        inside=int(acc["sets_inside"]),
        above=int(acc["sets_above"]),
        missing_actual_reps=int(acc["missing_actual_reps"]),
        completed_set_count=completed_set_count,
    )
    load_indicator = _classify_load(weight_delta, latest_weight, prior_weight)
    confidence = _classify_exercise_confidence(
        planned_session_count=len(acc["plan_instance_ids"]),
        completed_set_count=completed_set_count,
        missing_actual_reps=int(acc["missing_actual_reps"]),
        missing_actual_rir=int(acc["missing_actual_rir"]),
        missing_actual_weight=int(acc["missing_actual_weight"]),
        completion_indicator=completion_indicator,
        effort_indicator=effort_indicator,
        rep_range_indicator=rep_range_indicator,
    )
    reason_codes = list(acc["reason_codes"])
    limitations = list(acc["limitations"])
    if confidence in {"Limited", "Low"}:
        reason_codes.append("exercise_indicator_confidence_limited")
    if int(acc["missing_actual_reps"]):
        reason_codes.append("missing_actual_reps_lowers_confidence")
    if int(acc["missing_actual_rir"]):
        reason_codes.append("missing_actual_rir_lowers_confidence")
    if int(acc["missing_actual_weight"]):
        reason_codes.append("missing_actual_weight_limits_load_indicator")
    if load_indicator == "insufficient_comparable_load_data":
        limitations.append("Comparable load data is limited for this exercise.")
    return WorkoutExerciseSetIndicator(
        exercise_name=name,
        planned_session_count=len(acc["plan_instance_ids"]),
        planned_set_count=planned_set_count,
        completed_set_count=completed_set_count,
        skipped_set_count=skipped_set_count,
        completion_percentage=completion_percentage,
        latest_actual_weight=latest_weight,
        prior_actual_weight=prior_weight,
        weight_delta=weight_delta,
        average_actual_reps=avg_actual_reps,
        average_actual_rir=avg_actual_rir,
        average_planned_rir=avg_planned_rir,
        rir_delta=rir_delta,
        sets_below_planned_reps=int(acc["sets_below"]),
        sets_inside_planned_reps=int(acc["sets_inside"]),
        sets_above_planned_reps=int(acc["sets_above"]),
        completion_indicator=completion_indicator,
        effort_indicator=effort_indicator,
        rep_range_indicator=rep_range_indicator,
        load_indicator=load_indicator,
        confidence=confidence,
        reason_codes=_unique(reason_codes),
        limitations=_unique(limitations),
    )


def _load_comparison(
    values: list[tuple[str, float]],
) -> tuple[float | None, float | None, float | None]:
    dated = [(date_value, weight) for date_value, weight in values if date_value]
    if len(dated) < 2:
        return None, None, None
    by_date: dict[str, list[float]] = defaultdict(list)
    for date_value, weight in dated:
        by_date[date_value].append(weight)
    ordered_dates = sorted(by_date)
    if len(ordered_dates) < 2:
        return None, None, None
    latest = round(mean(by_date[ordered_dates[-1]]), 1)
    prior = round(mean(by_date[ordered_dates[-2]]), 1)
    return latest, prior, round(latest - prior, 1)


def _classify_completion(
    *,
    completion_percentage: float | None,
    completed_execution_count: int,
    planned_set_count: int,
    skipped_count: int,
    missing_rows: int,
) -> str:
    if planned_set_count == 0:
        return "unknown"
    if completed_execution_count == 0:
        return "no_planned_execution_data"
    if completed_execution_count == 1 and missing_rows:
        return "limited_data"
    if completion_percentage is None:
        return "limited_data"
    if completion_percentage < 50 or skipped_count >= 2:
        return "frequently_incomplete"
    if completion_percentage < 85:
        return "partially_completed"
    if skipped_count:
        return "partially_completed"
    return "mostly_completed"


def _classify_effort(
    rir_delta: float | None, missing_actual_rir: int, completed_set_count: int
) -> str:
    if completed_set_count == 0:
        return "unknown"
    if rir_delta is None:
        return "limited_effort_data"
    if missing_actual_rir >= max(1, completed_set_count // 2):
        return "limited_effort_data"
    if rir_delta <= -1.0:
        return "harder_than_planned"
    if rir_delta >= 1.0:
        return "easier_than_planned"
    return "as_planned"


def _classify_rep_range(
    *,
    below: int,
    inside: int,
    above: int,
    missing_actual_reps: int,
    completed_set_count: int,
) -> str:
    if completed_set_count == 0:
        return "unknown"
    if missing_actual_reps >= max(1, completed_set_count // 2):
        return "limited_rep_data"
    if below >= 2 and above >= 2:
        return "mixed"
    if below >= 2 and below > above:
        return "often_below_range"
    if above >= 2 and above > below:
        return "often_above_range"
    if inside >= below + above:
        return "mostly_inside_range"
    if below and above:
        return "mixed"
    if below > above:
        return "often_below_range"
    if above > below:
        return "often_above_range"
    return "mostly_inside_range"


def _classify_load(
    weight_delta: float | None,
    latest_weight: float | None,
    prior_weight: float | None,
) -> str:
    if latest_weight is None or prior_weight is None or weight_delta is None:
        return "insufficient_comparable_load_data"
    if weight_delta >= LOAD_DELTA_THRESHOLD_LB:
        return "increasing"
    if weight_delta <= -LOAD_DELTA_THRESHOLD_LB:
        return "decreasing"
    return "stable"


def _classify_logging_quality(
    *,
    planned_set_count: int,
    completed_set_count: int,
    missing_actual_reps: int,
    missing_actual_rir: int,
    missing_actual_weight: int,
) -> str:
    if planned_set_count == 0:
        return "unknown"
    missing_rows = max(planned_set_count - completed_set_count, 0)
    missing_fields = missing_actual_reps + missing_actual_rir + missing_actual_weight
    if completed_set_count == 0:
        return "limited"
    if missing_rows or missing_fields >= completed_set_count:
        return "incomplete"
    if missing_fields:
        return "mostly_complete"
    return "complete"


def _classify_overall_completion(sessions: list[WorkoutSetSessionSummary]) -> str:
    if not sessions:
        return "no_planned_execution_data"
    percentages = [
        s.completion_percentage for s in sessions if s.completion_percentage is not None
    ]
    if not percentages:
        return "limited_data"
    avg_completion = mean(percentages)
    total_skips = sum(s.skipped_set_count for s in sessions)
    return _classify_completion(
        completion_percentage=avg_completion,
        completed_execution_count=len(sessions),
        planned_set_count=sum(s.planned_set_count for s in sessions),
        skipped_count=total_skips,
        missing_rows=sum(
            max(s.planned_set_count - s.completed_set_count, 0) for s in sessions
        ),
    )


def _classify_overall_effort(sessions: list[WorkoutSetSessionSummary]) -> str:
    indicators = [
        s.effort_indicator for s in sessions if s.effort_indicator != "unknown"
    ]
    if not indicators:
        return "unknown"
    if "limited_effort_data" in indicators and len(set(indicators)) == 1:
        return "limited_effort_data"
    concrete = [value for value in indicators if value != "limited_effort_data"]
    if not concrete:
        return "limited_effort_data"
    if len(set(concrete)) > 1:
        return "mixed"
    return concrete[0]


def _classify_overall_rep_range(sessions: list[WorkoutSetSessionSummary]) -> str:
    below = sum(s.sets_below_planned_reps for s in sessions)
    inside = sum(s.sets_inside_planned_reps for s in sessions)
    above = sum(s.sets_above_planned_reps for s in sessions)
    missing = sum(s.missing_actual_reps_count for s in sessions)
    completed = sum(s.completed_set_count for s in sessions)
    return _classify_rep_range(
        below=below,
        inside=inside,
        above=above,
        missing_actual_reps=missing,
        completed_set_count=completed,
    )


def _classify_overall_logging_quality(sessions: list[WorkoutSetSessionSummary]) -> str:
    if not sessions:
        return "unknown"
    qualities = [s.logging_quality for s in sessions]
    if "limited" in qualities:
        return "limited"
    if "incomplete" in qualities:
        return "incomplete"
    if "mostly_complete" in qualities:
        return "mostly_complete"
    if all(value == "complete" for value in qualities):
        return "complete"
    return "unknown"


def _classify_exercise_confidence(
    *,
    planned_session_count: int,
    completed_set_count: int,
    missing_actual_reps: int,
    missing_actual_rir: int,
    missing_actual_weight: int,
    completion_indicator: str,
    effort_indicator: str,
    rep_range_indicator: str,
) -> str:
    if completed_set_count == 0:
        return "Limited"
    if planned_session_count == 1:
        return "Low"
    if missing_actual_reps or missing_actual_rir:
        return "Low"
    if missing_actual_weight and planned_session_count < 3:
        return "Low"
    if "limited" in {completion_indicator, effort_indicator, rep_range_indicator}:
        return "Low"
    return "Moderate"


def _classify_summary_confidence(sessions: list[WorkoutSetSessionSummary]) -> str:
    if not sessions:
        return "Limited"
    missing_fields = sum(
        s.missing_actual_reps_count
        + s.missing_actual_rir_count
        + s.missing_actual_weight_count
        for s in sessions
    )
    incomplete_sessions = sum(
        1 for s in sessions if s.logging_quality in {"incomplete", "limited"}
    )
    if len(sessions) == 1:
        return "Limited" if incomplete_sessions else "Low"
    if incomplete_sessions or missing_fields:
        return "Low"
    if len(sessions) >= 2:
        return "Moderate"
    return "Low"


def _session_reason_codes(
    *,
    plan: _PlanInstanceRow,
    execution_session: dict[str, Any] | None,
    planned_set_count: int,
    completed_set_count: int,
    skipped_set_count: int,
    missing_actual_reps: int,
    missing_actual_rir: int,
    missing_actual_weight: int,
    rep_counts: dict[str, int],
    effort_indicator: str,
) -> list[str]:
    reason_codes = ["completed_planned_execution_used"]
    if execution_session is None:
        reason_codes.append("execution_session_missing")
    if plan.date_source_limited:
        reason_codes.append(f"date_resolved_from_{plan.date_source}")
    if completed_set_count < planned_set_count:
        reason_codes.append("incomplete_set_logging_lowers_confidence")
    if skipped_set_count:
        reason_codes.append("skipped_sets_lowers_confidence")
    if missing_actual_reps:
        reason_codes.append("missing_actual_reps_lowers_confidence")
    if missing_actual_rir:
        reason_codes.append("missing_actual_rir_lowers_confidence")
    if missing_actual_weight:
        reason_codes.append("missing_actual_weight_limits_load_indicator")
    if rep_counts["below"]:
        reason_codes.append("sets_below_planned_reps")
    if rep_counts["above"]:
        reason_codes.append("sets_above_planned_reps")
    if effort_indicator == "harder_than_planned":
        reason_codes.append("actual_effort_harder_than_planned")
    if effort_indicator == "easier_than_planned":
        reason_codes.append("actual_effort_easier_than_planned")
    if (
        any(
            row.get("substitution_for_planned_exercise_id") is not None
            for row in _load_actual_rows(int(execution_session["id"]))
        )
        if execution_session
        else False
    ):
        reason_codes.append("substitution_lowers_confidence")
    return _unique(reason_codes)


def _session_limitations(
    *,
    execution_session: dict[str, Any] | None,
    planned_set_count: int,
    completed_set_count: int,
    missing_actual_reps: int,
    missing_actual_rir: int,
    missing_actual_weight: int,
    date_source_limited: bool,
) -> list[str]:
    limitations = []
    if execution_session is None:
        limitations.append(
            "No execution session row was linked to this completed plan instance."
        )
    if completed_set_count < planned_set_count:
        limitations.append("Some planned sets were not logged as completed.")
    if missing_actual_reps:
        limitations.append("Some completed sets are missing actual reps.")
    if missing_actual_rir:
        limitations.append("Some completed sets are missing actual RIR.")
    if missing_actual_weight:
        limitations.append("Some completed sets are missing actual weight.")
    if date_source_limited:
        limitations.append("Workout date used fallback date resolution.")
    return limitations


def _build_summary_reason_codes(
    *,
    plan_instances: list[_PlanInstanceRow],
    session_summaries: list[WorkoutSetSessionSummary],
    exercise_indicators: list[WorkoutExerciseSetIndicator],
    confidence: str,
) -> list[str]:
    reason_codes = [
        "completed_planned_executions_only",
        "manual_workout_logs_not_used_for_planned_vs_actual",
    ]
    if len(plan_instances) == 1:
        reason_codes.append("single_completed_execution_limited_confidence")
    if len(plan_instances) > 1:
        reason_codes.append("multiple_completed_executions_available")
    if confidence in {"Limited", "Low"}:
        reason_codes.append("workout_set_intelligence_confidence_limited")
    for session in session_summaries:
        reason_codes.extend(session.reason_codes)
    for indicator in exercise_indicators:
        reason_codes.extend(indicator.reason_codes)
    return _unique(reason_codes)


def _build_summary_limitations(
    sessions: list[WorkoutSetSessionSummary], confidence: str
) -> list[str]:
    limitations = []
    if confidence in {"Limited", "Low"}:
        limitations.append(
            "Workout set intelligence confidence is limited by available logs."
        )
    for session in sessions:
        limitations.extend(session.limitations)
    return _unique(limitations)


def _build_source_facts(
    *,
    completed_execution_count: int,
    overall_completion: str,
    overall_effort: str,
    overall_rep_range: str,
    overall_logging: str,
    confidence: str,
) -> list[str]:
    return [
        f"Recent planned workout executions reviewed: {completed_execution_count}.",
        f"Completion indicator: {overall_completion}.",
        f"Effort indicator: {overall_effort}.",
        f"Rep range indicator: {overall_rep_range}.",
        f"Workout logging quality: {overall_logging}.",
        f"Workout set intelligence confidence: {confidence}.",
    ]


def _build_coach_safe_summary(
    *, completion: str, effort: str, rep_range: str, logging_quality: str
) -> str:
    if completion == "no_planned_execution_data":
        return "Recent planned workout execution data is unavailable, so the training read should stay limited."
    if logging_quality in {"limited", "incomplete"}:
        return "Recent workout logs are usable only cautiously because set, rep, RIR, or weight details are incomplete."
    if effort == "harder_than_planned":
        return "Recent logged sets show the work may have felt harder than planned, so the training read should stay conservative."
    if rep_range == "often_below_range":
        return "Recent sets often landed below the planned rep range, which is worth reviewing before changing the plan."
    if completion == "mostly_completed" and effort == "as_planned":
        return "Recent logged sets mostly matched the written plan, with effort close to the planned RIR range."
    return "Recent planned workout logs provide a cautious set-level training indicator for the Daily Coach snapshot."


def _planned_rir_midpoint(row: dict[str, Any]) -> float | None:
    minimum = _safe_float(row.get("planned_rir_min") or row.get("rir_min"))
    maximum = _safe_float(row.get("planned_rir_max") or row.get("rir_max"))
    if minimum is None and maximum is None:
        return None
    if minimum is None:
        return maximum
    if maximum is None:
        return minimum
    return round((minimum + maximum) / 2, 2)


def _is_completed(row: dict[str, Any]) -> bool:
    return _is_truthy(row.get("completed")) and not _is_truthy(row.get("skipped"))


def _is_truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _safe_int(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _round_mean(values: Iterable[float]) -> float | None:
    cleaned = [float(value) for value in values if value is not None]
    if not cleaned:
        return None
    return round(mean(cleaned), 2)


def _date_part(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)[:10]


def _parse_date(value: str | None) -> date:
    if not value:
        return date.today()
    return date.fromisoformat(str(value)[:10])


def _guard_safe_text(values: list[str]) -> None:
    serialized = "\n".join(values).lower()
    found = [term for term in FORBIDDEN_COACH_LANGUAGE if term in serialized]
    if found:
        raise ValueError(
            f"Workout set intelligence text contains forbidden terms: {found}"
        )


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
