# =====================================
# Imports
# =====================================

from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

API_BASE_URL = "http://127.0.0.1:8000"


def api_get(path: str, params: dict | None = None) -> dict:
    response = requests.get(
        f"{API_BASE_URL}{path}",
        params=params,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict | None = None) -> dict:
    response = requests.post(
        f"{API_BASE_URL}{path}",
        json=payload or {},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def api_put(path: str, payload: dict | None = None) -> dict:
    response = requests.put(
        f"{API_BASE_URL}{path}",
        json=payload or {},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def api_patch(path: str, payload: dict | None = None) -> dict:
    response = requests.patch(
        f"{API_BASE_URL}{path}",
        json=payload or {},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def humanize_label(value: str | None) -> str:
    if not value:
        return "Unknown"

    return value.replace("_", " ").title()


def scenario_display_name(scenario: str | None) -> str:
    labels = {
        "recovery_limited": "Recovery Priority",
        "aligned_managed": "Stable / Managed",
        "nutrition_training_mismatch": "Nutrition + Training Mismatch",
        "improving_after_deload": "Improving After Deload",
        "data_quality_limited": "Data Quality Limited",
    }

    return labels.get(scenario or "", humanize_label(scenario))


def format_range(
    minimum: int | float | None,
    maximum: int | float | None,
    unit: str,
) -> str | None:
    if minimum is None or maximum is None:
        return None

    return f"{minimum}-{maximum} {unit}"


def display_nutrition_targets(nutrition_targets: dict) -> None:
    st.subheader("Nutrition Targets")

    display_message = nutrition_targets.get("nutrition_display_message")
    confidence = nutrition_targets.get("confidence")

    if confidence == "Limited":
        st.info(
            display_message
            or "Nutrition targets are limited until logging is more complete. "
            "Focus on verifying entries and improving consistency first."
        )
        return

    target_rows = []

    if nutrition_targets.get("allow_calorie_targets"):
        calorie_range = format_range(
            nutrition_targets.get("calorie_target_min"),
            nutrition_targets.get("calorie_target_max"),
            "calories/day",
        )
        if calorie_range:
            target_rows.append(
                {
                    "Target": "Calories",
                    "Range": calorie_range,
                }
            )

    if nutrition_targets.get("allow_protein_targets"):
        protein_range = format_range(
            nutrition_targets.get("protein_grams_min"),
            nutrition_targets.get("protein_grams_max"),
            "g/day",
        )
        if protein_range:
            target_rows.append(
                {
                    "Target": "Protein",
                    "Range": protein_range,
                }
            )

    if nutrition_targets.get("allow_carbohydrate_targets"):
        carbohydrate_range = format_range(
            nutrition_targets.get("carbohydrate_grams_min"),
            nutrition_targets.get("carbohydrate_grams_max"),
            "g/day",
        )
        if carbohydrate_range:
            target_rows.append(
                {
                    "Target": "Carbohydrates",
                    "Range": carbohydrate_range,
                }
            )

    if nutrition_targets.get("allow_fat_targets"):
        fat_range = format_range(
            nutrition_targets.get("fat_grams_min"),
            nutrition_targets.get("fat_grams_max"),
            "g/day",
        )
        if fat_range:
            target_rows.append(
                {
                    "Target": "Fat",
                    "Range": fat_range,
                }
            )

    if target_rows:
        st.dataframe(
            pd.DataFrame(target_rows),
            width="stretch",
            hide_index=True,
        )
        if display_message:
            st.caption(display_message)
    else:
        st.info(
            display_message
            or "Nutrition targets are limited until logging is more complete. "
            "Focus on verifying entries and improving consistency first."
        )


def display_training_constraints(training_constraints: dict) -> None:
    recommended_rir_min = training_constraints.get("recommended_rir_min")
    recommended_rir_max = training_constraints.get("recommended_rir_max")

    if recommended_rir_min is not None and recommended_rir_max is not None:
        st.caption(
            f"Recommended effort today: RIR {recommended_rir_min}-{recommended_rir_max}"
        )

    low_rir_guidance = training_constraints.get("low_rir_guidance")
    progression_guidance = training_constraints.get("progression_guidance")
    recovery_constraint = training_constraints.get("recovery_constraint")

    if low_rir_guidance:
        st.write(f"**Effort guidance:** {low_rir_guidance}")

    if progression_guidance:
        st.write(f"**Progression guidance:** {progression_guidance}")

    if recovery_constraint:
        st.write(f"**Recovery constraint:** {recovery_constraint}")


def workout_exercise_role_label(index: int, exercise: dict) -> str:
    if index == 0:
        return "Main Lower / Primary Movement"

    if index == 1:
        return "Main Push"

    if index == 2:
        return "Main Pull"

    if index == 3:
        return "Accessory / Core / Conditioning"

    return f"Additional Movement {index + 1}"


def format_workout_range(
    minimum: int | float | None,
    maximum: int | float | None,
    suffix: str = "",
) -> str:
    if minimum is None and maximum is None:
        return "Unknown"

    if minimum is None:
        return f"Up to {maximum}{suffix}"

    if maximum is None:
        return f"{minimum}+{suffix}"

    if minimum == maximum:
        return f"{minimum}{suffix}"

    return f"{minimum}-{maximum}{suffix}"


def format_equipment_required(exercise: dict) -> str:
    equipment_required = exercise.get("equipment_required") or []

    if not equipment_required:
        return "Bodyweight / none"

    return ", ".join(
        equipment_display_name(equipment) for equipment in equipment_required
    )


def display_workout_plan_preview(
    workout_plan: dict, user_id: int | None = None
) -> None:
    title = workout_plan.get("title", "Workout Plan Preview")
    session_focus = workout_plan.get("session_focus", "No focus available.")
    duration_minutes = workout_plan.get("duration_minutes", "Unknown")
    warmup = workout_plan.get("warmup")
    cooldown = workout_plan.get("cooldown")
    progression_guidance = workout_plan.get("progression_guidance")
    rationale = workout_plan.get("rationale")
    confidence = workout_plan.get("confidence", "Unknown")
    exercises = workout_plan.get("exercises") or []

    st.subheader("Plan Summary")

    st.markdown(f"### {title}")

    col1, col2, col3 = st.columns(3)

    col1.metric("Duration", f"{duration_minutes} min")
    col2.metric("Confidence", confidence)
    col3.metric("Exercises", len(exercises))

    st.write(f"**Session focus:** {session_focus}")

    if user_id is not None:
        display_workout_plan_explanation(user_id)

    st.subheader("Workout Exercises")

    if not exercises:
        st.warning("No exercises are available for this workout preview.")
    else:
        exercise_rows = []

        for index, exercise in enumerate(exercises):
            role = workout_exercise_role_label(index, exercise)
            reps = format_workout_range(
                exercise.get("reps_min"),
                exercise.get("reps_max"),
            )
            rir = format_workout_range(
                exercise.get("rir_min"),
                exercise.get("rir_max"),
            )

            exercise_rows.append(
                {
                    "Slot": role,
                    "Exercise": exercise.get("name", "Unknown"),
                    "Sets": exercise.get("sets", "Unknown"),
                    "Reps": reps,
                    "RIR Range": rir,
                    "Equipment": format_equipment_required(exercise),
                    "Notes": exercise.get("notes", ""),
                }
            )

        st.dataframe(
            pd.DataFrame(exercise_rows),
            width="stretch",
            hide_index=True,
        )

        for index, exercise in enumerate(exercises):
            role = workout_exercise_role_label(index, exercise)
            exercise_name = exercise.get("name", "Unknown")

            with st.expander(f"{role}: {exercise_name}", expanded=False):
                col1, col2, col3, col4 = st.columns(4)

                col1.metric("Sets", exercise.get("sets", "Unknown"))
                col2.metric(
                    "Reps",
                    format_workout_range(
                        exercise.get("reps_min"),
                        exercise.get("reps_max"),
                    ),
                )
                col3.metric(
                    "RIR",
                    format_workout_range(
                        exercise.get("rir_min"),
                        exercise.get("rir_max"),
                    ),
                )
                col4.metric("Equipment", format_equipment_required(exercise))

                notes = exercise.get("notes")
                if notes:
                    st.write(f"**Notes:** {notes}")

    with st.expander("Why this plan", expanded=False):
        if rationale:
            st.write(rationale)
        else:
            st.info("No rationale was returned for this workout preview.")

    with st.expander("Warmup, progression, and cooldown guidance", expanded=False):
        if warmup:
            st.write(f"**Warmup:** {warmup}")

        if progression_guidance:
            st.write(f"**Progression guidance:** {progression_guidance}")

        if cooldown:
            st.write(f"**Cooldown:** {cooldown}")

        if not any([warmup, progression_guidance, cooldown]):
            st.info("No additional guidance was returned for this workout preview.")


def get_workout_explanation_for_user(user_id: int) -> dict | None:
    """Fetch the public-safe workout explanation and cache it by user.

    The public endpoint intentionally returns explanation copy only. It does not
    return the approved workout plan, raw output, provider internals, runtime
    metadata, or prompt/context details.
    """
    cache = st.session_state.workout_explanation_by_user
    errors = st.session_state.workout_explanation_error_by_user

    if user_id in cache:
        errors.pop(user_id, None)
        return cache[user_id]

    try:
        explanation_data = api_get(f"/workout-plans/preview/{user_id}/explanation")
        cache[user_id] = explanation_data
        errors.pop(user_id, None)
        return explanation_data
    except requests.RequestException as exc:
        errors[user_id] = extract_api_error_message(exc)
        return None


def display_workout_plan_explanation(user_id: int) -> None:
    st.markdown("#### Coach Explanation")
    st.caption(
        "This explains the already-approved workout. It does not change the "
        "exercises, sets, reps, RIR, equipment, progression, deload, or nutrition "
        "decisions."
    )

    explanation_data = get_workout_explanation_for_user(user_id)
    explanation_error = st.session_state.workout_explanation_error_by_user.get(user_id)

    if explanation_error and not explanation_data:
        st.info(f"Coach explanation is unavailable right now: {explanation_error}")
        return

    if not explanation_data or not explanation_data.get("success"):
        st.info("Coach explanation is not available for this workout preview yet.")
        return

    explanation = explanation_data.get("approved_workout_explanation") or {}

    if not explanation:
        st.info("Coach explanation is not available for this workout preview yet.")
        return

    session_summary = explanation.get("session_summary")
    why_this_fits_today = explanation.get("why_this_fits_today")
    focus_cue = explanation.get("focus_cue")
    recovery_context = explanation.get("recovery_context")
    nutrition_or_logging_context = explanation.get("nutrition_or_logging_context")
    confidence = explanation.get("confidence") or explanation_data.get("confidence")

    if session_summary:
        st.write(f"**Session summary:** {session_summary}")

    if focus_cue:
        st.info(f"**Focus cue:** {focus_cue}")

    with st.expander("Why this workout?", expanded=False):
        if why_this_fits_today:
            st.write("**Why this fits today:**")
            st.write(why_this_fits_today)

        if recovery_context:
            st.write("**Recovery context:**")
            st.write(recovery_context)

        if nutrition_or_logging_context:
            st.write("**Nutrition/logging context:**")
            st.write(nutrition_or_logging_context)

        if confidence:
            st.caption(f"Confidence: {confidence}")

    if st.session_state.get("developer_mode", False):
        safe_debug_response = {
            "success": explanation_data.get("success"),
            "user_id": explanation_data.get("user_id"),
            "scenario": explanation_data.get("scenario"),
            "confidence": explanation_data.get("confidence"),
            "approved_workout_explanation": explanation,
        }
        developer_details(
            "Developer details: public workout explanation",
            safe_debug_response,
        )


def extract_api_error_message(exc: requests.RequestException) -> str:
    response = getattr(exc, "response", None)

    if response is None:
        return str(exc)

    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = response.text

    if detail:
        return str(detail)

    return str(exc)


def display_planned_exercises(
    planned_exercises: list[dict],
    active_substitutions: dict[int, dict] | None = None,
) -> None:
    if not planned_exercises:
        st.warning("No planned exercises were returned.")
        return

    active_substitutions = active_substitutions or {}
    planned_rows = []

    for exercise in planned_exercises:
        reps_min = exercise.get("reps_min")
        reps_max = exercise.get("reps_max")
        rir_min = exercise.get("rir_min")
        rir_max = exercise.get("rir_max")
        equipment_required = exercise.get("equipment_required") or []
        planned_exercise_id = exercise.get("id")
        active_substitution = None

        if planned_exercise_id is not None:
            try:
                active_substitution = active_substitutions.get(int(planned_exercise_id))
            except (TypeError, ValueError):
                active_substitution = None

        original_exercise_name = exercise.get("name", "Unknown")
        active_exercise_name = original_exercise_name
        substitution_status = "Original"

        if active_substitution:
            active_exercise_name = active_substitution.get(
                "replacement_exercise_name",
                active_exercise_name,
            )
            substitution_status = "Substituted"

        planned_rows.append(
            {
                "Order": exercise.get("exercise_order", "Unknown"),
                "Original Exercise": original_exercise_name,
                "Active Exercise": active_exercise_name,
                "Status": substitution_status,
                "Sets": exercise.get("sets", "Unknown"),
                "Reps": (
                    f"{reps_min}-{reps_max}"
                    if reps_min is not None and reps_max is not None
                    else "Unknown"
                ),
                "RIR": (
                    f"{rir_min}-{rir_max}"
                    if rir_min is not None and rir_max is not None
                    else "Unknown"
                ),
                "Equipment": (
                    ", ".join(equipment_required) if equipment_required else "None"
                ),
                "Notes": exercise.get("notes", ""),
            }
        )

    st.dataframe(
        pd.DataFrame(planned_rows),
        width="stretch",
        hide_index=True,
    )


def display_selected_workout_plan_state(plan_response: dict) -> None:
    workout_plan_instance = plan_response.get("workout_plan_instance", {})
    execution_session = plan_response.get("execution_session", {})
    planned_exercises = plan_response.get("planned_exercises", [])

    st.subheader("Selected Workout Plan Status")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Plan Instance ID",
        workout_plan_instance.get("id", "Unknown"),
    )

    col2.metric(
        "Plan Status",
        humanize_label(workout_plan_instance.get("status")),
    )

    col3.metric(
        "Execution Status",
        humanize_label(execution_session.get("status")),
    )

    started_at = execution_session.get("started_at")
    workout_session_id = execution_session.get("workout_session_id")

    if started_at or workout_session_id:
        col4, col5 = st.columns(2)

        col4.metric(
            "Started At",
            started_at or "Not started",
        )

        col5.metric(
            "Workout Session ID",
            workout_session_id or "Not created",
        )

    st.write("**Planned Exercises**")
    display_planned_exercises(planned_exercises)


def display_actual_sets(actual_sets: list[dict]) -> None:
    st.subheader("Actual Logged Sets")

    if not actual_sets:
        st.info("No actual sets have been logged for this workout plan yet.")
        return

    actual_rows = []
    show_debug_columns = st.session_state.get("developer_mode", False)

    for actual_set in actual_sets:
        row = {
            "Exercise": actual_set.get("exercise_name", "Unknown"),
            "Set": actual_set.get("set_number", "Unknown"),
            "Actual Reps": actual_set.get("actual_reps", "Unknown"),
            "Actual Weight": actual_set.get("actual_weight", "Unknown"),
            "Actual RIR": actual_set.get("actual_rir", "Unknown"),
            "Completed": actual_set.get("completed", False),
            "Skipped": actual_set.get("skipped", False),
            "Notes": actual_set.get("notes") or "",
        }

        if show_debug_columns:
            row = {
                "ID": actual_set.get("id", "Unknown"),
                "Planned Exercise ID": actual_set.get(
                    "planned_workout_exercise_id",
                    "None",
                ),
                **row,
                "Substitution For": actual_set.get(
                    "substitution_for_planned_exercise_id",
                    "",
                )
                or "",
            }

        actual_rows.append(row)

    st.dataframe(
        pd.DataFrame(actual_rows),
        width="stretch",
        hide_index=True,
    )


PLANNED_VS_ACTUAL_FLAG_LABELS = {
    "empty_completion": "No actual workout execution rows have been logged yet.",
    "incomplete_logging": "Some planned work has not been logged yet.",
    "skipped_exercises_present": "Some planned exercises or sets were skipped.",
    "substitutions_present": "Some exercises were substituted.",
    "actual_effort_harder_than_planned": "Logged effort was harder than planned.",
    "actual_effort_easier_than_planned": "Logged effort was easier than planned.",
    "reps_below_plan": "Some logged sets were below the planned rep range.",
    "reps_above_plan": "Some logged sets were above the planned rep range.",
    "missing_actual_rir": "Some completed sets are missing actual RIR.",
    "missing_actual_reps": "Some completed sets are missing actual reps.",
}


def format_summary_metric(value: object, suffix: str = "") -> str:
    if value is None or value == "":
        return "Unknown"

    if isinstance(value, float):
        value = round(value, 2)
        if value.is_integer():
            value = int(value)

    return f"{value}{suffix}"


def planned_vs_actual_flag_label(flag: str) -> str:
    return PLANNED_VS_ACTUAL_FLAG_LABELS.get(flag, humanize_label(flag))


def display_metric_cards(metrics: list[dict], columns: int = 4) -> None:
    if not metrics:
        return

    for index in range(0, len(metrics), columns):
        row_metrics = metrics[index : index + columns]
        cols = st.columns(len(row_metrics))

        for column, metric in zip(cols, row_metrics, strict=False):
            column.metric(
                metric["label"],
                metric["value"],
                help=metric.get("help"),
            )


def compact_count(value: object) -> str:
    if value is None or value == "":
        return "0"

    return str(value)


def format_signed_delta(value: int | float | None, suffix: str = "") -> str:
    if value is None:
        return "Unknown"

    if isinstance(value, float):
        value = round(value, 2)
        if value.is_integer():
            value = int(value)

    sign = "+" if value > 0 else ""
    return f"{sign}{value}{suffix}"


def planned_range_label(
    minimum: int | float | None, maximum: int | float | None
) -> str:
    if minimum is None or maximum is None:
        return "Unknown"

    return f"{minimum}-{maximum}"


def effort_delta_label(rir_deviation: int | float | None) -> str:
    if rir_deviation is None:
        return "⚪ Effort unknown"

    if rir_deviation < 0:
        return f"🔴 Harder than planned ({format_signed_delta(rir_deviation, ' RIR')})"

    if rir_deviation > 0:
        return f"🟡 Easier than planned ({format_signed_delta(rir_deviation, ' RIR')})"

    return "✅ On target"


def rep_result_label(below: int, inside: int, above: int) -> str:
    parts = []

    if below:
        parts.append(f"🟡 {below} below")
    if inside:
        parts.append(f"✅ {inside} on target")
    if above:
        parts.append(f"🔴 {above} above")

    if not parts:
        return "⚪ Reps unknown"

    return " / ".join(parts)


def build_planned_vs_actual_delta_rows(
    planned_exercises: list[dict] | None,
    actual_sets: list[dict] | None,
) -> list[dict]:
    if not planned_exercises or not actual_sets:
        return []

    actual_sets_by_plan: dict[int, list[dict]] = {}
    for actual_set in actual_sets:
        planned_id = actual_set.get("planned_workout_exercise_id")
        substitution_id = actual_set.get("substitution_for_planned_exercise_id")

        candidate_ids = []
        if planned_id is not None:
            candidate_ids.append(planned_id)
        if substitution_id is not None and substitution_id != planned_id:
            candidate_ids.append(substitution_id)

        for candidate_id in candidate_ids:
            try:
                actual_sets_by_plan.setdefault(int(candidate_id), []).append(actual_set)
            except (TypeError, ValueError):
                continue

    delta_rows = []

    for exercise in planned_exercises:
        try:
            planned_id = int(exercise.get("id"))
        except (TypeError, ValueError):
            continue

        exercise_actual_sets = actual_sets_by_plan.get(planned_id, [])
        completed_sets = [
            actual_set
            for actual_set in exercise_actual_sets
            if actual_set.get("completed") and not actual_set.get("skipped")
        ]
        skipped_sets = [
            actual_set
            for actual_set in exercise_actual_sets
            if actual_set.get("skipped")
        ]

        planned_sets = exercise.get("sets") or 0
        reps_min = exercise.get("reps_min")
        reps_max = exercise.get("reps_max")
        rir_min = exercise.get("rir_min")
        rir_max = exercise.get("rir_max")

        active_exercise_name = exercise.get("name", "Unknown")
        substituted = False

        for actual_set in exercise_actual_sets:
            actual_exercise_name = actual_set.get("exercise_name")
            if actual_exercise_name and actual_exercise_name != exercise.get("name"):
                active_exercise_name = actual_exercise_name
                substituted = True
                break
            if actual_set.get("substitution_for_planned_exercise_id") == planned_id:
                substituted = True

        if substituted:
            exercise_label = (
                f"{active_exercise_name}  \nOriginal: {exercise.get('name', 'Unknown')}"
            )
        else:
            exercise_label = exercise.get("name", "Unknown")

        below_reps = 0
        inside_reps = 0
        above_reps = 0
        actual_rirs = []
        actual_reps = []
        actual_weights = []

        for actual_set in completed_sets:
            reps = actual_set.get("actual_reps")
            actual_rir = actual_set.get("actual_rir")
            actual_weight = actual_set.get("actual_weight")

            if reps is not None:
                actual_reps.append(str(reps))
                if reps_min is not None and reps_max is not None:
                    if reps < reps_min:
                        below_reps += 1
                    elif reps > reps_max:
                        above_reps += 1
                    else:
                        inside_reps += 1

            if actual_rir is not None:
                actual_rirs.append(actual_rir)
            if actual_weight is not None:
                actual_weights.append(str(actual_weight))

        planned_rir_midpoint = None
        if rir_min is not None and rir_max is not None:
            planned_rir_midpoint = (rir_min + rir_max) / 2

        actual_rir_average = None
        if actual_rirs:
            actual_rir_average = round(sum(actual_rirs) / len(actual_rirs), 2)

        rir_delta = None
        if planned_rir_midpoint is not None and actual_rir_average is not None:
            rir_delta = round(actual_rir_average - planned_rir_midpoint, 2)

        if skipped_sets and not completed_sets:
            status = "⚪ Skipped"
        elif completed_sets and len(completed_sets) >= planned_sets:
            status = "✅ Complete"
        elif completed_sets:
            status = "🟡 Partially logged"
        else:
            status = "⚪ Not logged"

        if substituted:
            status = f"↔️ Substituted / {status}"

        delta_rows.append(
            {
                "Exercise": exercise_label,
                "Planned": (
                    f"{planned_sets} sets × {planned_range_label(reps_min, reps_max)} reps "
                    f"@ RIR {planned_range_label(rir_min, rir_max)}"
                ),
                "Actual": (
                    f"{len(completed_sets)} completed"
                    + (f" / {len(skipped_sets)} skipped" if skipped_sets else "")
                    + (f"  \nReps: {', '.join(actual_reps)}" if actual_reps else "")
                    + (
                        f"  \nWeight: {', '.join(actual_weights)}"
                        if actual_weights
                        else ""
                    )
                    + (
                        f"  \nRIR: {', '.join(str(rir) for rir in actual_rirs)}"
                        if actual_rirs
                        else ""
                    )
                ),
                "Rep Delta": rep_result_label(below_reps, inside_reps, above_reps),
                "Effort Delta": effort_delta_label(rir_delta),
                "Status": status,
            }
        )

    return delta_rows


def display_review_signal_rows(summary: dict, deviation_flags: list[str]) -> None:
    signal_rows = [
        {
            "Area": "Completion",
            "Signal": (
                f"{format_summary_metric(summary.get('completion_percentage'), '%')} complete; "
                f"{compact_count(summary.get('completed_set_count'))}/"
                f"{compact_count(summary.get('planned_set_count'))} planned sets logged"
            ),
        },
        {
            "Area": "Effort vs Plan",
            "Signal": effort_delta_label(summary.get("rir_deviation")),
        },
        {
            "Area": "Reps vs Plan",
            "Signal": rep_result_label(
                int(summary.get("sets_below_planned_reps") or 0),
                int(summary.get("sets_inside_planned_reps") or 0),
                int(summary.get("sets_above_planned_reps") or 0),
            ),
        },
        {
            "Area": "Substitutions / Skips",
            "Signal": (
                f"{compact_count(summary.get('substituted_exercise_count'))} substitutions; "
                f"{compact_count(summary.get('skipped_set_count'))} skipped sets"
            ),
        },
        {
            "Area": "Logging Quality",
            "Signal": (
                "No review flags returned"
                if not deviation_flags
                else "; ".join(
                    planned_vs_actual_flag_label(flag) for flag in deviation_flags
                )
            ),
        },
    ]

    st.dataframe(
        pd.DataFrame(signal_rows),
        width="stretch",
        hide_index=True,
    )


def display_planned_vs_actual_summary(
    summary: dict,
    planned_exercises: list[dict] | None = None,
    actual_sets: list[dict] | None = None,
) -> None:
    st.subheader("Workout Review")

    if not summary:
        st.info("Planned-vs-actual summary is not available yet.")
        return

    completion_percentage = summary.get("completion_percentage") or 0
    deviation_flags = summary.get("deviation_flags") or []
    notes = summary.get("notes") or []

    progress_value = max(0.0, min(float(completion_percentage) / 100, 1.0))
    st.progress(
        progress_value,
        text=f"{format_summary_metric(completion_percentage, '%')} of planned sets completed",
    )

    display_metric_cards(
        [
            {
                "label": "Sets Logged",
                "value": (
                    f"{compact_count(summary.get('completed_set_count'))}/"
                    f"{compact_count(summary.get('planned_set_count'))}"
                ),
                "help": "Completed actual sets compared with planned sets.",
            },
            {
                "label": "Skipped Sets",
                "value": format_summary_metric(summary.get("skipped_set_count")),
                "help": "Skipped work is recorded neutrally.",
            },
            {
                "label": "Effort Delta",
                "value": format_signed_delta(summary.get("rir_deviation"), " RIR"),
                "help": (
                    "Negative means logged effort was harder than planned. "
                    "Positive means logged effort was easier than planned."
                ),
            },
            {
                "label": "Rep Target",
                "value": (
                    f"{compact_count(summary.get('sets_inside_planned_reps'))} in / "
                    f"{compact_count(summary.get('sets_below_planned_reps'))} below / "
                    f"{compact_count(summary.get('sets_above_planned_reps'))} above"
                ),
                "help": "How completed sets compared with the planned rep range.",
            },
        ],
        columns=4,
    )

    st.markdown("#### Planned vs Actual Deltas")
    delta_rows = build_planned_vs_actual_delta_rows(planned_exercises, actual_sets)

    if delta_rows:
        st.dataframe(
            pd.DataFrame(delta_rows),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "Exercise-level deltas will appear when planned exercises and actual sets "
            "are available for this review."
        )

    st.markdown("#### Review Signals")
    display_review_signal_rows(summary, deviation_flags)

    if notes:
        with st.expander("Review notes", expanded=False):
            for note in notes:
                st.info(note)

    if st.session_state.get("developer_mode", False):
        with st.expander("Developer details: planned-vs-actual summary"):
            st.json(summary)
            if planned_exercises is not None:
                st.subheader("Planned Exercises Used For Delta Table")
                st.json(planned_exercises)
            if actual_sets is not None:
                st.subheader("Actual Sets Used For Delta Table")
                st.json(actual_sets)


def planned_exercise_option_label(exercise: dict) -> str:
    reps_min = exercise.get("reps_min")
    reps_max = exercise.get("reps_max")
    rir_min = exercise.get("rir_min")
    rir_max = exercise.get("rir_max")

    reps_label = (
        f"{reps_min}-{reps_max} reps"
        if reps_min is not None and reps_max is not None
        else "reps unknown"
    )

    rir_label = (
        f"RIR {rir_min}-{rir_max}"
        if rir_min is not None and rir_max is not None
        else "RIR unknown"
    )

    return (
        f"{exercise.get('id')} — "
        f"{exercise.get('exercise_order', '?')}. "
        f"{exercise.get('name', 'Unknown')} "
        f"({exercise.get('sets', '?')} sets, {reps_label}, {rir_label})"
    )


def substitution_reason_label(reason_code: str) -> str:
    labels = {
        "same_movement_pattern": "Same movement pattern",
        "compatible_movement_family": "Compatible movement family",
        "equipment_profile_compatible": "Compatible with current equipment profile",
        "same_primary_muscle_group": "Similar primary muscle group",
        "same_exercise_type": "Same exercise type",
        "difficulty_match": "Similar difficulty",
        "bodyweight_compatible": "Bodyweight-compatible",
        "limited_equipment_compatible": "Limited-equipment-compatible",
        "home_gym_compatible": "Home-gym-compatible",
    }

    return labels.get(reason_code, humanize_label(reason_code))


def format_substitution_list(values: list[str] | None) -> str:
    if not values:
        return "Unknown"

    return ", ".join(equipment_display_name(value) for value in values)


def display_substitution_candidate_table(candidates: list[dict]) -> None:
    if not candidates:
        st.info("No compatible substitutions were returned for this planned exercise.")
        return

    top_candidates = candidates[:5]
    summary_rows = []

    for candidate in top_candidates:
        reason_codes = candidate.get("compatibility_reason_codes") or []
        first_reason = (
            substitution_reason_label(reason_codes[0])
            if reason_codes
            else "Compatible with current constraints"
        )
        summary_rows.append(
            {
                "Option": candidate.get("name", "Unknown"),
                "Equipment": format_substitution_list(
                    candidate.get("required_equipment")
                ),
                "Why it fits": first_reason,
            }
        )

    st.caption(
        "Top compatible substitutions are shown first. Full details are hidden below."
    )
    st.dataframe(
        pd.DataFrame(summary_rows),
        width="stretch",
        hide_index=True,
    )

    with st.expander("More options / candidate details", expanded=False):
        candidate_rows = []
        for candidate in candidates:
            reason_codes = candidate.get("compatibility_reason_codes") or []
            candidate_rows.append(
                {
                    "Exercise": candidate.get("name", "Unknown"),
                    "Movement Pattern": humanize_label(
                        candidate.get("movement_pattern")
                    ),
                    "Required Equipment": format_substitution_list(
                        candidate.get("required_equipment")
                    ),
                    "Primary Muscle Groups": format_substitution_list(
                        candidate.get("primary_muscle_groups")
                    ),
                    "Type": humanize_label(candidate.get("exercise_type")),
                    "Difficulty": humanize_label(candidate.get("difficulty")),
                    "Why Compatible": ", ".join(
                        substitution_reason_label(reason_code)
                        for reason_code in reason_codes
                    )
                    or "Compatible with current constraints",
                }
            )

        st.dataframe(
            pd.DataFrame(candidate_rows),
            width="stretch",
            hide_index=True,
        )


def substitution_candidate_option_label(candidate: dict) -> str:
    equipment = format_substitution_list(candidate.get("required_equipment"))
    movement_pattern = humanize_label(candidate.get("movement_pattern"))

    return (
        f"{candidate.get('catalog_exercise_id')} — "
        f"{candidate.get('name', 'Unknown')} "
        f"({movement_pattern}; {equipment})"
    )


def display_active_substitution(apply_response: dict | None) -> None:
    if not apply_response:
        return

    active_substitution = apply_response.get("active_substitution") or {}
    original_name = active_substitution.get("original_exercise_name") or "Unknown"
    replacement_name = (
        active_substitution.get("replacement_exercise_name")
        or apply_response.get("selected_candidate", {}).get("name")
        or "Unknown"
    )

    st.success("Active substitution applied.")
    st.write(f"**Original:** {original_name}")
    st.write(f"**Substituted with:** {replacement_name}")

    if apply_response.get("previous_active_substitution_replaced"):
        st.caption(
            "A previous active substitution for this planned exercise was replaced."
        )


def active_substitution_response_from_record(substitution: dict | None) -> dict | None:
    if not substitution:
        return None

    return {
        "active_substitution": substitution,
        "previous_active_substitution_replaced": False,
        "selected_candidate": {
            "name": substitution.get("replacement_exercise_name"),
        },
    }


def active_substitution_map_from_execution(
    execution_response: dict | None,
) -> dict[int, dict]:
    if not execution_response:
        return {}

    active_substitutions = execution_response.get("active_substitutions") or []
    substitution_map = {}

    for substitution in active_substitutions:
        planned_exercise_id = substitution.get("planned_workout_exercise_id")
        if planned_exercise_id is None:
            continue

        substitution_map[int(planned_exercise_id)] = substitution

    return substitution_map


def active_substitution_map_from_session(plan_instance_id: int) -> dict[int, dict]:
    substitution_map = {}
    prefix = f"{plan_instance_id}_"

    for (
        response_key,
        apply_response,
    ) in st.session_state.applied_substitution_responses.items():
        if not str(response_key).startswith(prefix):
            continue

        active_substitution = apply_response.get("active_substitution") or {}
        planned_exercise_id = active_substitution.get("planned_workout_exercise_id")

        if planned_exercise_id is None:
            planned_exercise_id = apply_response.get("planned_workout_exercise_id")

        if planned_exercise_id is None:
            continue

        substitution_map[int(planned_exercise_id)] = active_substitution

    return substitution_map


def merged_active_substitution_map(
    plan_instance_id: int,
    execution_response: dict | None,
) -> dict[int, dict]:
    substitution_map = active_substitution_map_from_execution(execution_response)
    substitution_map.update(active_substitution_map_from_session(plan_instance_id))
    return substitution_map


def display_active_substitution_summary(
    planned_exercises: list[dict],
    active_substitutions: dict[int, dict],
) -> None:
    if not active_substitutions:
        return

    planned_names = {
        int(exercise["id"]): exercise.get("name", "Unknown")
        for exercise in planned_exercises
        if exercise.get("id") is not None
    }

    rows = []
    for planned_exercise_id, substitution in active_substitutions.items():
        rows.append(
            {
                "Original": planned_names.get(
                    planned_exercise_id,
                    substitution.get("original_exercise_name", "Unknown"),
                ),
                "Substituted With": substitution.get(
                    "replacement_exercise_name",
                    "Unknown",
                ),
                "Status": humanize_label(substitution.get("status", "active")),
                "Reason": humanize_label(
                    substitution.get("substitution_reason", "user_selected"),
                ),
            }
        )

    st.write("**Active Substitutions**")
    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
        hide_index=True,
    )


def can_apply_substitution(
    plan_status: str | None,
    execution_status: str | None,
) -> bool:
    allowed_statuses = {"selected", "started", "in_progress"}

    return plan_status in allowed_statuses or execution_status in allowed_statuses


def apply_substitution_candidate(
    plan_instance_id: int,
    planned_exercise_id: int,
    planned_exercise_name: str,
    selected_candidate: dict,
    apply_response_key: str,
) -> None:
    payload = {
        "replacement_catalog_exercise_id": int(
            selected_candidate["catalog_exercise_id"]
        ),
        "substitution_reason": "user_selected",
    }

    try:
        apply_response = api_post(
            "/workout-plans/"
            f"{plan_instance_id}/planned-exercises/"
            f"{planned_exercise_id}/substitute",
            payload,
        )
    except requests.RequestException as exc:
        st.session_state.substitution_apply_error = (
            f"Substitution apply failed for {planned_exercise_name}: "
            f"{extract_api_error_message(exc)}"
        )
        st.rerun()

    if apply_response.get("success"):
        st.session_state.applied_substitution_responses[apply_response_key] = (
            apply_response
        )
        refresh_active_plan_response(plan_instance_id)
        replacement_name = (
            apply_response.get("active_substitution", {}).get(
                "replacement_exercise_name"
            )
            or selected_candidate.get("name")
            or "selected exercise"
        )
        st.session_state.substitution_apply_message = (
            f"Substitution applied: {planned_exercise_name} → {replacement_name}. "
            "Actual set logging will use the substituted exercise."
        )
        st.session_state.substitution_apply_error = None
        st.session_state.substitution_flow_ready_to_do_workout = True
        request_workout_flow_step("2. Do Workout")
        st.rerun()

    st.session_state.substitution_apply_error = (
        f"Substitution apply failed for {planned_exercise_name}."
    )
    st.rerun()


def display_apply_substitution_control(
    plan_instance_id: int,
    planned_exercise_id: int,
    planned_exercise_name: str,
    candidates: list[dict],
    apply_response_key: str,
    allow_apply: bool,
) -> None:
    if not candidates:
        return

    if not allow_apply:
        st.caption(
            "Apply is available after a plan is selected, started, or in progress. "
            "Completed workouts preserve completed history."
        )
        return

    candidate_options = [
        candidate
        for candidate in candidates
        if candidate.get("catalog_exercise_id") is not None
    ]

    if not candidate_options:
        st.caption("No selectable substitution candidates were returned.")
        return

    st.markdown("##### Apply substitution")
    st.caption("Use one of the top matches, or open More options for the full list.")

    for index, candidate in enumerate(candidate_options[:5], start=1):
        reason_codes = candidate.get("compatibility_reason_codes") or []
        first_reason = (
            substitution_reason_label(reason_codes[0])
            if reason_codes
            else "Compatible with current constraints"
        )
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{index}. {candidate.get('name', 'Unknown')}**")
            st.caption(
                f"{humanize_label(candidate.get('movement_pattern'))} · "
                f"{format_substitution_list(candidate.get('required_equipment'))} · "
                f"{first_reason}"
            )
        with col2:
            if st.button(
                "Use this",
                key=(
                    "substitution_quick_apply_"
                    f"{apply_response_key}_{candidate.get('catalog_exercise_id')}"
                ),
            ):
                apply_substitution_candidate(
                    plan_instance_id=plan_instance_id,
                    planned_exercise_id=planned_exercise_id,
                    planned_exercise_name=planned_exercise_name,
                    selected_candidate=candidate,
                    apply_response_key=apply_response_key,
                )

    with st.expander("More options", expanded=False):
        candidate_option_map = {
            substitution_candidate_option_label(candidate): candidate
            for candidate in candidate_options
        }
        selected_candidate_label = st.selectbox(
            "All compatible substitutions",
            options=list(candidate_option_map.keys()),
            key=f"substitution_apply_select_{apply_response_key}",
        )
        selected_candidate = candidate_option_map[selected_candidate_label]

        if st.button(
            f"Apply selected substitution for {planned_exercise_name}",
            key=f"substitution_apply_button_{apply_response_key}",
        ):
            apply_substitution_candidate(
                plan_instance_id=plan_instance_id,
                planned_exercise_id=planned_exercise_id,
                planned_exercise_name=planned_exercise_name,
                selected_candidate=selected_candidate,
                apply_response_key=apply_response_key,
            )


def display_substitution_candidates(
    plan_instance_id: int,
    planned_exercises: list[dict],
    context_key: str,
    plan_status: str | None = None,
    execution_status: str | None = None,
    active_substitutions: dict[int, dict] | None = None,
    always_visible: bool = False,
    title: str = "Compatible Substitutions",
) -> None:
    st.markdown(f"#### {title}")

    if not planned_exercises:
        st.info("No planned exercises are available for substitution lookup.")
        return

    if st.session_state.substitution_apply_message:
        st.success(st.session_state.substitution_apply_message)
        st.session_state.substitution_apply_message = None

    if st.session_state.substitution_apply_error:
        st.error(st.session_state.substitution_apply_error)
        st.session_state.substitution_apply_error = None

    allow_apply = can_apply_substitution(plan_status, execution_status)
    active_substitutions = active_substitutions or {}

    st.caption(
        "Substitutions are optional. The original plan stays preserved, while actual "
        "set logging uses the active substituted exercise after apply."
    )

    if not allow_apply:
        st.caption(
            "Substitution candidates can be reviewed here, but Apply is only available "
            "for selected, started, or in-progress workout plans."
        )

    for planned_exercise in planned_exercises:
        planned_exercise_id = planned_exercise.get("id")
        planned_exercise_name = planned_exercise.get("name", "Unknown")

        if planned_exercise_id is None:
            st.caption(
                f"Substitution lookup is unavailable for {planned_exercise_name} "
                "because no planned exercise ID was returned."
            )
            continue

        planned_exercise_id_int = int(planned_exercise_id)
        active_substitution = active_substitutions.get(planned_exercise_id_int)
        expander_label = f"Need a substitution? {planned_exercise_name}"
        if active_substitution:
            expander_label = f"Substitution active: {planned_exercise_name}"

        with st.expander(
            expander_label,
            expanded=bool(active_substitution) or bool(always_visible),
        ):
            st.write(f"**Original:** {planned_exercise_name}")

            apply_response_key = f"{plan_instance_id}_{planned_exercise_id_int}"
            apply_response = st.session_state.applied_substitution_responses.get(
                apply_response_key
            ) or active_substitution_response_from_record(active_substitution)
            display_active_substitution(apply_response)

            try:
                candidate_response = api_get(
                    "/workout-plans/"
                    f"{plan_instance_id}/planned-exercises/"
                    f"{planned_exercise_id_int}/substitution-candidates"
                )
            except requests.RequestException as exc:
                st.error(
                    "Failed to load substitution candidates for "
                    f"{planned_exercise_name}: {extract_api_error_message(exc)}"
                )
                continue

            candidates = candidate_response.get("substitution_candidates", [])

            display_substitution_candidate_table(candidates)
            display_apply_substitution_control(
                plan_instance_id=plan_instance_id,
                planned_exercise_id=planned_exercise_id_int,
                planned_exercise_name=planned_exercise_name,
                candidates=candidates,
                apply_response_key=apply_response_key,
                allow_apply=allow_apply,
            )

            if st.session_state.get("developer_mode", False):
                with st.expander(
                    f"Developer details: substitution candidates for {planned_exercise_name}"
                ):
                    st.json(candidate_response)

                    latest_apply_response = (
                        st.session_state.applied_substitution_responses.get(
                            apply_response_key
                        )
                    )
                    if latest_apply_response:
                        st.subheader("Latest Raw Apply Response")
                        st.json(latest_apply_response)


def actual_set_reference_id(actual_set: dict) -> int | None:
    planned_id = actual_set.get("planned_workout_exercise_id")
    substitution_for_id = actual_set.get("substitution_for_planned_exercise_id")
    reference_id = planned_id if planned_id is not None else substitution_for_id

    if reference_id is None:
        return None

    try:
        return int(reference_id)
    except (TypeError, ValueError):
        return None


def actual_sets_for_planned_exercise(
    actual_sets: list[dict],
    planned_exercise_id: int,
) -> list[dict]:
    return [
        actual_set
        for actual_set in actual_sets
        if actual_set_reference_id(actual_set) == planned_exercise_id
    ]


def next_set_number_for_planned_exercise(
    actual_sets: list[dict],
    planned_exercise_id: int,
) -> int:
    existing_sets = actual_sets_for_planned_exercise(actual_sets, planned_exercise_id)
    existing_numbers = [
        int(actual_set.get("set_number"))
        for actual_set in existing_sets
        if actual_set.get("set_number") is not None
    ]

    if existing_numbers:
        return max(existing_numbers) + 1

    return 1


def active_exercise_name_for_planned_exercise(
    planned_exercise: dict,
    active_substitutions: dict[int, dict],
) -> str:
    planned_exercise_id = planned_exercise.get("id")
    planned_name = planned_exercise.get("name", "Unknown")

    if planned_exercise_id is None:
        return planned_name

    active_substitution = active_substitutions.get(int(planned_exercise_id))
    if not active_substitution:
        return planned_name

    return active_substitution.get("replacement_exercise_name") or planned_name


def active_workout_exercise_label(
    planned_exercise: dict,
    active_substitutions: dict[int, dict],
) -> str:
    planned_exercise_id = planned_exercise.get("id")
    planned_name = planned_exercise.get("name", "Unknown")
    active_name = active_exercise_name_for_planned_exercise(
        planned_exercise,
        active_substitutions,
    )
    sets = planned_exercise.get("sets", "?")
    reps = format_workout_range(
        planned_exercise.get("reps_min"),
        planned_exercise.get("reps_max"),
        " reps",
    )
    rir = format_workout_range(
        planned_exercise.get("rir_min"),
        planned_exercise.get("rir_max"),
    )

    if planned_exercise_id is not None and active_name != planned_name:
        return (
            f"{planned_exercise_id} — {active_name} "
            f"(sub for {planned_name}; {sets} sets, {reps}, RIR {rir})"
        )

    return f"{planned_exercise_id} — {planned_name} ({sets} sets, {reps}, RIR {rir})"


def actual_set_status_label(actual_set: dict) -> str:
    if actual_set.get("skipped"):
        return "Skipped"

    if actual_set.get("completed"):
        return "Logged"

    return "Started"


def display_logged_sets_for_exercise(
    actual_sets: list[dict],
    planned_exercise_id: int,
) -> None:
    exercise_actual_sets = actual_sets_for_planned_exercise(
        actual_sets,
        planned_exercise_id,
    )

    if not exercise_actual_sets:
        st.caption("No sets logged for this exercise yet.")
        return

    rows = []
    show_debug_columns = st.session_state.get("developer_mode", False)

    for actual_set in sorted(
        exercise_actual_sets,
        key=lambda item: item.get("set_number") or 0,
    ):
        row = {
            "Set": actual_set.get("set_number", "Unknown"),
            "Exercise Logged": actual_set.get("exercise_name", "Unknown"),
            "Reps": actual_set.get("actual_reps", ""),
            "Weight": actual_set.get("actual_weight", ""),
            "RIR": actual_set.get("actual_rir", ""),
            "Status": actual_set_status_label(actual_set),
            "Notes": actual_set.get("notes") or "",
        }

        if show_debug_columns:
            row = {"Actual Set ID": actual_set.get("id", "Unknown"), **row}

        rows.append(row)

    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
        hide_index=True,
    )


def display_active_workout_session_overview(
    planned_exercises: list[dict],
    actual_sets: list[dict],
    active_substitutions: dict[int, dict],
) -> None:
    st.markdown("#### Active Workout")
    st.caption(
        "Log the next set below. Substitutions and corrections stay available when needed."
    )

    if not planned_exercises:
        st.warning("No planned exercises are available for this active workout.")
        return

    for exercise in planned_exercises:
        planned_exercise_id = exercise.get("id")
        if planned_exercise_id is None:
            continue

        planned_exercise_id = int(planned_exercise_id)
        planned_name = exercise.get("name", "Unknown")
        active_name = active_exercise_name_for_planned_exercise(
            exercise,
            active_substitutions,
        )
        logged_sets = actual_sets_for_planned_exercise(actual_sets, planned_exercise_id)
        completed_sets = [
            actual_set
            for actual_set in logged_sets
            if actual_set.get("completed") and not actual_set.get("skipped")
        ]
        skipped_sets = [
            actual_set for actual_set in logged_sets if actual_set.get("skipped")
        ]
        planned_sets = exercise.get("sets", "?")
        planned_reps = format_workout_range(
            exercise.get("reps_min"),
            exercise.get("reps_max"),
            " reps",
        )
        target_rir = format_workout_range(
            exercise.get("rir_min"),
            exercise.get("rir_max"),
        )

        with st.container():
            title_col, status_col = st.columns([4, 1])
            with title_col:
                st.markdown(f"**{active_name}**")
                if active_name != planned_name:
                    st.caption(f"Original planned exercise: {planned_name}")
            with status_col:
                st.metric("Logged", f"{len(completed_sets)}/{planned_sets}")

            detail_cols = st.columns(4)
            detail_cols[0].caption(f"Planned: {planned_sets} sets")
            detail_cols[1].caption(f"Reps: {planned_reps}")
            detail_cols[2].caption(f"Target RIR: {target_rir}")
            detail_cols[3].caption(f"Equipment: {format_equipment_required(exercise)}")

            if skipped_sets:
                st.caption(f"Skipped sets recorded: {len(skipped_sets)}")

        st.divider()

    if active_substitutions:
        st.caption(
            "Substitutions are active for this workout. Original planned exercises "
            "remain preserved, while set logging uses the active substituted exercise."
        )


def display_actual_set_logging(
    plan_instance_id: int, context_key: str = "workout"
) -> None:
    try:
        execution_response = api_get(f"/workout-plans/{plan_instance_id}/execution")
    except requests.RequestException as exc:
        st.error(f"Failed to load actual set logger: {extract_api_error_message(exc)}")
        return

    workout_plan_instance = execution_response.get("workout_plan_instance", {})
    execution_session = execution_response.get("execution_session", {})
    planned_exercises = execution_response.get("planned_exercises", [])
    actual_sets = execution_response.get("actual_sets", [])
    active_substitutions = merged_active_substitution_map(
        plan_instance_id,
        execution_response,
    )

    plan_status = workout_plan_instance.get("status")
    execution_status = execution_session.get("status")

    st.subheader("Log Sets")

    if plan_status not in {"started", "in_progress"} and execution_status not in {
        "started",
        "in_progress",
    }:
        st.info(
            "Set logging appears after this selected plan is started. "
            f"Current plan status: {humanize_label(plan_status)}. "
            f"Execution status: {humanize_label(execution_status)}."
        )
        return

    if st.session_state.actual_set_logging_message:
        st.success(st.session_state.actual_set_logging_message)
        st.session_state.actual_set_logging_message = None

    if not planned_exercises:
        st.warning("No planned exercises are available for actual set logging.")
        return

    display_active_workout_session_overview(
        planned_exercises,
        actual_sets,
        active_substitutions,
    )

    planned_options = {
        active_workout_exercise_label(exercise, active_substitutions): exercise
        for exercise in planned_exercises
        if exercise.get("id") is not None
    }

    if not planned_options:
        st.warning("No planned exercises have IDs available for set logging.")
        return

    planned_option_labels = list(planned_options.keys())
    next_exercise_index = 0
    for index, option_label in enumerate(planned_option_labels):
        option_exercise = planned_options[option_label]
        option_exercise_id = int(option_exercise["id"])
        logged_sets = actual_sets_for_planned_exercise(actual_sets, option_exercise_id)
        completed_sets = [
            actual_set
            for actual_set in logged_sets
            if actual_set.get("completed") and not actual_set.get("skipped")
        ]
        planned_set_count = option_exercise.get("sets") or 0
        if len(completed_sets) < int(planned_set_count):
            next_exercise_index = index
            break

    st.markdown("#### Quick Log Set")

    with st.form(f"actual_set_logging_form_{context_key}_{plan_instance_id}"):
        selected_planned_label = st.selectbox(
            "Exercise",
            options=planned_option_labels,
            index=next_exercise_index,
            key=f"actual_set_exercise_{context_key}_{plan_instance_id}",
            help=(
                "If a substitution is active, this selector shows the substituted "
                "exercise first and set logging will automatically use it."
            ),
        )

        selected_planned_exercise = planned_options[selected_planned_label]
        selected_planned_exercise_id = int(selected_planned_exercise["id"])
        active_substitution = active_substitutions.get(selected_planned_exercise_id)
        planned_exercise_name = selected_planned_exercise.get("name", "Unknown")
        active_exercise_name = active_exercise_name_for_planned_exercise(
            selected_planned_exercise,
            active_substitutions,
        )

        if active_substitution:
            st.info(
                f"Original: {planned_exercise_name}\n\n"
                f"Substituted with: {active_exercise_name}\n\n"
                "This form will log completed sets using the substituted exercise."
            )
        else:
            st.caption(f"Logging sets for: {active_exercise_name}")

        skip_set = st.checkbox(
            "Mark this set as skipped",
            value=False,
            key=f"actual_set_skip_{context_key}_{plan_instance_id}",
            help="Use this only when you intentionally skipped the planned set.",
        )

        suggested_set_number = next_set_number_for_planned_exercise(
            actual_sets,
            selected_planned_exercise_id,
        )

        set_number = st.number_input(
            "Set Number",
            min_value=1,
            value=int(suggested_set_number),
            step=1,
            key=f"actual_set_number_{context_key}_{plan_instance_id}",
        )

        actual_reps = None
        actual_weight = None
        actual_rir = None

        if not skip_set:
            default_reps = selected_planned_exercise.get("reps_min") or 1
            default_rir = selected_planned_exercise.get("rir_max") or 2

            col1, col2, col3 = st.columns(3)

            with col1:
                actual_reps = st.number_input(
                    "Actual Reps",
                    min_value=0,
                    value=int(default_reps),
                    step=1,
                    key=f"actual_reps_{context_key}_{plan_instance_id}",
                )

            with col2:
                actual_weight = st.number_input(
                    "Actual Weight",
                    min_value=0.0,
                    value=0.0,
                    step=5.0,
                    key=f"actual_weight_{context_key}_{plan_instance_id}",
                )

            with col3:
                actual_rir = st.slider(
                    "Actual RIR",
                    min_value=0,
                    max_value=10,
                    value=int(default_rir),
                    key=f"actual_rir_{context_key}_{plan_instance_id}",
                )
        else:
            st.caption(
                "Skipped sets are recorded without reps, weight, or RIR. "
                "Use optional notes only if useful."
            )

        actual_set_notes = st.text_area(
            "Notes (optional)",
            key=f"actual_set_notes_{context_key}_{plan_instance_id}",
            placeholder="Optional: pain, substitution context, form cue, or reason for a skipped set.",
        )

        submit_actual_set = st.form_submit_button("Log Set", type="primary")

    st.markdown("#### Logged Sets For Selected Exercise")
    display_logged_sets_for_exercise(actual_sets, selected_planned_exercise_id)

    if submit_actual_set:
        payload = {
            "set_number": int(set_number),
            "notes": actual_set_notes or None,
        }

        if skip_set:
            payload.update(
                {
                    "planned_workout_exercise_id": selected_planned_exercise["id"],
                    "completed": False,
                    "skipped": True,
                }
            )
        elif active_substitution:
            payload.update(
                {
                    "substitution_for_planned_exercise_id": selected_planned_exercise[
                        "id"
                    ],
                    "exercise_name": active_exercise_name,
                    "actual_reps": int(actual_reps),
                    "actual_weight": float(actual_weight),
                    "actual_rir": int(actual_rir),
                    "completed": True,
                    "skipped": False,
                }
            )
        else:
            payload.update(
                {
                    "planned_workout_exercise_id": selected_planned_exercise["id"],
                    "actual_reps": int(actual_reps),
                    "actual_weight": float(actual_weight),
                    "actual_rir": int(actual_rir),
                    "completed": True,
                    "skipped": False,
                }
            )

        payload = {key: value for key, value in payload.items() if value is not None}

        try:
            actual_set_response = api_post(
                f"/workout-plans/{plan_instance_id}/actual-sets",
                payload,
            )

            if actual_set_response.get("success"):
                actual_set = actual_set_response.get("actual_set", {})
                logged_name = actual_set.get("exercise_name") or active_exercise_name
                st.session_state.actual_set_logging_message = (
                    f"Logged {logged_name} set {set_number}."
                )
                st.rerun()
            else:
                st.error("Actual set logging failed.")

        except requests.RequestException as exc:
            st.error(f"Actual set logging failed: {extract_api_error_message(exc)}")

    if st.session_state.get("developer_mode", False):
        with st.expander("Developer details: actual set logging"):
            st.subheader("Raw Execution Response Used By Logger")
            st.json(execution_response)


def actual_set_option_label(actual_set: dict) -> str:
    actual_set_id = actual_set.get("id", "Unknown")
    exercise_name = actual_set.get("exercise_name") or "Unknown Exercise"
    set_number = actual_set.get("set_number", "Unknown")
    completed = actual_set.get("completed", False)
    skipped = actual_set.get("skipped", False)

    if skipped:
        status = "Skipped"
    elif completed:
        status = "Completed"
    else:
        status = "Not Completed"

    return f"Actual Set {actual_set_id} — {exercise_name} — Set {set_number} — {status}"


def planned_exercise_by_id(
    planned_exercises: list[dict],
) -> dict[int, dict]:
    return {
        int(exercise["id"]): exercise
        for exercise in planned_exercises
        if exercise.get("id") is not None
    }


def get_planned_exercise_index(
    planned_exercise_ids: list[int],
    selected_id: int | None,
) -> int:
    if selected_id in planned_exercise_ids:
        return planned_exercise_ids.index(selected_id)

    return 0


def display_actual_set_editing(
    plan_instance_id: int,
    context_key: str,
) -> None:
    show_corrections = st.toggle(
        "Make Corrections to Workout / Sets",
        value=False,
        key=f"show_actual_set_corrections_{context_key}_{plan_instance_id}",
        help=(
            "Open this only when you need to fix reps, weight, RIR, skipped/completed "
            "state, notes, or substitution details."
        ),
    )

    if not show_corrections:
        st.caption(
            "Need to fix a logged set? Corrections are hidden by default to keep "
            "the normal workout flow focused on logging sets."
        )
        return

    st.markdown("#### Actual Set Corrections")

    try:
        execution_response = api_get(f"/workout-plans/{plan_instance_id}/execution")
    except requests.RequestException as exc:
        st.error(
            f"Failed to load actual set corrections: {extract_api_error_message(exc)}"
        )
        return

    workout_plan_instance = execution_response.get("workout_plan_instance", {})
    execution_session = execution_response.get("execution_session", {})
    planned_exercises = execution_response.get("planned_exercises", [])
    actual_sets = execution_response.get("actual_sets", [])

    plan_status = workout_plan_instance.get("status")
    execution_status = execution_session.get("status")

    editable_statuses = {"in_progress", "completed"}

    if (
        plan_status not in editable_statuses
        and execution_status not in editable_statuses
    ):
        st.info(
            "Actual set corrections are available after actual sets are logged or "
            "after the workout is completed. "
            f"Current plan status: {humanize_label(plan_status)}. "
            f"Execution status: {humanize_label(execution_status)}."
        )
        return

    if not actual_sets:
        st.info("No actual sets are available to correct yet.")
        return

    if plan_status == "completed" or execution_status == "completed":
        st.warning(
            "You are correcting a completed workout. The completed status and "
            "timestamp will remain unchanged, but the planned-vs-actual summary "
            "will update."
        )

    if st.session_state.actual_set_editing_message:
        st.success(st.session_state.actual_set_editing_message)
        st.session_state.actual_set_editing_message = None

    if st.session_state.actual_set_editing_error:
        st.error(st.session_state.actual_set_editing_error)
        st.session_state.actual_set_editing_error = None

    actual_set_options = {
        actual_set_option_label(actual_set): actual_set for actual_set in actual_sets
    }

    planned_options = {
        planned_exercise_option_label(exercise): exercise
        for exercise in planned_exercises
    }

    planned_by_id = planned_exercise_by_id(planned_exercises)
    planned_labels = list(planned_options.keys())
    planned_ids = [
        int(exercise["id"])
        for exercise in planned_exercises
        if exercise.get("id") is not None
    ]

    if not planned_labels:
        st.warning("No planned exercises are available for correction context.")
        return

    selected_actual_label = st.selectbox(
        "Actual Set to Correct",
        options=list(actual_set_options.keys()),
        key=f"actual_set_edit_select_{context_key}_{plan_instance_id}",
    )
    selected_actual_set = actual_set_options[selected_actual_label]

    actual_set_id = selected_actual_set.get("id")
    current_planned_id = selected_actual_set.get("planned_workout_exercise_id")
    current_substitution_for_id = selected_actual_set.get(
        "substitution_for_planned_exercise_id"
    )

    current_reference_id = current_planned_id or current_substitution_for_id
    if current_reference_id is not None:
        current_reference_id = int(current_reference_id)

    is_current_substitution = current_substitution_for_id is not None

    planned_reference_index = get_planned_exercise_index(
        planned_ids,
        current_reference_id,
    )

    current_skipped = bool(selected_actual_set.get("skipped", False))

    status_options = ["Completed", "Skipped"]
    status_index = 1 if current_skipped else 0

    form_key = f"actual_set_edit_form_{context_key}_{plan_instance_id}_{actual_set_id}"

    with st.form(form_key):
        status_choice = st.radio(
            "Correction Status",
            options=status_options,
            index=status_index,
            horizontal=True,
        )

        is_substitution = st.checkbox(
            "This actual set is a substitution",
            value=is_current_substitution,
        )

        selected_planned_label = st.selectbox(
            (
                "Substitution For Planned Exercise"
                if is_substitution
                else "Planned Exercise"
            ),
            options=planned_labels,
            index=planned_reference_index,
        )
        selected_planned_exercise = planned_options[selected_planned_label]

        actual_exercise_name = None
        if is_substitution:
            actual_exercise_name = st.text_input(
                "Actual Exercise Name",
                value=selected_actual_set.get("exercise_name") or "",
                help=(
                    "Use the exercise actually performed. The planned exercise above "
                    "will be preserved as the substitution target."
                ),
            )

        set_number = st.number_input(
            "Set Number",
            min_value=1,
            value=int(selected_actual_set.get("set_number") or 1),
            step=1,
        )

        notes = st.text_area(
            "Notes",
            value=selected_actual_set.get("notes") or "",
        )

        actual_reps = None
        actual_weight = None
        actual_rir = None

        if status_choice == "Completed":
            col1, col2, col3 = st.columns(3)

            with col1:
                actual_reps = st.number_input(
                    "Actual Reps",
                    min_value=0,
                    value=int(selected_actual_set.get("actual_reps") or 0),
                    step=1,
                )

            with col2:
                actual_weight = st.number_input(
                    "Actual Weight",
                    min_value=0.0,
                    value=float(selected_actual_set.get("actual_weight") or 0.0),
                    step=5.0,
                )

            with col3:
                actual_rir = st.slider(
                    "Actual RIR",
                    min_value=0,
                    max_value=10,
                    value=int(selected_actual_set.get("actual_rir") or 0),
                )
        else:
            st.info(
                "Skipped rows are saved without reps, weight, or RIR. "
                "Use notes to explain the skip."
            )

        submit_correction = st.form_submit_button("Save Actual Set Correction")

    if submit_correction:
        completed = status_choice == "Completed"
        skipped = status_choice == "Skipped"

        if completed and skipped:
            st.session_state.actual_set_editing_error = (
                "An actual set cannot be both completed and skipped."
            )
            st.rerun()

        selected_planned_id = int(selected_planned_exercise["id"])

        payload = {
            "set_number": int(set_number),
            "completed": completed,
            "skipped": skipped,
            "notes": notes or None,
        }

        if is_substitution:
            if not actual_exercise_name or not actual_exercise_name.strip():
                st.session_state.actual_set_editing_error = (
                    "Actual Exercise Name is required for substitution corrections."
                )
                st.rerun()

            payload.update(
                {
                    "planned_workout_exercise_id": None,
                    "substitution_for_planned_exercise_id": selected_planned_id,
                    "exercise_name": actual_exercise_name.strip(),
                }
            )
        else:
            planned_name = planned_by_id.get(selected_planned_id, {}).get("name")
            payload.update(
                {
                    "planned_workout_exercise_id": selected_planned_id,
                    "substitution_for_planned_exercise_id": None,
                    "exercise_name": planned_name,
                }
            )

        if completed:
            payload.update(
                {
                    "actual_reps": int(actual_reps),
                    "actual_weight": float(actual_weight),
                    "actual_rir": int(actual_rir),
                }
            )
        else:
            payload.update(
                {
                    "actual_reps": None,
                    "actual_weight": None,
                    "actual_rir": None,
                }
            )

        try:
            edit_response = api_patch(
                f"/workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}",
                payload,
            )

            if edit_response.get("success"):
                st.session_state.actual_set_edit_response = edit_response
                st.session_state.actual_set_editing_message = (
                    f"Actual set {actual_set_id} corrected successfully."
                )
                st.session_state.actual_set_editing_error = None
                st.rerun()

            st.session_state.actual_set_editing_error = "Actual set correction failed."
            st.rerun()

        except requests.RequestException as exc:
            st.session_state.actual_set_editing_error = (
                f"Actual set correction failed: {extract_api_error_message(exc)}"
            )
            st.rerun()

    if st.session_state.get("developer_mode", False):
        with st.expander("Developer details: actual set correction"):
            st.subheader("Raw Execution Response Used By Correction Form")
            st.json(execution_response)

            if st.session_state.actual_set_edit_response:
                st.subheader("Latest Raw PATCH Response")
                st.json(st.session_state.actual_set_edit_response)


def display_post_workout_review_summary(
    execution_id: int | None,
    context_key: str,
) -> None:
    st.subheader("Post-Workout Review")
    st.caption(
        "Reflection only: this summarizes the completed workout. It does not "
        "change the next workout, progression, exercises, sets, reps, RIR, or "
        "nutrition decisions."
    )

    if execution_id is None:
        st.info(
            "Post-workout review is available after the completed execution ID "
            "is available."
        )
        return

    try:
        review_response = api_get(
            f"/workout-executions/{execution_id}/post-workout-summary"
        )
    except requests.RequestException as exc:
        st.info(
            "Post-workout review is not available for this completed workout yet: "
            f"{extract_api_error_message(exc)}"
        )
        return

    if not review_response.get("success"):
        st.info("Post-workout review is not available for this completed workout yet.")
        developer_details(
            f"Developer details: post-workout review {context_key}",
            review_response,
        )
        return

    review_summary = review_response.get("approved_post_workout_review_summary") or {}

    if not review_summary:
        st.info("Post-workout review did not return summary copy.")
        developer_details(
            f"Developer details: post-workout review {context_key}",
            review_response,
        )
        return

    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(
            "**Session summary:** "
            f"{review_summary.get('session_summary', 'Not available.')}"
        )

    with col2:
        st.metric("Confidence", review_summary.get("confidence", "Unknown"))

    review_rows = [
        {
            "Area": "Completion reflection",
            "Review": review_summary.get("completion_reflection", "Not available."),
        },
        {
            "Area": "Effort reflection",
            "Review": review_summary.get("effort_reflection", "Not available."),
        },
        {
            "Area": "Reps / volume reflection",
            "Review": review_summary.get(
                "reps_or_volume_reflection",
                "Not available.",
            ),
        },
        {
            "Area": "Substitutions / skips",
            "Review": review_summary.get(
                "substitutions_or_skips_context",
                "Not available.",
            ),
        },
        {
            "Area": "Logging quality",
            "Review": review_summary.get("logging_quality_note", "Not available."),
        },
        {
            "Area": "Next-time focus",
            "Review": review_summary.get("next_time_focus", "Not available."),
        },
    ]

    st.dataframe(
        pd.DataFrame(review_rows),
        width="stretch",
        hide_index=True,
    )

    developer_details(
        f"Developer details: post-workout review {context_key}",
        review_response,
    )


def display_complete_workout_control(
    plan_instance_id: int, context_key: str = "workout"
) -> None:
    st.subheader("Complete Workout")

    if st.session_state.workout_completion_message:
        st.success(st.session_state.workout_completion_message)
        st.session_state.workout_completion_message = None

    if st.session_state.workout_completion_error:
        st.error(st.session_state.workout_completion_error)
        st.session_state.workout_completion_error = None

    try:
        execution_response = api_get(f"/workout-plans/{plan_instance_id}/execution")
    except requests.RequestException as exc:
        st.error(f"Failed to load completion state: {extract_api_error_message(exc)}")
        return

    workout_plan_instance = execution_response.get("workout_plan_instance", {})
    execution_session = execution_response.get("execution_session", {})
    planned_exercises = execution_response.get("planned_exercises", [])

    plan_status = workout_plan_instance.get("status")
    execution_status = execution_session.get("status")

    if plan_status == "completed" or execution_status == "completed":
        completed_at = execution_session.get(
            "completed_at"
        ) or workout_plan_instance.get("completed_at")
        st.info("This planned workout has already been completed.")

        if completed_at:
            st.caption(f"Completed at: {completed_at}")

    elif plan_status == "in_progress" or execution_status == "in_progress":
        st.write(
            "Complete this planned workout after you finish logging the actual sets "
            "you want included in the planned-vs-actual summary."
        )

        if st.button(
            "Complete Workout",
            key=f"complete_workout_plan_button_{context_key}_{plan_instance_id}",
        ):
            try:
                complete_response = api_post(
                    f"/workout-plans/{plan_instance_id}/complete"
                )

                if complete_response.get("success"):
                    st.session_state.completed_workout_plan_response = complete_response
                    st.session_state.started_workout_plan_response = {
                        **complete_response,
                        "planned_exercises": planned_exercises,
                    }
                    st.session_state.workout_completion_message = (
                        "Workout completed successfully."
                    )
                    st.session_state.workout_completion_error = None
                    st.rerun()
                else:
                    st.session_state.workout_completion_error = (
                        "Workout completion failed."
                    )

            except requests.RequestException as exc:
                st.session_state.workout_completion_error = (
                    f"Workout completion failed: {extract_api_error_message(exc)}"
                )
                st.rerun()

    else:
        st.info(
            "Complete Workout will be available after actual set logging changes "
            "this planned workout to in progress. "
            f"Current plan status: {humanize_label(plan_status)}. "
            f"Execution status: {humanize_label(execution_status)}."
        )

    completion_response = st.session_state.completed_workout_plan_response

    if completion_response:
        workout_plan_result = completion_response.get("workout_plan_instance", {})
        execution_result = completion_response.get("execution_session", {})
        summary = completion_response.get("planned_vs_actual_summary", {})

        st.write("**Latest Completion Result**")

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Plan Status",
            humanize_label(workout_plan_result.get("status")),
        )
        col2.metric(
            "Execution Status",
            humanize_label(execution_result.get("status")),
        )
        col3.metric(
            "Completed At",
            execution_result.get("completed_at")
            or workout_plan_result.get("completed_at")
            or "Unknown",
        )

        display_planned_vs_actual_summary(
            summary,
            planned_exercises=planned_exercises,
            actual_sets=execution_response.get("actual_sets", []),
        )

        completion_execution_id = execution_result.get("id")
        if completion_execution_id is not None:
            display_post_workout_review_summary(
                int(completion_execution_id),
                context_key=f"completion_result_{plan_instance_id}",
            )

    if st.session_state.get("developer_mode", False):
        with st.expander("Developer details: workout completion"):
            st.subheader("Raw Execution Response Used By Completion Control")
            st.json(execution_response)

            if completion_response:
                st.subheader("Raw Complete Response")
                st.json(completion_response)


def display_workout_execution_review(plan_instance_id: int) -> None:
    st.subheader("Workout Execution Review")

    try:
        execution_response = api_get(f"/workout-plans/{plan_instance_id}/execution")
    except requests.RequestException as exc:
        st.error(
            f"Failed to load workout execution review: {extract_api_error_message(exc)}"
        )
        return

    workout_plan_instance = execution_response.get("workout_plan_instance", {})
    execution_session = execution_response.get("execution_session", {})
    planned_exercises = execution_response.get("planned_exercises", [])
    actual_sets = execution_response.get("actual_sets", [])
    active_substitutions = merged_active_substitution_map(
        plan_instance_id,
        execution_response,
    )

    if st.session_state.get("developer_mode", False):
        col1, col2, col3 = st.columns(3)
    else:
        col1, col2 = st.columns(2)
        col3 = None

    col1.metric(
        "Plan Status",
        humanize_label(workout_plan_instance.get("status")),
    )
    col2.metric(
        "Execution Status",
        humanize_label(execution_session.get("status")),
    )
    if col3 is not None:
        col3.metric(
            "Workout Session ID",
            execution_session.get("workout_session_id") or "Not created",
        )

    col4, col5 = st.columns(2)

    col4.metric(
        "Started At",
        execution_session.get("started_at") or "Not started",
    )
    col5.metric(
        "Completed At",
        execution_session.get("completed_at") or "Not completed",
    )

    with st.expander("Planned exercises and substitutions", expanded=False):
        display_planned_exercises(planned_exercises)
        display_active_substitution_summary(planned_exercises, active_substitutions)

    with st.expander("Logged sets", expanded=False):
        display_actual_sets(actual_sets)

    display_actual_set_editing(
        plan_instance_id,
        context_key="execution_review",
    )

    planned_vs_actual_response = None
    planned_vs_actual_error = None

    try:
        planned_vs_actual_response = api_get(
            f"/workout-plans/{plan_instance_id}/planned-vs-actual"
        )
        display_planned_vs_actual_summary(
            planned_vs_actual_response.get("planned_vs_actual_summary", {}),
            planned_exercises=planned_vs_actual_response.get("planned_exercises", []),
            actual_sets=planned_vs_actual_response.get("actual_sets", []),
        )
    except requests.RequestException as exc:
        planned_vs_actual_error = extract_api_error_message(exc)
        st.info(
            f"Planned-vs-actual summary is not available yet: {planned_vs_actual_error}"
        )

    review_execution_id = execution_session.get("id")
    if (
        workout_plan_instance.get("status") == "completed"
        or execution_session.get("status") == "completed"
    ) and review_execution_id is not None:
        display_post_workout_review_summary(
            int(review_execution_id),
            context_key=f"execution_review_{plan_instance_id}",
        )

    if st.session_state.get("developer_mode", False):
        with st.expander("Developer details: workout execution review"):
            st.subheader("Raw Execution Response")
            st.json(execution_response)

            if planned_vs_actual_response:
                st.subheader("Raw Planned-vs-Actual Response")
                st.json(planned_vs_actual_response)

            if planned_vs_actual_error:
                st.subheader("Planned-vs-Actual Error")
                st.write(planned_vs_actual_error)


def display_workout_execution_history_item(
    history_item: dict,
    context_scope: str = "history",
) -> None:
    workout_plan_instance = history_item.get("workout_plan_instance", {})
    execution_session = history_item.get("execution_session") or {}
    planned_vs_actual_summary = history_item.get("planned_vs_actual_summary")

    plan_instance_id = workout_plan_instance.get("id", "Unknown")
    plan_status = workout_plan_instance.get("status")
    execution_status = execution_session.get("status")

    if st.session_state.get("developer_mode", False):
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Plan Instance ID",
            plan_instance_id,
        )
        col2.metric(
            "Plan Status",
            humanize_label(plan_status),
        )
        col3.metric(
            "Execution Status",
            humanize_label(execution_status),
        )

        col4, col5, col6 = st.columns(3)
        col6.metric(
            "Workout Session ID",
            execution_session.get("workout_session_id") or "Not created",
        )
    else:
        col4, col5 = st.columns(2)

    col4.metric(
        "Scenario",
        scenario_display_name(workout_plan_instance.get("scenario")),
    )
    col5.metric(
        "Confidence",
        workout_plan_instance.get("confidence", "Unknown"),
    )

    title = history_item.get("approved_workout_title") or workout_plan_instance.get(
        "title",
        "Unknown",
    )
    session_focus = history_item.get("approved_workout_session_focus") or "Unknown"

    st.write(f"**Workout:** {title}")
    st.write(f"**Focus:** {session_focus}")

    time_rows = [
        {
            "Field": "Selected At",
            "Value": workout_plan_instance.get("selected_at") or "Unknown",
        },
        {
            "Field": "Started At",
            "Value": execution_session.get("started_at") or "Not started",
        },
        {
            "Field": "Completed At",
            "Value": execution_session.get("completed_at")
            or workout_plan_instance.get("completed_at")
            or "Not completed",
        },
    ]

    st.dataframe(
        pd.DataFrame(time_rows),
        width="stretch",
        hide_index=True,
    )

    if plan_status in {"in_progress", "completed"} or execution_status in {
        "in_progress",
        "completed",
    }:
        if planned_vs_actual_summary:
            display_planned_vs_actual_summary(planned_vs_actual_summary)

            history_execution_id = execution_session.get("id")
            if (
                plan_status == "completed" or execution_status == "completed"
            ) and history_execution_id is not None:
                display_post_workout_review_summary(
                    int(history_execution_id),
                    context_key=f"{context_scope}_{plan_instance_id}",
                )
        else:
            st.info("Planned-vs-actual summary is not available for this item yet.")
    else:
        st.info(
            "Planned-vs-actual summary is not available until the workout is "
            "in progress or completed."
        )

    if plan_instance_id != "Unknown" and (
        plan_status in {"in_progress", "completed"}
        or execution_status in {"in_progress", "completed"}
    ):
        display_actual_set_editing(
            int(plan_instance_id),
            context_key=f"{context_scope}_{plan_instance_id}_{execution_session.get('id') or execution_session.get('workout_session_id') or 'no_execution'}",
        )


def display_workout_execution_history(
    user_id: int,
    context_scope: str = "history",
) -> None:
    st.subheader("Workout Execution History")

    try:
        history_response = api_get(f"/workout-plans/history/{user_id}")
    except requests.RequestException as exc:
        st.error(
            "Failed to load workout execution history: "
            f"{extract_api_error_message(exc)}"
        )
        return

    history_items = history_response.get("workout_plan_instances", [])

    if not history_items:
        st.info("No workout plan execution history found for this user.")
    else:
        for history_item in history_items:
            workout_plan_instance = history_item.get("workout_plan_instance", {})
            execution_session = history_item.get("execution_session") or {}

            plan_instance_id = workout_plan_instance.get("id", "Unknown")
            title = history_item.get(
                "approved_workout_title"
            ) or workout_plan_instance.get(
                "title",
                "Workout Plan",
            )
            plan_status = humanize_label(workout_plan_instance.get("status"))
            selected_at = workout_plan_instance.get("selected_at") or "Unknown"

            if st.session_state.get("developer_mode", False):
                expander_label = (
                    f"Plan {plan_instance_id} — {title} — "
                    f"{plan_status} — selected {selected_at}"
                )
            else:
                expander_label = f"{title} — {plan_status} — selected {selected_at}"

            with st.expander(expander_label):
                display_workout_execution_history_item(
                    history_item,
                    context_scope=context_scope,
                )

                if execution_session.get("completed_at"):
                    st.caption(f"Completed at: {execution_session['completed_at']}")

    if st.session_state.get("developer_mode", False):
        with st.expander("Developer details: workout execution history"):
            st.json(history_response)


TRAINING_ENVIRONMENT_OPTIONS = {
    "commercial_gym": "Commercial Gym",
    "home_gym": "Home Gym",
    "bodyweight_only": "Bodyweight Only",
    "limited_equipment": "Limited Equipment",
    "unknown": "Unknown",
}

KNOWN_EQUIPMENT_OPTIONS = [
    "adjustable_bench",
    "barbell",
    "bike",
    "bodyweight",
    "cable",
    "dumbbell",
    "ez_bar",
    "kettlebell",
    "machine",
    "plates",
    "pull_up_bar",
    "rack",
    "resistance_band",
    "treadmill",
]


def equipment_display_name(value: str) -> str:
    return value.replace("_", " ").title()


def normalize_catalog_list(value: object) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item) for item in value if item is not None]

    if isinstance(value, str):
        return [
            item.strip() for item in value.replace("|", ",").split(",") if item.strip()
        ]

    return [str(value)]


def catalog_value_label(value: object) -> str:
    if value is None or value == "":
        return "Unknown"

    return equipment_display_name(str(value))


def exercise_catalog_equipment(exercise: dict) -> list[str]:
    return normalize_catalog_list(
        exercise.get("equipment_required") or exercise.get("equipment")
    )


def exercise_catalog_muscle_groups(exercise: dict) -> list[str]:
    return normalize_catalog_list(
        exercise.get("primary_muscle_groups") or exercise.get("muscle_group")
    )


def exercise_catalog_movement_pattern(exercise: dict) -> str:
    return (
        exercise.get("movement_pattern") or exercise.get("movement_type") or "unknown"
    )


def exercise_catalog_type(exercise: dict) -> str:
    return (
        exercise.get("exercise_type")
        or exercise.get("category")
        or exercise.get("type")
        or "unknown"
    )


def exercise_matches_equipment_profile(
    exercise: dict,
    available_equipment: list[str],
    unavailable_equipment: list[str],
) -> bool:
    required_equipment = set(exercise_catalog_equipment(exercise))
    available = set(available_equipment)
    unavailable = set(unavailable_equipment)

    if required_equipment & unavailable:
        return False

    if available and not required_equipment.issubset(available):
        return False

    return True


def display_exercise_catalog(user_id: int) -> None:
    st.header("📚 Exercise Catalog")

    try:
        catalog_response = api_get("/exercise-catalog")
    except requests.RequestException:
        try:
            catalog_response = api_get("/exercises")
        except requests.RequestException as exc:
            st.error(
                f"Failed to load exercise catalog: {extract_api_error_message(exc)}"
            )
            return

    exercises = catalog_response.get("exercises", [])

    if not exercises:
        st.info("No catalog exercises found.")
        if st.session_state.get("developer_mode", False):
            with st.expander("Developer details: exercise catalog"):
                st.json(catalog_response)
        return

    try:
        equipment_profile_response = api_get(f"/users/{user_id}/equipment-profile")
        equipment_profile = equipment_profile_response.get("equipment_profile", {})
    except requests.RequestException:
        equipment_profile_response = {}
        equipment_profile = {}

    available_equipment = normalize_catalog_list(
        equipment_profile.get("available_equipment")
    )
    unavailable_equipment = normalize_catalog_list(
        equipment_profile.get("unavailable_equipment")
    )

    st.caption(
        "Browse the seeded exercise catalog used by equipment-aware workout previews."
    )

    search_query = (
        st.text_input(
            "Search by exercise name",
            value="",
            key="exercise_catalog_search_query",
        )
        .strip()
        .lower()
    )

    equipment_options = sorted(
        {
            equipment
            for exercise in exercises
            for equipment in exercise_catalog_equipment(exercise)
        }
    )

    movement_pattern_options = sorted(
        {
            exercise_catalog_movement_pattern(exercise)
            for exercise in exercises
            if exercise_catalog_movement_pattern(exercise) != "unknown"
        }
    )

    muscle_group_options = sorted(
        {
            muscle_group
            for exercise in exercises
            for muscle_group in exercise_catalog_muscle_groups(exercise)
        }
    )

    exercise_type_options = sorted(
        {
            exercise_catalog_type(exercise)
            for exercise in exercises
            if exercise_catalog_type(exercise) != "unknown"
        }
    )

    difficulty_options = sorted(
        {
            str(exercise.get("difficulty"))
            for exercise in exercises
            if exercise.get("difficulty")
        }
    )

    col1, col2 = st.columns(2)

    with col1:
        selected_equipment = st.multiselect(
            "Required Equipment",
            options=equipment_options,
            format_func=equipment_display_name,
            key="exercise_catalog_equipment_filter",
        )

        selected_movement_patterns = st.multiselect(
            "Movement Pattern",
            options=movement_pattern_options,
            format_func=catalog_value_label,
            key="exercise_catalog_movement_pattern_filter",
        )

    with col2:
        selected_muscle_groups = st.multiselect(
            "Primary Muscle Group",
            options=muscle_group_options,
            format_func=catalog_value_label,
            key="exercise_catalog_muscle_group_filter",
        )

        selected_exercise_types = st.multiselect(
            "Exercise Type / Category",
            options=exercise_type_options,
            format_func=catalog_value_label,
            key="exercise_catalog_type_filter",
        )

    selected_difficulties = st.multiselect(
        "Difficulty",
        options=difficulty_options,
        format_func=catalog_value_label,
        key="exercise_catalog_difficulty_filter",
    )

    compatible_only = st.checkbox(
        "Show only exercises compatible with my current equipment profile",
        value=False,
        key="exercise_catalog_compatible_only",
    )

    filtered_exercises = []

    for exercise in exercises:
        exercise_name = str(exercise.get("name", ""))

        if search_query and search_query not in exercise_name.lower():
            continue

        exercise_equipment = set(exercise_catalog_equipment(exercise))
        exercise_movement_pattern = exercise_catalog_movement_pattern(exercise)
        exercise_muscle_groups = set(exercise_catalog_muscle_groups(exercise))
        exercise_type = exercise_catalog_type(exercise)
        exercise_difficulty = str(exercise.get("difficulty", ""))

        if selected_equipment and not exercise_equipment.intersection(
            selected_equipment
        ):
            continue

        if (
            selected_movement_patterns
            and exercise_movement_pattern not in selected_movement_patterns
        ):
            continue

        if selected_muscle_groups and not exercise_muscle_groups.intersection(
            selected_muscle_groups
        ):
            continue

        if selected_exercise_types and exercise_type not in selected_exercise_types:
            continue

        if selected_difficulties and exercise_difficulty not in selected_difficulties:
            continue

        if compatible_only and not exercise_matches_equipment_profile(
            exercise,
            available_equipment,
            unavailable_equipment,
        ):
            continue

        filtered_exercises.append(exercise)

    st.caption(f"Showing {len(filtered_exercises)} of {len(exercises)} exercises.")

    if compatible_only and not available_equipment and not unavailable_equipment:
        st.info(
            "No explicit equipment profile is loaded for this user, so compatibility "
            "uses the backend/default profile assumptions."
        )

    if not filtered_exercises:
        st.warning("No exercises match the selected filters.")
    else:
        catalog_rows = []

        for exercise in filtered_exercises:
            catalog_rows.append(
                {
                    "Exercise": exercise.get("name", "Unknown"),
                    "Type": catalog_value_label(exercise_catalog_type(exercise)),
                    "Movement Pattern": catalog_value_label(
                        exercise_catalog_movement_pattern(exercise)
                    ),
                    "Primary Muscle Groups": ", ".join(
                        catalog_value_label(group)
                        for group in exercise_catalog_muscle_groups(exercise)
                    )
                    or "Unknown",
                    "Required Equipment": ", ".join(
                        equipment_display_name(equipment)
                        for equipment in exercise_catalog_equipment(exercise)
                    )
                    or "Bodyweight / none",
                    "Difficulty": catalog_value_label(exercise.get("difficulty")),
                }
            )

        st.dataframe(
            pd.DataFrame(catalog_rows),
            width="stretch",
            hide_index=True,
        )

    if st.session_state.get("developer_mode", False):
        with st.expander("Developer details: exercise catalog"):
            st.subheader("Catalog Response")
            st.json(catalog_response)

            if equipment_profile_response:
                st.subheader("Equipment Profile Response")
                st.json(equipment_profile_response)


# =====================================
# App Configuration
# =====================================

st.set_page_config(
    page_title="Fitness AI",
    layout="wide",
)

st.title("🏋️ Fitness AI Platform")
st.caption("Daily workout flow, logging, history, and AI coaching in one place.")
# Streamlit Today + Workout UX Consolidation v3

# =====================================
# Session State Initialization
# =====================================

SESSION_DEFAULTS = {
    "health_report": None,
    "health_report_timestamp": None,
    "report_job_id": None,
    "report_job_status": None,
    "last_completed_job_id": None,
    "current_sets": [],
    "food_search_results": [],
    "equipment_profile_saved": False,
    "selected_workout_plan_response": None,
    "started_workout_plan_response": None,
    "workout_plan_action_error": None,
    "actual_set_logging_message": None,
    "completed_workout_plan_response": None,
    "workout_completion_message": None,
    "workout_completion_error": None,
    "actual_set_editing_message": None,
    "actual_set_editing_error": None,
    "actual_set_edit_response": None,
    "visible_substitution_candidates": [],
    "applied_substitution_responses": {},
    "substitution_apply_message": None,
    "substitution_apply_error": None,
    "substitution_flow_ready_to_do_workout": False,
    "workout_flow_step": "1. Plan",
    "workout_flow_step_selector": "1. Plan",
    "workout_flow_step_override": None,
    "developer_mode": False,
    "current_user_id": None,
    "last_user_id": None,
    "daily_recommendation_by_user": {},
    "daily_recommendation_error_by_user": {},
    "workout_explanation_by_user": {},
    "workout_explanation_error_by_user": {},
}

for key, default_value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        if isinstance(default_value, list):
            st.session_state[key] = default_value.copy()
        elif isinstance(default_value, dict):
            st.session_state[key] = default_value.copy()
        else:
            st.session_state[key] = default_value


def request_workout_flow_step(step: str) -> None:
    """Request a workout-flow step change for the next Streamlit rerun.

    The visible step selector uses its own widget key. Streamlit does not allow
    modifying a widget-backed session-state key after that widget has rendered,
    so button handlers set a non-widget override key instead. The override is
    consumed before the selector is instantiated on the next run.
    """
    st.session_state.workout_flow_step = step
    st.session_state.workout_flow_step_override = step


def reset_user_scoped_state() -> None:
    st.session_state.health_report = None
    st.session_state.health_report_timestamp = None
    st.session_state.report_job_id = None
    st.session_state.report_job_status = None
    st.session_state.last_completed_job_id = None
    st.session_state.current_sets = []
    st.session_state.food_search_results = []
    st.session_state.equipment_profile_saved = False
    st.session_state.selected_workout_plan_response = None
    st.session_state.started_workout_plan_response = None
    st.session_state.workout_plan_action_error = None
    st.session_state.actual_set_logging_message = None
    st.session_state.completed_workout_plan_response = None
    st.session_state.workout_completion_message = None
    st.session_state.workout_completion_error = None
    st.session_state.actual_set_editing_message = None
    st.session_state.actual_set_editing_error = None
    st.session_state.actual_set_edit_response = None
    st.session_state.visible_substitution_candidates = []
    st.session_state.applied_substitution_responses = {}
    st.session_state.substitution_apply_message = None
    st.session_state.substitution_apply_error = None
    st.session_state.substitution_flow_ready_to_do_workout = False
    st.session_state.workout_flow_step = "1. Plan"
    st.session_state.workout_flow_step_selector = "1. Plan"
    st.session_state.workout_flow_step_override = None


def handle_user_switch(selected_user_id: int) -> None:
    """Clear transient UI state when the selected Streamlit user changes.

    Most data entry and workout widgets are user-scoped. If those values survive
    a user switch, the UI can show stale cards or fail to refresh user-specific
    panels. Keep per-user caches keyed by user_id, but clear active/transient
    workflow state whenever the selected user changes.
    """
    st.session_state.current_user_id = selected_user_id

    last_user_id = st.session_state.get("last_user_id")

    if last_user_id is None:
        st.session_state.last_user_id = selected_user_id
        st.session_state.selected_user_id = selected_user_id
        return

    if last_user_id == selected_user_id:
        st.session_state.selected_user_id = selected_user_id
        return

    reset_user_scoped_state()
    st.session_state.current_user_id = selected_user_id
    st.session_state.selected_user_id = selected_user_id
    st.session_state.last_user_id = selected_user_id
    st.rerun()


USER_OPTIONS = {
    "User 1": 1,
    "User 2": 2,
    "QA 101 — Under-recovered lifter": 101,
    "QA 102 — Well-recovered baseline": 102,
    "QA 103 — Nutrition/training mismatch": 103,
    "QA 104 — Improving after deload": 104,
    "QA 105 — Messy/incomplete logging": 105,
}

# =====================================
# Sidebar Controls
# =====================================

with st.sidebar:
    st.header("Controls")

    selected_user_label = st.selectbox(
        "User",
        options=list(USER_OPTIONS.keys()),
        index=0,
    )

    user_id = USER_OPTIONS[selected_user_label]

    st.session_state.developer_mode = st.toggle(
        "Developer Mode",
        value=st.session_state.developer_mode,
        help="Show raw backend responses and internal diagnostic details.",
    )

    st.divider()
    st.caption("Primary flow")
    st.write("Today → Workout → Nutrition → History → Reports")

handle_user_switch(user_id)


# =====================================
# Small UI Helpers
# =====================================


def developer_details(label: str, payload: object) -> None:
    if st.session_state.get("developer_mode", False):
        with st.expander(label):
            st.json(payload)


def render_status_pill(label: str, value: object) -> None:
    st.caption(f"**{label}:** {humanize_label(str(value)) if value else 'Unknown'}")


def get_plan_instance_id_from_response(plan_response: dict | None) -> int | None:
    if not plan_response:
        return None

    workout_plan_instance = plan_response.get("workout_plan_instance") or {}
    plan_instance_id = workout_plan_instance.get("id")

    if plan_instance_id is None:
        return None

    try:
        return int(plan_instance_id)
    except (TypeError, ValueError):
        return None


def get_active_plan_response(user_id: int) -> dict | None:
    active_response = (
        st.session_state.started_workout_plan_response
        or st.session_state.selected_workout_plan_response
    )

    if active_response:
        return active_response

    try:
        history_response = api_get(f"/workout-plans/history/{user_id}")
    except requests.RequestException:
        return None

    for history_item in history_response.get("workout_plan_instances", []):
        workout_plan_instance = history_item.get("workout_plan_instance") or {}
        status = workout_plan_instance.get("status")

        if status not in {"selected", "started", "in_progress"}:
            continue

        plan_instance_id = workout_plan_instance.get("id")
        if plan_instance_id is None:
            continue

        try:
            execution_response = api_get(
                f"/workout-plans/{int(plan_instance_id)}/execution"
            )
        except (requests.RequestException, TypeError, ValueError):
            continue

        if status == "selected":
            st.session_state.selected_workout_plan_response = execution_response
        else:
            st.session_state.started_workout_plan_response = execution_response

        return execution_response

    return None


def refresh_active_plan_response(plan_instance_id: int) -> dict | None:
    try:
        execution_response = api_get(f"/workout-plans/{plan_instance_id}/execution")
    except requests.RequestException:
        return None

    workout_plan_instance = execution_response.get("workout_plan_instance") or {}
    status = workout_plan_instance.get("status")

    if status == "selected":
        st.session_state.selected_workout_plan_response = execution_response
        st.session_state.started_workout_plan_response = None
    elif status in {"started", "in_progress", "completed"}:
        st.session_state.started_workout_plan_response = execution_response
        if status != "selected":
            st.session_state.selected_workout_plan_response = None

    return execution_response


def get_plan_statuses(plan_response: dict | None) -> tuple[str | None, str | None]:
    if not plan_response:
        return None, None

    workout_plan_instance = plan_response.get("workout_plan_instance") or {}
    execution_session = plan_response.get("execution_session") or {}

    return workout_plan_instance.get("status"), execution_session.get("status")


def is_started_or_in_progress(plan_response: dict | None) -> bool:
    plan_status, execution_status = get_plan_statuses(plan_response)
    return plan_status in {"started", "in_progress"} or execution_status in {
        "started",
        "in_progress",
    }


def is_in_progress(plan_response: dict | None) -> bool:
    plan_status, execution_status = get_plan_statuses(plan_response)
    return plan_status == "in_progress" or execution_status == "in_progress"


def render_active_plan_summary(plan_response: dict | None) -> None:
    if not plan_response:
        st.info("No active selected workout plan yet. Preview and select one first.")
        return

    workout_plan_instance = plan_response.get("workout_plan_instance") or {}
    execution_session = plan_response.get("execution_session") or {}
    planned_exercises = plan_response.get("planned_exercises") or []

    if st.session_state.get("developer_mode", False):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Plan ID", workout_plan_instance.get("id", "Unknown"))
        col2.metric("Plan", humanize_label(workout_plan_instance.get("status")))
        col3.metric("Execution", humanize_label(execution_session.get("status")))
        col4.metric(
            "Workout Session",
            execution_session.get("workout_session_id") or "Not created",
        )
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Plan Status", humanize_label(workout_plan_instance.get("status")))
        col2.metric("Execution", humanize_label(execution_session.get("status")))
        col3.metric("Exercises", len(planned_exercises))

    if execution_session.get("started_at") or execution_session.get("completed_at"):
        col5, col6 = st.columns(2)
        col5.caption(f"Started: {execution_session.get('started_at') or 'Not started'}")
        col6.caption(
            f"Completed: {execution_session.get('completed_at') or 'Not completed'}"
        )

    active_substitutions = merged_active_substitution_map(
        get_plan_instance_id_from_response(plan_response) or 0,
        plan_response,
    )

    if planned_exercises:
        with st.expander("Workout exercise details", expanded=False):
            display_planned_exercises(planned_exercises, active_substitutions)
            display_active_substitution_summary(planned_exercises, active_substitutions)


def render_preview_exercise_snapshot(workout_plan: dict) -> None:
    exercises = workout_plan.get("exercises") or []

    if not exercises:
        st.info("No exercises were returned for today's workout preview.")
        return

    rows = []
    for index, exercise in enumerate(exercises):
        rows.append(
            {
                "Slot": workout_exercise_role_label(index, exercise),
                "Exercise": exercise.get("name", "Unknown"),
                "Sets": exercise.get("sets", "Unknown"),
                "Reps": format_workout_range(
                    exercise.get("reps_min"),
                    exercise.get("reps_max"),
                ),
                "RIR": format_workout_range(
                    exercise.get("rir_min"),
                    exercise.get("rir_max"),
                ),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def select_today_workout(user_id: int, button_key: str) -> None:
    if st.button("Select This Workout", key=button_key, type="primary"):
        try:
            select_response = api_post(f"/workout-plans/{user_id}/select")
        except requests.RequestException as exc:
            st.session_state.workout_plan_action_error = (
                f"Workout plan selection failed: {extract_api_error_message(exc)}"
            )
            st.rerun()

        if select_response.get("success"):
            st.session_state.selected_workout_plan_response = select_response
            st.session_state.started_workout_plan_response = None
            st.session_state.workout_plan_action_error = None
            st.session_state.actual_set_logging_message = None
            st.session_state.completed_workout_plan_response = None
            st.session_state.workout_completion_message = None
            st.session_state.workout_completion_error = None
            st.session_state.visible_substitution_candidates = []
            st.session_state.applied_substitution_responses = {}
            st.session_state.substitution_apply_message = None
            st.session_state.substitution_apply_error = None
            st.session_state.substitution_flow_ready_to_do_workout = False
            request_workout_flow_step("1. Plan")
            st.success("Workout plan selected. Review substitutions before starting.")
            st.rerun()

        st.session_state.workout_plan_action_error = "Workout plan selection failed."
        st.rerun()


def start_active_workout(
    plan_response: dict | None, context_key: str = "workout"
) -> None:
    plan_instance_id = get_plan_instance_id_from_response(plan_response)

    if plan_instance_id is None:
        st.info("Select a workout plan before starting.")
        return

    workout_plan_instance = plan_response.get("workout_plan_instance") or {}
    plan_status = workout_plan_instance.get("status")

    if plan_status == "selected":
        if st.button(
            "Start Workout",
            key=f"start_workout_{context_key}_{plan_instance_id}",
            type="primary",
        ):
            try:
                start_response = api_post(f"/workout-plans/{plan_instance_id}/start")
            except requests.RequestException as exc:
                st.session_state.workout_plan_action_error = (
                    f"Workout plan start failed: {extract_api_error_message(exc)}"
                )
                st.rerun()

            if start_response.get("success"):
                st.session_state.started_workout_plan_response = start_response
                st.session_state.workout_plan_action_error = None
                st.session_state.actual_set_logging_message = None
                st.session_state.completed_workout_plan_response = None
                st.session_state.workout_completion_message = None
                st.session_state.workout_completion_error = None
                request_workout_flow_step("2. Do Workout")
                st.success("Workout started.")
                st.rerun()

            st.session_state.workout_plan_action_error = "Workout plan start failed."
            st.rerun()

    elif plan_status in {"started", "in_progress"}:
        st.success("Workout is active. Log sets below.")
    elif plan_status == "completed":
        st.info("This workout is already completed.")
    else:
        st.info(f"Current plan status: {humanize_label(plan_status)}")


def render_equipment_profile_editor(user_id: int) -> None:
    if st.session_state.equipment_profile_saved:
        st.success(
            "Equipment profile saved. Workout preview will use the updated profile."
        )
        st.session_state.equipment_profile_saved = False

    try:
        equipment_profile_response = api_get(f"/users/{user_id}/equipment-profile")
    except requests.RequestException as exc:
        st.error(f"Failed to load equipment profile: {extract_api_error_message(exc)}")
        return

    equipment_profile = equipment_profile_response.get("equipment_profile", {})
    equipment_profile_source = equipment_profile_response.get("source", "unknown")
    source_label = (
        "Explicit profile"
        if equipment_profile_source == "explicit"
        else "Default profile"
    )

    st.caption(f"Profile source: {source_label}")

    current_training_environment = equipment_profile.get(
        "training_environment",
        "unknown",
    )
    current_available_equipment = equipment_profile.get("available_equipment", [])
    current_unavailable_equipment = equipment_profile.get("unavailable_equipment", [])

    training_environment_keys = list(TRAINING_ENVIRONMENT_OPTIONS.keys())
    training_environment_index = (
        training_environment_keys.index(current_training_environment)
        if current_training_environment in training_environment_keys
        else training_environment_keys.index("unknown")
    )

    with st.form("equipment_profile_form"):
        selected_training_environment = st.selectbox(
            "Training Environment",
            options=training_environment_keys,
            format_func=lambda value: TRAINING_ENVIRONMENT_OPTIONS[value],
            index=training_environment_index,
        )

        selected_available_equipment = st.multiselect(
            "Available Equipment",
            options=KNOWN_EQUIPMENT_OPTIONS,
            default=[
                equipment
                for equipment in current_available_equipment
                if equipment in KNOWN_EQUIPMENT_OPTIONS
            ],
            format_func=equipment_display_name,
        )

        selected_unavailable_equipment = st.multiselect(
            "Unavailable Equipment",
            options=KNOWN_EQUIPMENT_OPTIONS,
            default=[
                equipment
                for equipment in current_unavailable_equipment
                if equipment in KNOWN_EQUIPMENT_OPTIONS
            ],
            format_func=equipment_display_name,
        )

        save_equipment_profile = st.form_submit_button("Save Equipment Profile")

    if save_equipment_profile:
        payload = {
            "training_environment": selected_training_environment,
            "available_equipment": selected_available_equipment,
            "unavailable_equipment": selected_unavailable_equipment,
        }

        try:
            save_response = api_put(f"/users/{user_id}/equipment-profile", payload)
        except requests.RequestException as exc:
            st.error(f"Equipment profile save failed: {extract_api_error_message(exc)}")
            return

        if save_response.get("success"):
            st.session_state.equipment_profile_saved = True
            st.session_state.selected_workout_plan_response = None
            st.session_state.started_workout_plan_response = None
            st.session_state.workout_plan_action_error = None
            st.session_state.actual_set_logging_message = None
            st.session_state.completed_workout_plan_response = None
            st.session_state.workout_completion_message = None
            st.session_state.workout_completion_error = None
            st.session_state.visible_substitution_candidates = []
            st.session_state.applied_substitution_responses = {}
            st.session_state.substitution_apply_message = None
            st.session_state.substitution_apply_error = None
            st.session_state.workout_explanation_by_user.pop(user_id, None)
            st.session_state.workout_explanation_error_by_user.pop(user_id, None)
            st.rerun()

        st.error("Equipment profile save failed.")

    developer_details(
        "Developer details: equipment profile", equipment_profile_response
    )


def render_readiness_snapshot(user_id: int) -> None:
    st.subheader("Readiness")

    try:
        data = api_get(f"/health-state/{user_id}")
    except requests.RequestException as exc:
        st.error(f"Failed to load health state: {extract_api_error_message(exc)}")
        return

    if not data.get("success"):
        st.info("Health state is not available yet.")
        return

    health_state = data["health_state"]
    recovery = health_state.get("recovery_state", {})
    training = health_state.get("training_state", {})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Recovery", recovery.get("recovery_score", "Unknown"))
    col2.metric("Readiness", recovery.get("readiness_level", "Unknown"))
    col3.metric("Fatigue Risk", recovery.get("fatigue_risk", "Unknown"))
    col4.metric("Stress", health_state.get("system_stress_level", "Unknown"))

    st.caption(
        "Training: "
        f"{training.get('adherence_level', 'Unknown')} adherence | "
        f"{training.get('training_trend', 'Unknown')} trend"
    )
    developer_details("Developer details: health state", data)


def get_daily_recommendation_for_user(user_id: int) -> dict | None:
    """Fetch daily recommendation data and cache it by user_id.

    The cache is intentionally keyed by user_id so switching 101 → 102 → 103
    can never reuse a recommendation from the previous user. A successful fetch
    always replaces that user's cached value; if a transient backend error occurs,
    the UI may show that same user's cached value instead of going blank.
    """
    cache = st.session_state.daily_recommendation_by_user
    errors = st.session_state.daily_recommendation_error_by_user

    try:
        recommendation_data = api_get(f"/recommendations/daily/{user_id}")
        cache[user_id] = recommendation_data
        errors.pop(user_id, None)
        return recommendation_data
    except requests.RequestException as exc:
        errors[user_id] = extract_api_error_message(exc)
        return cache.get(user_id)


DAILY_COACH_LIMITATION_LABELS = {
    "incomplete_actual_set_logging_limits_inference": (
        "Workout logging is incomplete, so recent training trends are limited."
    ),
    "nutrition_targets_limited_by_logging_quality": (
        "Nutrition guidance is limited because recent logging quality is incomplete."
    ),
}


def daily_coach_limitation_label(limitation: object) -> str | None:
    """Return user-friendly limitation copy for the Daily Coach Synthesis card."""

    if limitation is None:
        return None

    if isinstance(limitation, dict):
        message = limitation.get("message") or limitation.get("label")
        if message:
            return str(message)

        limitation = (
            limitation.get("reason_code")
            or limitation.get("code")
            or limitation.get("name")
            or limitation
        )

    limitation_code = str(limitation).strip()
    if not limitation_code:
        return None

    friendly_label = DAILY_COACH_LIMITATION_LABELS.get(limitation_code)
    if friendly_label:
        return friendly_label

    return f"{limitation_code.replace('_', ' ').capitalize()}."


def friendly_daily_coach_limitations(limitations: list[object]) -> list[str]:
    """Translate raw limitation/reason-code style values for normal UI."""

    friendly_values = []

    for limitation in limitations:
        friendly_label = daily_coach_limitation_label(limitation)
        if friendly_label and friendly_label not in friendly_values:
            friendly_values.append(friendly_label)

    return friendly_values


def render_daily_coach_synthesis_card(user_id: int) -> None:
    st.subheader("Coach’s Read for Today")
    st.caption(
        "A concise synthesis of today’s recovery, training, workout, and logging context."
    )

    synthesis_response = None
    synthesis_error = None

    try:
        synthesis_response = api_get(f"/daily-coach/{user_id}/synthesis")
    except requests.RequestException as exc:
        synthesis_error = extract_api_error_message(exc)

    if synthesis_error:
        st.info("Coach synthesis is not available yet.")
        if st.session_state.get("developer_mode", False):
            with st.expander("Developer details: daily coach synthesis error"):
                st.write(synthesis_error)
        return

    if not synthesis_response or not synthesis_response.get("success"):
        st.info("Coach synthesis is not available yet.")
        developer_details(
            "Developer details: daily coach synthesis response",
            synthesis_response or {},
        )
        return

    synthesis = synthesis_response.get("daily_coach_synthesis") or {}
    if not synthesis:
        st.info("Coach synthesis is not available yet.")
        developer_details(
            "Developer details: daily coach synthesis response",
            synthesis_response,
        )
        return

    today_summary = synthesis.get("today_summary")
    recommended_focus = synthesis.get("recommended_focus")
    workout_guidance = synthesis.get("workout_guidance")
    confidence = synthesis.get("confidence") or synthesis_response.get("confidence")
    limitations = synthesis.get("limitations") or []

    top_col, confidence_col = st.columns([4, 1])
    with top_col:
        if today_summary:
            st.write(today_summary)
        else:
            st.info("No coach summary is available yet.")
    with confidence_col:
        st.metric("Confidence", confidence or "Unknown")

    if recommended_focus:
        st.info(f"**Recommended focus:** {recommended_focus}")

    if workout_guidance:
        st.write(f"**Workout guidance:** {workout_guidance}")

    with st.expander("More coaching context", expanded=False):
        detail_rows = [
            ("Recovery signal", synthesis.get("recovery_signal")),
            ("Training signal", synthesis.get("training_signal")),
            ("Execution context", synthesis.get("execution_context")),
            ("Logging focus", synthesis.get("logging_focus")),
            ("Plan fit note", synthesis.get("plan_fit_note")),
        ]

        for label, value in detail_rows:
            if value:
                st.write(f"**{label}:** {value}")

        friendly_limitations = friendly_daily_coach_limitations(limitations)
        if friendly_limitations:
            st.write("**Current limits on the read:**")
            for limitation in friendly_limitations:
                st.write(f"- {limitation}")

    developer_details(
        "Developer details: daily coach synthesis response",
        synthesis_response,
    )


def render_daily_recommendation_snapshot(user_id: int) -> None:
    st.subheader("Daily Coaching")

    recommendation_data = get_daily_recommendation_for_user(user_id)
    recommendation_error = st.session_state.daily_recommendation_error_by_user.get(
        user_id
    )

    if recommendation_error and recommendation_data:
        st.warning(
            "Could not refresh today’s recommendation. Showing the last loaded "
            "recommendation for this user."
        )
    elif recommendation_error:
        st.error(f"Failed to load daily recommendation: {recommendation_error}")
        return

    if not recommendation_data or not recommendation_data.get("success"):
        st.info("No daily recommendation is available for this user yet.")
        return

    scenario = recommendation_data.get("scenario")
    confidence = recommendation_data.get("confidence", "Unknown")
    approved_plan = recommendation_data.get("approved_action_plan", {})
    training_constraints = recommendation_data.get("training_constraints", {})

    col1, col2 = st.columns(2)
    col1.metric("Status", scenario_display_name(scenario))
    col2.metric("Confidence", confidence)

    st.write(
        approved_plan.get(
            "daily_coaching_recommendation",
            "No daily coaching recommendation available.",
        )
    )

    with st.expander("Why this recommendation", expanded=False):
        st.write("**Workout:**")
        st.write(
            approved_plan.get(
                "workout_recommendation",
                "No workout recommendation available.",
            )
        )
        st.write("**Nutrition:**")
        st.write(
            approved_plan.get(
                "nutrition_action",
                "No nutrition action available.",
            )
        )
        st.write("**Why:**")
        st.write(approved_plan.get("rationale", "No rationale available."))
        display_training_constraints(training_constraints)

    developer_details("Developer details: daily recommendation", recommendation_data)


def render_today_workout_panel(user_id: int) -> None:
    st.subheader("Today’s Workout")
    st.caption(
        "Review the plan, start when ready, log sets, complete the workout, "
        "then review what happened."
    )

    active_plan_response = get_active_plan_response(user_id)

    if active_plan_response:
        plan_instance_id = get_plan_instance_id_from_response(active_plan_response)

        render_active_plan_summary(active_plan_response)

        if plan_instance_id is None:
            st.warning("The active workout is missing a plan instance ID.")
            return

        plan_status, execution_status = get_plan_statuses(active_plan_response)

        if plan_status == "selected" or execution_status == "selected":
            st.caption(
                "Workout selected. Start here when ready, or use the Workout tab if you need substitutions first."
            )
            start_active_workout(active_plan_response, context_key="today")

        refreshed_plan_response = refresh_active_plan_response(plan_instance_id)
        if refreshed_plan_response:
            active_plan_response = refreshed_plan_response

        if is_started_or_in_progress(active_plan_response):
            st.divider()
            st.markdown("### Log Sets")
            display_actual_set_logging(plan_instance_id, context_key="today")

        refreshed_plan_response = refresh_active_plan_response(plan_instance_id)
        if refreshed_plan_response:
            active_plan_response = refreshed_plan_response

        if is_in_progress(active_plan_response):
            st.divider()
            st.markdown("### Complete Workout")
            display_complete_workout_control(plan_instance_id, context_key="today")

        completed_response = st.session_state.get("completed_workout_plan_response")
        if completed_response:
            st.divider()
            st.markdown("### Result")
            display_planned_vs_actual_summary(
                completed_response.get("planned_vs_actual_summary", {})
            )
        elif get_plan_statuses(active_plan_response)[0] == "completed":
            st.divider()
            st.markdown("### Result")
            try:
                summary_response = api_get(
                    f"/workout-plans/{plan_instance_id}/planned-vs-actual"
                )
            except requests.RequestException as exc:
                st.info(
                    "Workout is completed, but the summary could not be loaded: "
                    f"{extract_api_error_message(exc)}"
                )
            else:
                display_planned_vs_actual_summary(
                    summary_response.get("planned_vs_actual_summary", {}),
                    planned_exercises=summary_response.get("planned_exercises", []),
                    actual_sets=summary_response.get("actual_sets", []),
                )
                developer_details(
                    "Developer details: completed planned-vs-actual summary",
                    summary_response,
                )

        return

    try:
        workout_plan_data = api_get(f"/workout-plans/preview/{user_id}")
    except requests.RequestException as exc:
        st.error(f"Failed to load workout preview: {extract_api_error_message(exc)}")
        return

    if not workout_plan_data.get("success"):
        st.info("No workout plan preview is available for this user yet.")
        return

    approved_workout_plan = workout_plan_data.get("approved_workout_plan", {})

    col1, col2, col3 = st.columns(3)
    col1.metric("Workout", approved_workout_plan.get("title", "Workout Plan"))
    col2.metric(
        "Duration", f"{approved_workout_plan.get('duration_minutes', 'Unknown')} min"
    )
    col3.metric("Confidence", workout_plan_data.get("confidence", "Unknown"))

    st.write(f"**Focus:** {approved_workout_plan.get('session_focus', 'Unknown')}")
    display_workout_plan_explanation(user_id)
    render_preview_exercise_snapshot(approved_workout_plan)

    select_today_workout(user_id, "select_today_workout_button")

    with st.expander("Plan rationale and guidance", expanded=False):
        if approved_workout_plan.get("rationale"):
            st.write(f"**Why:** {approved_workout_plan.get('rationale')}")
        if approved_workout_plan.get("progression_guidance"):
            st.write(
                f"**Progression:** {approved_workout_plan.get('progression_guidance')}"
            )
        if approved_workout_plan.get("warmup"):
            st.write(f"**Warmup:** {approved_workout_plan.get('warmup')}")
        if approved_workout_plan.get("cooldown"):
            st.write(f"**Cooldown:** {approved_workout_plan.get('cooldown')}")

    developer_details("Developer details: workout preview", workout_plan_data)


def render_recovery_checkin_card(user_id: int) -> None:
    st.subheader("Recovery Check-In")
    st.caption(
        "Quick check-in: improves today's workout and nutrition guidance without "
        "changing anything until you save it."
    )

    with st.expander("Complete recovery check-in", expanded=False):
        with st.form("today_recovery_checkin_form"):
            body_weight = st.number_input(
                "Body Weight",
                min_value=0.0,
                value=200.0,
                step=0.5,
                key="today_recovery_body_weight",
            )
            sleep_hours = st.number_input(
                "Sleep Hours",
                min_value=0.0,
                max_value=24.0,
                value=7.0,
                step=0.5,
                key="today_recovery_sleep_hours",
            )
            energy_level = st.slider(
                "Energy Level",
                min_value=1,
                max_value=10,
                value=6,
                key="today_recovery_energy",
            )
            soreness_level = st.slider(
                "Soreness Level",
                min_value=1,
                max_value=10,
                value=4,
                key="today_recovery_soreness",
            )
            mood = st.text_input(
                "Mood",
                value="Okay",
                key="today_recovery_mood",
            )
            notes = st.text_area(
                "Recovery Notes",
                key="today_recovery_notes",
            )
            recovery_submitted = st.form_submit_button("Save Recovery Check-In")

        if recovery_submitted:
            payload = {
                "user_id": user_id,
                "body_weight": body_weight,
                "sleep_hours": sleep_hours,
                "energy_level": energy_level,
                "soreness_level": soreness_level,
                "mood": mood,
                "notes": notes,
            }
            try:
                data = api_post("/recovery/checkins", payload)
            except requests.RequestException as exc:
                st.error(f"Recovery check-in failed: {extract_api_error_message(exc)}")
            else:
                if data.get("success", True):
                    st.success("Recovery check-in saved.")
                else:
                    st.error(data.get("message", "Recovery check-in failed."))


def render_quick_nutrition_status(user_id: int) -> None:
    st.subheader("Nutrition Today")
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        data = api_get(f"/nutrition/{user_id}/{today}")
    except requests.RequestException as exc:
        st.error(f"Failed to load nutrition: {extract_api_error_message(exc)}")
        return

    nutrition = data.get("nutrition") or {}
    if not nutrition:
        st.caption(
            "No food logged today yet. Use the Nutrition tab when you are ready."
        )
        return

    preferred_names = ["Energy", "Calories", "Protein", "Carbohydrate", "Fat"]
    rows = []
    for nutrient_name, nutrient_data in nutrition.items():
        if any(name.lower() in nutrient_name.lower() for name in preferred_names):
            rows.append(
                {
                    "Nutrient": nutrient_name,
                    "Amount": nutrient_data.get("amount"),
                    "Unit": nutrient_data.get("unit"),
                }
            )

    if not rows:
        st.caption(f"{len(nutrition)} nutrition fields logged today.")
        return

    st.dataframe(pd.DataFrame(rows[:6]), width="stretch", hide_index=True)


def latest_completed_workout_history_item(user_id: int) -> dict | None:
    try:
        history_response = api_get(f"/workout-plans/history/{user_id}")
    except requests.RequestException:
        return None

    for history_item in history_response.get("workout_plan_instances", []):
        workout_plan_instance = history_item.get("workout_plan_instance") or {}
        execution_session = history_item.get("execution_session") or {}

        if (
            workout_plan_instance.get("status") == "completed"
            or execution_session.get("status") == "completed"
        ):
            return history_item

    return None


def render_recent_workout_reflection_card(user_id: int) -> None:
    st.subheader("Recent Workout Reflection")

    history_item = latest_completed_workout_history_item(user_id)
    if not history_item:
        st.info("Complete a planned workout to see a short reflection here.")
        return

    workout_plan_instance = history_item.get("workout_plan_instance") or {}
    execution_session = history_item.get("execution_session") or {}
    summary = history_item.get("planned_vs_actual_summary") or {}
    title = history_item.get("approved_workout_title") or workout_plan_instance.get(
        "title",
        "Completed workout",
    )

    st.write(f"**Latest completed:** {title}")

    if summary:
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Completion",
            format_summary_metric(summary.get("completion_percentage"), "%"),
        )
        col2.metric(
            "Sets",
            f"{compact_count(summary.get('completed_set_count'))}/"
            f"{compact_count(summary.get('planned_set_count'))}",
        )
        col3.metric(
            "Effort",
            format_signed_delta(summary.get("rir_deviation"), " RIR"),
        )
    else:
        st.caption(
            "Review details will appear when planned-vs-actual data is available."
        )

    execution_id = execution_session.get("id")
    if execution_id is not None:
        with st.expander("Post-workout review", expanded=False):
            display_post_workout_review_summary(
                int(execution_id),
                context_key=f"today_recent_{workout_plan_instance.get('id', 'unknown')}",
            )


def render_today_section(user_id: int) -> None:
    st.header("Today")
    st.caption(
        "Start here: review the coach's read, check in, and run today's workout."
    )

    render_daily_coach_synthesis_card(user_id)

    with st.expander("Daily Grounded Recommendation", expanded=False):
        render_daily_recommendation_snapshot(user_id)

    st.divider()

    recovery_col, nutrition_col = st.columns([1, 1])
    with recovery_col:
        render_recovery_checkin_card(user_id)
    with nutrition_col:
        render_quick_nutrition_status(user_id)
        st.divider()
        render_recent_workout_reflection_card(user_id)

    st.divider()

    render_today_workout_panel(user_id)

    with st.expander("Readiness details", expanded=False):
        render_readiness_snapshot(user_id)


def render_workout_plan_section(user_id: int) -> None:
    st.header("Workout")
    st.caption(
        "Plan, customize, start, log, complete, and review the workout from one place."
    )

    if st.session_state.workout_plan_action_error:
        st.error(st.session_state.workout_plan_action_error)

    workout_steps = ["1. Plan", "2. Do Workout", "3. Review"]
    workout_step_display_labels = {
        "1. Plan": "Plan",
        "2. Do Workout": "Active Workout",
        "3. Review": "Review",
    }

    override_step = st.session_state.get("workout_flow_step_override")
    if override_step in workout_steps:
        st.session_state.workout_flow_step = override_step
        st.session_state.workout_flow_step_override = None

    current_step = st.session_state.get("workout_flow_step", "1. Plan")
    if current_step not in workout_steps:
        current_step = "1. Plan"
        st.session_state.workout_flow_step = current_step

    selected_step = st.radio(
        "Workout area",
        options=workout_steps,
        index=workout_steps.index(current_step),
        horizontal=True,
        format_func=lambda step: workout_step_display_labels.get(step, step),
    )

    if selected_step != current_step:
        st.session_state.workout_flow_step = selected_step

    if selected_step == "1. Plan":
        with st.expander("Equipment Profile", expanded=False):
            render_equipment_profile_editor(user_id)

        st.subheader("Workout Preview")
        try:
            workout_plan_data = api_get(f"/workout-plans/preview/{user_id}")
        except requests.RequestException as exc:
            st.error(
                f"Failed to load workout plan preview: {extract_api_error_message(exc)}"
            )
            return

        if workout_plan_data.get("success"):
            scenario = workout_plan_data.get("scenario")
            confidence = workout_plan_data.get("confidence", "Unknown")
            approved_workout_plan = workout_plan_data.get("approved_workout_plan", {})

            col1, col2 = st.columns(2)
            col1.metric("Plan Context", scenario_display_name(scenario))
            col2.metric("Confidence", confidence)

            display_workout_plan_preview(approved_workout_plan, user_id=user_id)

            active_plan_response = get_active_plan_response(user_id)
            if active_plan_response:
                st.success("Selected workout plan is ready to customize.")
                render_active_plan_summary(active_plan_response)

                plan_instance_id = get_plan_instance_id_from_response(
                    active_plan_response
                )
                if plan_instance_id is not None:
                    workout_plan_instance = (
                        active_plan_response.get("workout_plan_instance") or {}
                    )
                    execution_session = (
                        active_plan_response.get("execution_session") or {}
                    )
                    planned_exercises = (
                        active_plan_response.get("planned_exercises") or []
                    )
                    active_substitutions = merged_active_substitution_map(
                        plan_instance_id,
                        active_plan_response,
                    )

                    st.divider()
                    with st.expander(
                        "Need a substitution?",
                        expanded=bool(active_substitutions),
                    ):
                        st.caption(
                            "Optional: choose a compatible replacement before you start. "
                            "After you apply one, the active workout plan updates automatically "
                            "and the Do Workout step uses the substituted exercise for logging."
                        )
                        display_substitution_candidates(
                            plan_instance_id,
                            planned_exercises,
                            context_key="plan_step",
                            plan_status=workout_plan_instance.get("status"),
                            execution_status=execution_session.get("status"),
                            active_substitutions=active_substitutions,
                            always_visible=False,
                            title="Compatible Substitutions",
                        )

                    refreshed_plan_response = refresh_active_plan_response(
                        plan_instance_id
                    )
                    if refreshed_plan_response:
                        active_plan_response = refreshed_plan_response
                        active_substitutions = merged_active_substitution_map(
                            plan_instance_id,
                            active_plan_response,
                        )

                    if active_substitutions:
                        st.success(
                            "Workout plan updated with active substitutions. "
                            "The Do Workout step is populated with the active exercise choices."
                        )
                    else:
                        st.info(
                            "No substitutions are active yet. Keep the original plan or "
                            "apply a compatible substitution before moving to Do Workout."
                        )

                    if st.button(
                        "Continue to Do Workout",
                        key=f"continue_to_do_workout_{plan_instance_id}",
                        type="primary",
                    ):
                        request_workout_flow_step("2. Do Workout")
                        st.rerun()
            else:
                select_today_workout(user_id, "select_workout_plan_button")

            if st.session_state.get("developer_mode", False):
                with st.expander(
                    "Developer details: workout plan preview/select/start"
                ):
                    st.subheader("Training Constraints")
                    st.json(workout_plan_data.get("training_constraints", {}))
                    st.subheader("Workout Constraints")
                    st.json(workout_plan_data.get("workout_constraints", {}))
                    st.subheader("Raw Workout Plan Preview Response")
                    st.json(workout_plan_data)

        else:
            st.warning("No workout plan preview is available for this user yet.")

    elif selected_step == "2. Do Workout":
        active_plan_response = get_active_plan_response(user_id)
        render_active_plan_summary(active_plan_response)

        if active_plan_response:
            plan_instance_id = get_plan_instance_id_from_response(active_plan_response)
            if plan_instance_id is None:
                st.warning("The active plan is missing a plan instance ID.")
            else:
                start_active_workout(active_plan_response, context_key="workout")

                refreshed_plan_response = refresh_active_plan_response(plan_instance_id)
                if refreshed_plan_response:
                    active_plan_response = refreshed_plan_response

                if is_started_or_in_progress(active_plan_response):
                    st.divider()
                    display_actual_set_logging(plan_instance_id, context_key="workout")

                if is_in_progress(active_plan_response):
                    st.divider()
                    display_complete_workout_control(
                        plan_instance_id, context_key="workout"
                    )
        else:
            st.info("Select a workout plan before starting the workout.")

    elif selected_step == "3. Review":
        active_plan_response = get_active_plan_response(user_id)
        plan_instance_id = get_plan_instance_id_from_response(active_plan_response)

        if plan_instance_id is None:
            st.info("Select or start a workout plan to review execution details.")
        else:
            display_workout_execution_review(plan_instance_id)

    st.divider()
    with st.expander("Workout History", expanded=False):
        display_workout_execution_history(
            user_id,
            context_scope="workout_history",
        )

    with st.expander("Exercise Catalog", expanded=False):
        display_exercise_catalog(user_id)

    with st.expander("Manual Workout Logger", expanded=False):
        render_manual_workout_logger(user_id)


def nutrition_public_text(value: object) -> str:
    """Convert public-safe nutrition text/code values into friendly UI copy."""
    if value is None or value == "":
        return ""

    if isinstance(value, dict):
        for key in ("message", "label", "description", "text", "code"):
            if value.get(key):
                return nutrition_public_text(value.get(key))
        return humanize_label(str(value))

    text_value = str(value).strip()
    if not text_value:
        return ""

    limitation_labels = {
        "no_logs": "No nutrition logs are available for this date yet.",
        "no_nutrition_logs": "No nutrition logs are available for this date yet.",
        "nutrition_logs_missing": "No nutrition logs are available for this date yet.",
        "partial_day_logging": "Nutrition logging may only cover part of the day.",
        "likely_incomplete_logging": "Nutrition logging may be incomplete for this date.",
        "incomplete_logging": "Nutrition logging may be incomplete for this date.",
        "nutrition_targets_limited_by_logging_quality": (
            "Nutrition guidance is limited because recent logging quality is incomplete."
        ),
        "calorie_targets_limited_by_logging_quality": (
            "Calorie comparison is limited until logging quality improves."
        ),
        "protein_targets_limited_by_logging_quality": (
            "Protein comparison is limited until logging quality improves."
        ),
        "missing_calorie_actual": "Logged calories are not available for this date.",
        "missing_protein_actual": "Logged protein is not available for this date.",
        "missing_carbohydrate_actual": "Logged carbohydrate is not available for this date.",
        "missing_fat_actual": "Logged fat is not available for this date.",
        "target_not_approved": "This target comparison is not approved for display yet.",
        "calorie_target_not_approved": "Calorie targets are not approved for display yet.",
        "protein_target_not_approved": "Protein targets are not approved for display yet.",
        "carbohydrate_target_not_approved": (
            "Carbohydrate targets are not approved for display yet."
        ),
        "fat_target_not_approved": "Fat targets are not approved for display yet.",
    }

    if text_value in limitation_labels:
        return limitation_labels[text_value]

    return humanize_label(text_value).rstrip(".") + "."


def nutrition_amount_parts(value: object) -> tuple[object, str | None]:
    if isinstance(value, dict):
        amount = (
            value.get("amount")
            if value.get("amount") is not None
            else (
                value.get("value")
                if value.get("value") is not None
                else (
                    value.get("actual")
                    if value.get("actual") is not None
                    else value.get("total")
                )
            )
        )
        unit = value.get("unit") or value.get("units")
        return amount, unit

    return value, None


def format_nutrition_value(value: object, default_unit: str | None = None) -> str:
    amount, unit = nutrition_amount_parts(value)
    unit = unit or default_unit

    if amount is None or amount == "":
        return "Not available"

    if isinstance(amount, float):
        amount = round(amount, 1)
        if amount.is_integer():
            amount = int(amount)

    return f"{amount} {unit}".strip() if unit else str(amount)


def first_present_value(source: dict, keys: list[str]) -> object | None:
    for key in keys:
        if key in source and source.get(key) is not None:
            return source.get(key)

    return None


def nutrition_metric_value(source: dict, candidate_keys: list[str]) -> object | None:
    if not source:
        return None

    direct_value = first_present_value(source, candidate_keys)
    if direct_value is not None:
        return direct_value

    for key, value in source.items():
        normalized_key = str(key).lower().replace(" ", "_")
        if normalized_key in candidate_keys:
            return value

    return None


def target_comparison_value(comparison: dict, keys: list[str]) -> object | None:
    value = first_present_value(comparison, keys)
    if value is not None:
        return value

    target_min = comparison.get("target_min")
    target_max = comparison.get("target_max")

    if target_min is not None and target_max is not None:
        return (
            f"{format_nutrition_value(target_min)}–{format_nutrition_value(target_max)}"
        )

    return None


def macro_comparison_from_summary(
    summary: dict, candidate_keys: list[str]
) -> dict | None:
    for key in candidate_keys:
        value = summary.get(key)
        if isinstance(value, dict):
            return value

    comparisons = summary.get("comparisons")
    if isinstance(comparisons, list):
        for comparison in comparisons:
            if not isinstance(comparison, dict):
                continue
            name = str(
                comparison.get("nutrient")
                or comparison.get("macro")
                or comparison.get("target")
                or comparison.get("name")
                or ""
            ).lower()
            if any(candidate in name for candidate in candidate_keys):
                return comparison

    return None


def comparison_is_displayable(comparison: dict) -> bool:
    display_flags = [
        "approved",
        "allow_display",
        "display_allowed",
        "comparison_available",
        "target_available",
        "target_approved",
    ]

    for flag in display_flags:
        if flag in comparison:
            return bool(comparison.get(flag))

    status = str(comparison.get("status") or comparison.get("confidence") or "").lower()
    if status in {"blocked", "limited", "not_available", "unavailable"}:
        return False

    return True


def display_nutrition_actuals(actuals: dict, logging_summary: dict) -> None:
    st.markdown("#### Logged Actuals")

    if not actuals:
        st.caption(
            "No nutrition logs found for this date yet. Logging meals will improve "
            "nutrition guidance."
        )
        return

    metric_specs = [
        (
            "Calories",
            [
                "calories",
                "calorie_actual",
                "total_calories",
                "energy",
                "energy_kcal",
                "kcal",
            ],
            "kcal",
        ),
        ("Protein", ["protein", "protein_g", "protein_grams", "total_protein_g"], "g"),
        (
            "Carbs",
            [
                "carbs",
                "carbohydrates",
                "carbohydrate",
                "carbohydrate_g",
                "carbohydrate_grams",
                "total_carbohydrate_g",
            ],
            "g",
        ),
        ("Fat", ["fat", "fat_g", "fat_grams", "total_fat_g"], "g"),
    ]

    cols = st.columns(4)
    for column, (label, keys, unit) in zip(cols, metric_specs, strict=False):
        column.metric(
            label, format_nutrition_value(nutrition_metric_value(actuals, keys), unit)
        )

    entry_count = first_present_value(
        logging_summary,
        ["entry_count", "food_entry_count", "logged_entry_count", "entries_logged"],
    )
    meal_count = first_present_value(
        logging_summary,
        ["meal_count", "logged_meal_count", "meals_logged"],
    )

    caption_parts = []
    if meal_count is not None:
        caption_parts.append(f"{meal_count} meals")
    if entry_count is not None:
        caption_parts.append(f"{entry_count} entries")

    if caption_parts:
        st.caption("Logged today: " + " / ".join(caption_parts))


def nutrition_comparison_rows_from_summary(summary: dict) -> list[dict]:
    if not summary:
        return []

    macro_specs = [
        ("Calories", ["calories", "calorie", "energy", "kcal"], "kcal"),
        ("Protein", ["protein", "protein_g", "protein_grams"], "g"),
        (
            "Carbs",
            [
                "carbs",
                "carbohydrate",
                "carbohydrates",
                "carbohydrate_g",
                "carbohydrate_grams",
            ],
            "g",
        ),
        ("Fat", ["fat", "fat_g", "fat_grams"], "g"),
    ]

    rows = []
    for label, keys, unit in macro_specs:
        comparison = macro_comparison_from_summary(summary, keys)
        if not comparison:
            continue

        actual = target_comparison_value(
            comparison,
            ["actual", "actual_amount", "actual_value", "logged", "logged_amount"],
        )

        if comparison_is_displayable(comparison):
            target = target_comparison_value(
                comparison,
                ["target", "target_amount", "target_value", "range", "approved_target"],
            )
            delta = target_comparison_value(
                comparison,
                ["delta", "difference", "variance", "remaining"],
            )
            status = (
                comparison.get("status") or comparison.get("guidance") or "Available"
            )
        else:
            target = None
            delta = None
            status = (
                comparison.get("limitation")
                or comparison.get("reason")
                or comparison.get("reason_code")
                or "target_not_approved"
            )

        status_text = nutrition_public_text(status)
        if not status_text:
            status_text = "Comparison is limited for this date."

        rows.append(
            {
                "Nutrient": label,
                "Logged": format_nutrition_value(actual, unit),
                "Target": (
                    format_nutrition_value(target, unit)
                    if target is not None
                    else "Limited"
                ),
                "Difference": (
                    format_nutrition_value(delta, unit)
                    if delta is not None
                    else "Limited"
                ),
                "Status": status_text,
            }
        )

    return rows


def display_target_vs_actual_table(summary: dict) -> None:
    st.markdown("#### Target vs Actual")

    rows = nutrition_comparison_rows_from_summary(summary)
    if not rows:
        st.caption(
            "Target comparisons are limited for this date. Keep logging meals to improve "
            "nutrition guidance."
        )
        return

    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    limited_rows = [row for row in rows if row.get("Target") == "Limited"]
    if limited_rows:
        st.caption(
            "Some comparisons are limited because the backend did not approve those "
            "targets for display with the current logging context."
        )


def display_approved_nutrition_guidance(guidance: object) -> None:
    if not guidance:
        st.caption("No approved nutrition guidance is available for this date yet.")
        return

    if isinstance(guidance, str):
        st.write(guidance)
        return

    if not isinstance(guidance, dict):
        st.write(str(guidance))
        return

    preferred_keys = [
        "summary",
        "guidance",
        "nutrition_guidance",
        "calorie_guidance",
        "protein_guidance",
        "carbohydrate_guidance",
        "fat_guidance",
        "logging_guidance",
        "next_step",
    ]

    shown = False
    for key in preferred_keys:
        value = guidance.get(key)
        if value:
            st.write(f"**{humanize_label(key)}:** {value}")
            shown = True

    if not shown:
        for key, value in guidance.items():
            if value and key not in {"reason_codes", "runtime_metadata", "debug"}:
                st.write(f"**{humanize_label(key)}:** {value}")


def display_logging_quality(
    logging_summary: dict,
    logging_completeness: object,
    limitations: list,
) -> None:
    st.markdown("#### Logging Quality")

    quality_value = (
        logging_completeness
        or logging_summary.get("logging_quality")
        or logging_summary.get("status")
        or logging_summary.get("completeness")
    )

    if quality_value:
        st.caption(f"Logging completeness: {nutrition_public_text(quality_value)}")
    else:
        st.caption("Logging completeness is not available yet.")

    missing_fields = logging_summary.get(
        "missing_nutrient_fields"
    ) or logging_summary.get("missing_fields")
    if missing_fields:
        friendly_fields = ", ".join(
            humanize_label(str(field)) for field in missing_fields
        )
        st.caption(f"Missing fields: {friendly_fields}")

    if limitations:
        st.markdown("#### Limitations")
        for limitation in limitations:
            friendly = nutrition_public_text(limitation)
            if friendly:
                st.caption(f"• {friendly}")


FORMULA_TARGET_DISPLAY_SPECS = [
    {
        "label": "Calories",
        "target_key": "calorie_target",
        "flag_key": "allow_calorie_targets",
        "unit": "kcal/day",
    },
    {
        "label": "Protein",
        "target_key": "protein_target_g",
        "flag_key": "allow_protein_targets",
        "unit": "g/day",
    },
    {
        "label": "Carbohydrates",
        "target_key": "carbohydrate_target_g",
        "flag_key": "allow_carbohydrate_targets",
        "unit": "g/day",
    },
    {
        "label": "Fat",
        "target_key": "fat_target_g",
        "flag_key": "allow_fat_targets",
        "unit": "g/day",
    },
]

FORMULA_LIMITATION_LABELS = {
    "missing_body_weight": "A current body weight is needed before this target can be shown.",
    "body_weight_missing": "A current body weight is needed before this target can be shown.",
    "protein_requires_body_weight": "Protein targets require a current body weight.",
    "missing_height": "Height is needed before calorie targets can be shown.",
    "height_missing": "Height is needed before calorie targets can be shown.",
    "missing_age": "Age is needed before calorie targets can be shown.",
    "age_missing": "Age is needed before calorie targets can be shown.",
    "missing_sex": "Sex is needed before calorie targets can be shown.",
    "sex_missing": "Sex is needed before calorie targets can be shown.",
    "missing_activity_level": "Activity level is needed before calorie targets can be shown.",
    "activity_level_missing": "Activity level is needed before calorie targets can be shown.",
    "missing_primary_goal": "A primary goal is needed before calorie targets can be shown.",
    "primary_goal_missing": "A primary goal is needed before calorie targets can be shown.",
    "calorie_formula_inputs_missing": "Calories are not shown yet because key profile inputs are missing.",
    "calorie_targets_limited_by_profile_inputs": "Calories are not shown yet because key profile inputs are missing.",
    "calorie_target_not_approved": "Calories are not approved for display yet.",
    "carbohydrate_requires_calorie_target": "Carbohydrate targets depend on an approved calorie target.",
    "carbohydrate_target_not_approved": "Carbohydrate targets are not approved for display yet.",
    "fat_requires_calorie_target": "Fat targets depend on an approved calorie target.",
    "fat_target_not_approved": "Fat targets are not approved for display yet.",
    "target_not_approved": "This target is not approved for display yet.",
    "nutrition_targets_limited_by_logging_quality": "Nutrition guidance is limited because recent logging quality is incomplete.",
    "limited_confidence": "Target confidence is limited with the current profile and logging context.",
}


def formula_public_text(value: object) -> str:
    """Humanize public-safe nutrition formula reason/limitation values."""

    if value is None or value == "":
        return ""

    if isinstance(value, dict):
        for key in (
            "message",
            "label",
            "description",
            "text",
            "reason",
            "reason_code",
            "code",
        ):
            if value.get(key):
                return formula_public_text(value.get(key))
        return humanize_label(str(value))

    text_value = str(value).strip()
    if not text_value:
        return ""

    if text_value in FORMULA_LIMITATION_LABELS:
        return FORMULA_LIMITATION_LABELS[text_value]

    return humanize_label(text_value).rstrip(".") + "."


def selected_nutrition_summary_date_text(user_id: int) -> str:
    selected_date = st.session_state.get(f"nutrition_target_vs_actual_date_{user_id}")
    if hasattr(selected_date, "isoformat"):
        return selected_date.isoformat()
    if selected_date:
        return str(selected_date)
    return datetime.now().date().isoformat()


def formula_target_value(target: dict | None, default_unit: str) -> str | None:
    if not target or not target.get("display_allowed"):
        return None

    display_value = target.get("display_value")
    if display_value:
        return str(display_value)

    unit = target.get("unit") or default_unit
    value = target.get("value")
    if value is not None:
        return format_nutrition_value(value, unit)

    min_value = target.get("min_value")
    max_value = target.get("max_value")
    if min_value is not None and max_value is not None:
        return f"{format_nutrition_value(min_value, unit)}–{format_nutrition_value(max_value, unit)}"

    return None


def formula_target_is_displayable(
    target: dict | None,
    display_flags: dict,
    flag_key: str,
) -> bool:
    return bool(
        display_flags.get(flag_key)
        and target
        and target.get("display_allowed")
        and formula_target_value(target, target.get("unit") or "")
    )


def formula_target_reasons(
    target: dict | None,
    formula_response: dict,
) -> list[str]:
    raw_reasons = []
    if target:
        raw_reasons.extend(target.get("limitations") or [])
        raw_reasons.extend(target.get("reason_codes") or [])

    raw_reasons.extend(formula_response.get("limitations") or [])
    raw_reasons.extend(formula_response.get("reason_codes") or [])

    friendly_reasons = []
    for reason in raw_reasons:
        friendly = formula_public_text(reason)
        if friendly and friendly not in friendly_reasons:
            friendly_reasons.append(friendly)

    return friendly_reasons


def formula_target_rows(formula_response: dict) -> tuple[list[dict], list[dict]]:
    approved_targets = formula_response.get("approved_macro_targets") or {}
    display_flags = formula_response.get("display_flags") or {}

    approved_rows = []
    limited_rows = []

    for spec in FORMULA_TARGET_DISPLAY_SPECS:
        target = approved_targets.get(spec["target_key"])
        is_displayable = formula_target_is_displayable(
            target,
            display_flags,
            spec["flag_key"],
        )

        if is_displayable:
            approved_rows.append(
                {
                    "Target": spec["label"],
                    "Formula-derived target": formula_target_value(
                        target, spec["unit"]
                    ),
                    "Confidence": target.get("confidence")
                    or formula_response.get("confidence", "Unknown"),
                    "Method": humanize_label(target.get("method")),
                }
            )
            continue

        reasons = formula_target_reasons(target, formula_response)
        limited_rows.append(
            {
                "Target": spec["label"],
                "Display status": "Limited",
                "Why": (
                    reasons[0]
                    if reasons
                    else "This target is not approved for display yet."
                ),
            }
        )

    return approved_rows, limited_rows


def display_formula_transparency_metadata(formula_response: dict) -> None:
    metadata = formula_response.get("formula_metadata") or {}
    formula_name = metadata.get("formula_name") or "Nutrition target formula"
    formula_version = metadata.get("formula_version") or "Unknown"
    confidence = formula_response.get("confidence", "Unknown")

    cols = st.columns(3)
    cols[0].metric("Formula", humanize_label(formula_name))
    cols[1].metric("Version", formula_version)
    cols[2].metric("Confidence", confidence)

    st.caption(
        "Formula targets are coaching estimates, not medical advice. Only approved "
        "display targets are shown in the normal UI."
    )

    with st.expander("Formula transparency", expanded=False):
        target_basis = metadata.get("target_basis")
        if target_basis:
            st.write(f"**Target basis:** {formula_public_text(target_basis)}")

        detail_specs = [
            ("Inputs used", metadata.get("inputs_used") or []),
            ("Assumptions", metadata.get("assumptions") or []),
            ("Rounding rules", metadata.get("rounding_rules") or []),
            ("Formula limitations", metadata.get("limitations") or []),
        ]

        for label, values in detail_specs:
            if not values:
                continue
            st.write(f"**{label}:**")
            for value in values:
                friendly = formula_public_text(value)
                if friendly:
                    st.caption(f"• {friendly}")


def render_nutrition_formula_target_transparency_card(user_id: int) -> None:
    st.subheader("Formula-Derived Targets")
    st.caption(
        "Approved formula targets are shown here. Limited targets stay hidden until "
        "the backend approves them for display."
    )

    target_date = selected_nutrition_summary_date_text(user_id)

    try:
        formula_response = api_get(
            f"/nutrition/{user_id}/targets/formula",
            params={"date": target_date},
        )
    except requests.RequestException as exc:
        st.caption(
            "Formula-derived target transparency is not available yet. "
            f"{extract_api_error_message(exc)}"
        )
        return

    if not formula_response.get("success"):
        st.caption("Formula-derived target transparency is not available yet.")
        developer_details(
            "Developer details: nutrition target formula response",
            formula_response,
        )
        return

    approved_rows, limited_rows = formula_target_rows(formula_response)

    st.markdown("#### Approved Targets")
    if approved_rows:
        st.dataframe(
            pd.DataFrame(approved_rows),
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption(
            "No formula-derived calorie or macro targets are approved for display yet."
        )

    if limited_rows:
        with st.expander("Why some targets are limited", expanded=False):
            st.dataframe(
                pd.DataFrame(limited_rows),
                width="stretch",
                hide_index=True,
            )
            st.caption(
                "Limited targets are intentionally not shown as numeric goals until "
                "the backend approves them for display."
            )

    display_formula_transparency_metadata(formula_response)

    developer_details(
        "Developer details: nutrition target formula response",
        formula_response,
    )


def render_nutrition_target_vs_actual_card(user_id: int) -> None:
    st.subheader("Nutrition Today Summary")
    st.caption(
        "Review logged nutrition against approved display targets. Comparisons stay "
        "limited when logging is incomplete."
    )

    date_col, confidence_col, logging_col = st.columns([2, 1, 1])
    with date_col:
        selected_date = st.date_input(
            "Summary date",
            value=datetime.now().date(),
            key=f"nutrition_target_vs_actual_date_{user_id}",
            help="Choose the date to review. Today is selected by default.",
        )
    selected_date_text = selected_date.isoformat()

    try:
        nutrition_response = api_get(
            f"/nutrition/{user_id}/target-vs-actual",
            params={"date": selected_date_text},
        )
    except requests.RequestException as exc:
        st.caption(
            "Nutrition target-vs-actual summary is not available yet. "
            f"{extract_api_error_message(exc)}"
        )
        return

    if not nutrition_response.get("success"):
        st.caption("Nutrition target-vs-actual summary is not available yet.")
        developer_details(
            "Developer details: nutrition target-vs-actual response",
            nutrition_response,
        )
        return

    nutrition_actuals = nutrition_response.get("nutrition_actuals") or {}
    logging_summary = nutrition_response.get("logging_summary") or {}
    target_vs_actual_summary = nutrition_response.get("target_vs_actual_summary") or {}
    approved_guidance = nutrition_response.get("approved_nutrition_guidance")
    logging_completeness = nutrition_response.get("logging_completeness")
    confidence = nutrition_response.get("confidence", "Unknown")
    limitations = nutrition_response.get("limitations") or []

    with confidence_col:
        st.metric("Confidence", confidence)
    logging_status_text = (
        nutrition_public_text(logging_completeness)
        if logging_completeness
        else "Unknown"
    )
    logging_status_key = str(logging_completeness or "").strip().lower()

    if (
        logging_status_key
        in {
            "no_logs",
            "no_nutrition_logs",
            "nutrition_logs_missing",
        }
        or "no nutrition logs" in logging_status_text.lower()
    ):
        logging_metric_label = "No logs"
        logging_caption = (
            "Nutrition logs are unavailable for this date. "
            "Logging meals will improve guidance."
        )
    elif "partial" in logging_status_text.lower():
        logging_metric_label = "Partial"
        logging_caption = logging_status_text
    elif "incomplete" in logging_status_text.lower():
        logging_metric_label = "Incomplete"
        logging_caption = logging_status_text
    elif "complete" in logging_status_text.lower():
        logging_metric_label = "Complete"
        logging_caption = logging_status_text
    elif logging_status_text and len(logging_status_text) <= 18:
        logging_metric_label = logging_status_text
        logging_caption = ""
    else:
        logging_metric_label = "Limited"
        logging_caption = logging_status_text

    with logging_col:
        st.metric("Logging", logging_metric_label)

    if logging_caption:
        st.caption(logging_caption)

    st.markdown("#### Approved Guidance")
    display_approved_nutrition_guidance(approved_guidance)

    display_nutrition_actuals(nutrition_actuals, logging_summary)

    with st.expander("Target comparisons — approved targets only", expanded=True):
        st.caption(
            "Comparisons are shown only when the backend approves the target for display."
        )
        display_target_vs_actual_table(target_vs_actual_summary)

    with st.expander("Logging quality and limitations", expanded=False):
        display_logging_quality(logging_summary, logging_completeness, limitations)

    developer_details(
        "Developer details: nutrition target-vs-actual response",
        nutrition_response,
    )


def canonical_food_nutrient_summary_text(food: dict) -> str:
    nutrient_summary = food.get("nutrient_summary") or {}
    if not nutrient_summary:
        return "Nutrients unavailable"

    summary_parts = []
    nutrient_specs = [
        ("calories_per_100g", "kcal"),
        ("protein_g_per_100g", "g protein"),
        ("carbohydrate_g_per_100g", "g carbs"),
        ("fat_g_per_100g", "g fat"),
    ]

    for key, label in nutrient_specs:
        value = nutrient_summary.get(key)
        if value is None:
            continue

        if isinstance(value, float):
            value = round(value, 1)
            if value.is_integer():
                value = int(value)

        summary_parts.append(f"{value} {label}")

    if not summary_parts:
        return "Nutrients unavailable"

    return " / ".join(summary_parts) + " per 100g"


def canonical_food_option_label(food: dict) -> str:
    display_name = food.get("display_name") or "Unknown food"
    food_type = humanize_label(food.get("food_type"))
    serving_grams = food.get("default_grams")
    nutrient_summary = canonical_food_nutrient_summary_text(food)

    serving_label = ""
    if serving_grams is not None:
        serving_label = f" · default {serving_grams}g"

    type_label = "" if food_type == "Unknown" else f" · {food_type}"

    return f"{display_name}{type_label}{serving_label} · {nutrient_summary}"


def canonical_food_result_rows(canonical_foods: list[dict]) -> list[dict]:
    rows = []
    for food in canonical_foods:
        rows.append(
            {
                "Food": food.get("display_name", "Unknown food"),
                "Type": humanize_label(food.get("food_type")),
                "Default": (
                    f"{food.get('default_grams')}g"
                    if food.get("default_grams") is not None
                    else "Unknown"
                ),
                "Nutrition": canonical_food_nutrient_summary_text(food),
            }
        )

    return rows


def raw_food_option_label(food: dict) -> str:
    nutrients = food.get("nutrients") or {}
    calories = nutrients.get("Calories") or nutrients.get("Energy") or {}
    protein = nutrients.get("Protein") or {}

    summary_parts = []
    if calories.get("amount") is not None:
        summary_parts.append(f"{calories.get('amount')} {calories.get('unit', 'kcal')}")
    if protein.get("amount") is not None:
        summary_parts.append(
            f"{protein.get('amount')} {protein.get('unit', 'g')} protein"
        )

    suffix = f" · {' / '.join(summary_parts)}" if summary_parts else ""
    return f"{food.get('name', 'Unknown food')}{suffix}"


def canonical_food_search_option_label(food: dict) -> str:
    """User-facing canonical food label. Do not expose backend IDs."""
    display_name = food.get("display_name") or food.get("name") or "Unknown food"
    food_type = food.get("food_type")
    default_unit = food.get("default_unit")
    default_grams = food.get("default_grams")

    details = []
    if food_type:
        details.append(humanize_label(str(food_type)))
    if default_unit and default_grams:
        details.append(f"default {default_grams:g}g {default_unit}")

    if details:
        return f"{display_name} ({'; '.join(details)})"

    return str(display_name)


def raw_food_search_option_label(food: dict) -> str:
    """User-facing fallback food label. Do not expose raw/source IDs."""
    return str(food.get("name") or food.get("display_name") or "Unknown food")


def unique_food_option_label(label: str, existing_labels: set[str]) -> str:
    """Keep selectbox labels unique without exposing IDs."""
    if label not in existing_labels:
        existing_labels.add(label)
        return label

    suffix = 2
    candidate = f"{label} ({suffix})"
    while candidate in existing_labels:
        suffix += 1
        candidate = f"{label} ({suffix})"

    existing_labels.add(candidate)
    return candidate


def render_nutrition_section(user_id: int) -> None:
    st.header("Nutrition")
    st.caption(
        "Fast path: search clean foods, log grams, then review today’s guidance "
        "and target comparison."
    )

    st.subheader("Log Food")
    st.caption(
        "Canonical foods are searched first. Existing raw/source foods remain "
        "available as a fallback."
    )

    canonical_results_key = "canonical_food_search_results"
    canonical_response_key = "canonical_food_search_response"
    canonical_error_key = "canonical_food_search_error"
    raw_fallback_query_key = "raw_food_fallback_query"

    with st.form("nutrition_canonical_food_search_form"):
        food_query = st.text_input(
            "Food search",
            value="",
            key="nutrition_canonical_food_query",
            placeholder="Example: chicken breast, rice, egg, oats",
        )
        search_food = st.form_submit_button("Search Clean Foods", type="primary")

    if search_food:
        query = food_query.strip()
        st.session_state[canonical_results_key] = []
        st.session_state[canonical_response_key] = {}
        st.session_state[canonical_error_key] = None
        st.session_state.food_search_results = []
        st.session_state[raw_fallback_query_key] = query

        if len(query) < 2:
            st.caption("Enter at least two characters to search clean foods.")
        else:
            try:
                canonical_response = api_get(
                    "/foods/canonical/search",
                    params={"q": query, "limit": 10},
                )
            except requests.RequestException as exc:
                st.session_state[canonical_error_key] = extract_api_error_message(exc)
            else:
                st.session_state[canonical_response_key] = canonical_response
                st.session_state[canonical_results_key] = (
                    canonical_response.get("results") or []
                )

            if not st.session_state.get(canonical_results_key):
                try:
                    fallback_response = api_get(
                        "/foods/search",
                        params={"query": query},
                    )
                except requests.RequestException:
                    st.session_state.food_search_results = []
                else:
                    st.session_state.food_search_results = (
                        fallback_response.get("foods") or []
                    )

    canonical_error = st.session_state.get(canonical_error_key)
    canonical_results = st.session_state.get(canonical_results_key, [])
    canonical_response = st.session_state.get(canonical_response_key, {})

    if canonical_error:
        st.caption(
            "Clean food search is not available right now. "
            "Use the existing food database fallback below."
        )
        if st.session_state.get("developer_mode", False):
            with st.expander("Developer details: canonical food search error"):
                st.write(canonical_error)

    if canonical_results:
        st.markdown("#### Clean food matches")
        result_rows = canonical_food_result_rows(canonical_results)
        if result_rows:
            st.dataframe(
                pd.DataFrame(result_rows),
                width="stretch",
                hide_index=True,
            )

        canonical_options = {
            canonical_food_option_label(food): food
            for food in canonical_results
            if food.get("canonical_food_id") is not None
        }

        if canonical_options:
            with st.form("nutrition_log_canonical_food_form"):
                selected_food_label = st.selectbox(
                    "Selected clean food",
                    list(canonical_options.keys()),
                    key="nutrition_selected_canonical_food",
                )
                selected_food = canonical_options[selected_food_label]
                default_grams = float(selected_food.get("default_grams") or 100.0)
                grams = st.number_input(
                    "Amount in grams",
                    min_value=1.0,
                    value=default_grams,
                    step=5.0,
                    key="nutrition_canonical_grams",
                )
                try:
                    default_entry_date = datetime.fromisoformat(
                        selected_nutrition_summary_date_text(user_id)
                    ).date()
                except ValueError:
                    default_entry_date = datetime.now().date()
                entry_date = st.date_input(
                    "Log date",
                    value=default_entry_date,
                    key=f"nutrition_canonical_log_date_{user_id}",
                    help=(
                        "Defaults to the Nutrition Today Summary date when available."
                    ),
                )
                st.caption(
                    "Nutrition values are estimates from the approved canonical food "
                    "record. Weights are logged in grams for v1."
                )
                log_canonical_food = st.form_submit_button(
                    "Save Clean Food Log",
                    type="primary",
                )

            if log_canonical_food:
                payload = {
                    "canonical_food_id": int(selected_food["canonical_food_id"]),
                    "grams": grams,
                    "entry_date": entry_date.isoformat(),
                }
                try:
                    data = api_post(
                        f"/nutrition/{user_id}/log-canonical",
                        payload,
                    )
                except requests.RequestException as exc:
                    st.error(
                        "Food logging failed: " f"{extract_api_error_message(exc)}"
                    )
                else:
                    if data.get("success", True):
                        food_name = selected_food.get("display_name", "Selected food")
                        st.success(f"Logged {food_name}.")
                        st.session_state[canonical_results_key] = []
                        st.session_state[canonical_response_key] = {}
                        st.session_state[canonical_error_key] = None
                        st.session_state.food_search_results = []
                        st.rerun()
                    else:
                        st.error(data.get("message", "Food logging failed."))

        developer_details(
            "Developer details: canonical food search response",
            canonical_response,
        )
    elif search_food and not canonical_error:
        st.caption("No clean food match found yet. Use existing food database for now.")

    fallback_expanded = bool(
        st.session_state.get("food_search_results")
        or (search_food and not canonical_results)
        or canonical_error
    )

    with st.expander(
        "Advanced: existing food database fallback",
        expanded=fallback_expanded,
    ):
        st.caption(
            "Use this fallback only when a clean canonical food is not available yet. "
            "These results may include noisier source records."
        )

        with st.form("nutrition_raw_food_search_form"):
            fallback_query = st.text_input(
                "Existing food database search",
                value=st.session_state.get(raw_fallback_query_key, ""),
                key="nutrition_raw_food_query",
                placeholder="Example: chicken breast, rice, banana",
            )
            search_raw_food = st.form_submit_button("Search Existing Foods")

        if search_raw_food:
            if not fallback_query.strip():
                st.caption("Enter a food search term to look up existing food records.")
            else:
                st.session_state[raw_fallback_query_key] = fallback_query.strip()
                try:
                    data = api_get(
                        "/foods/search",
                        params={"query": fallback_query.strip()},
                    )
                except requests.RequestException as exc:
                    st.error(
                        "Existing food search failed: "
                        f"{extract_api_error_message(exc)}"
                    )
                else:
                    st.session_state.food_search_results = data.get("foods", [])
                    if not st.session_state.food_search_results:
                        st.caption(
                            "No existing foods found. Try a simpler search term."
                        )

        if st.session_state.food_search_results:
            food_options = {
                raw_food_option_label(food): food
                for food in st.session_state.food_search_results
            }

            with st.form("nutrition_log_raw_food_form"):
                selected_food_label = st.selectbox(
                    "Selected existing food",
                    list(food_options.keys()),
                    key="nutrition_selected_raw_food",
                )
                grams = st.number_input(
                    "Amount in grams",
                    min_value=1.0,
                    value=100.0,
                    step=5.0,
                    key="nutrition_raw_grams",
                )
                st.caption(
                    "Existing food logging uses the legacy food ID returned by "
                    "the existing food database."
                )
                log_food = st.form_submit_button("Save Existing Food Log")

            if log_food:
                selected_food = food_options[selected_food_label]
                payload = {
                    "user_id": user_id,
                    "food_id": selected_food["id"],
                    "grams": grams,
                }
                try:
                    data = api_post("/nutrition/log", payload)
                except requests.RequestException as exc:
                    st.error(
                        "Food logging failed: " f"{extract_api_error_message(exc)}"
                    )
                else:
                    if data.get("success", True):
                        st.success("Food logged successfully.")
                        st.session_state.food_search_results = []
                        st.rerun()
                    else:
                        st.error(data.get("message", "Food logging failed."))

    st.divider()

    render_nutrition_target_vs_actual_card(user_id)

    render_nutrition_formula_target_transparency_card(user_id)

    with st.expander("Logged nutrient details", expanded=False):
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            data = api_get(f"/nutrition/{user_id}/{today}")
        except requests.RequestException as exc:
            st.error(
                f"Failed to load nutrition details: {extract_api_error_message(exc)}"
            )
        else:
            nutrition = data.get("nutrition") or {}
            if nutrition:
                nutrition_rows = [
                    {
                        "Nutrient": nutrient_name,
                        "Amount": nutrient_data["amount"],
                        "Unit": nutrient_data["unit"],
                    }
                    for nutrient_name, nutrient_data in nutrition.items()
                ]
                st.dataframe(
                    pd.DataFrame(nutrition_rows),
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.caption("No nutrition details found for today yet.")


def render_manual_workout_logger(user_id: int) -> None:
    st.subheader("Manual Workout Logger")
    st.caption("Use this for workouts that are not tied to the planned workout flow.")

    try:
        exercise_response = api_get("/exercises")
        exercise_data = exercise_response.get("exercises", [])
    except requests.RequestException as exc:
        st.error(f"Failed to load exercises: {extract_api_error_message(exc)}")
        exercise_data = []

    exercise_options = {
        f"{exercise['name']} ({exercise.get('equipment', 'Unknown')})": exercise
        for exercise in exercise_data
    }

    if not exercise_options:
        st.warning("No exercises found. Make sure the /exercises endpoint is working.")
        return

    with st.form("manual_workout_logger_form"):
        workout_name = st.text_input("Workout Name", value="Manual Workout")
        duration_minutes = st.number_input(
            "Duration (minutes)",
            min_value=1,
            value=30,
        )
        selected_label = st.selectbox("Exercise", list(exercise_options.keys()))
        reps = st.number_input("Reps", min_value=1, value=10)
        weight = st.number_input("Weight", min_value=0.0, value=50.0, step=5.0)
        rir = st.slider("RIR", min_value=0, max_value=5, value=2)
        add_set = st.form_submit_button("Add Set")

    if add_set:
        selected_exercise = exercise_options[selected_label]
        set_number = len(st.session_state.current_sets) + 1
        st.session_state.current_sets.append(
            {
                "exercise_id": selected_exercise["id"],
                "exercise_name": selected_exercise["name"],
                "set_number": set_number,
                "reps": reps,
                "weight": weight,
                "rir": rir,
            }
        )
        st.success("Set added.")

    if not st.session_state.current_sets:
        return

    st.write("**Current Manual Workout**")
    st.dataframe(
        pd.DataFrame(st.session_state.current_sets),
        width="stretch",
        hide_index=True,
    )
    notes = st.text_area("Workout Notes", key="manual_workout_notes")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Manual Workout"):
            payload = {
                "user_id": user_id,
                "workout_name": workout_name,
                "duration_minutes": duration_minutes,
                "notes": notes,
                "sets": [
                    {
                        "exercise_id": set_data["exercise_id"],
                        "set_number": set_data["set_number"],
                        "reps": set_data["reps"],
                        "weight": set_data["weight"],
                        "rir": set_data["rir"],
                    }
                    for set_data in st.session_state.current_sets
                ],
            }
            try:
                data = api_post("/workouts/create", payload)
            except requests.RequestException as exc:
                st.error(f"Workout save failed: {extract_api_error_message(exc)}")
            else:
                if data.get("success", True):
                    st.success("Workout saved successfully.")
                    st.session_state.current_sets = []
                    st.rerun()
                else:
                    st.error(data.get("message", "Workout save failed."))
    with col2:
        if st.button("Clear Manual Workout"):
            st.session_state.current_sets = []
            st.rerun()


def render_log_workout_section(user_id: int) -> None:
    st.header("Log Workout")
    st.info(
        "This legacy combined logging section is no longer part of the top-level "
        "navigation. Use Today, Workout, and Nutrition instead."
    )


def render_history_section(user_id: int) -> None:
    st.header("History")
    history_tab, manual_tab = st.tabs(["Planned Workout History", "Manual Workouts"])

    with history_tab:
        display_workout_execution_history(user_id)

    with manual_tab:
        st.subheader("Recent Manual Workouts")
        try:
            data = api_get(f"/workouts/{user_id}")
        except requests.RequestException as exc:
            st.error(
                f"Failed to load recent workouts: {extract_api_error_message(exc)}"
            )
            return

        workouts = data.get("workouts") or []
        if not workouts:
            st.info("No manual workout data found.")
            return

        for workout in workouts:
            session = workout["session"]
            with st.expander(f"{session['workout_date']} — {session['workout_name']}"):
                if st.session_state.get("developer_mode", False):
                    col1, col2 = st.columns(2)
                    col1.metric("Duration", f"{session['duration_minutes']} min")
                    col2.metric("Session ID", session.get("id", "Unknown"))
                else:
                    st.metric("Duration", f"{session['duration_minutes']} min")

                workout_rows = [
                    {
                        "Exercise": set_data["name"],
                        "Set": set_data["set_number"],
                        "Reps": set_data["reps"],
                        "Weight": set_data["weight"],
                        "RIR": set_data["rir"],
                    }
                    for set_data in workout["sets"]
                ]
                st.dataframe(
                    pd.DataFrame(workout_rows), width="stretch", hide_index=True
                )


def poll_report_status(user_id: int) -> None:
    if not st.session_state.report_job_id:
        return

    try:
        data = api_get(f"/reports/status/{st.session_state.report_job_id}")
    except requests.RequestException as exc:
        st.error(f"Report status check failed: {extract_api_error_message(exc)}")
        st.session_state.report_job_id = None
        st.session_state.report_job_status = None
        return

    if data.get("success"):
        st.session_state.report_job_status = data["status"]

        if data["status"] == "running":
            st.info("Generating report...")
            st_autorefresh(interval=3000, key="report_refresh")
        elif data["status"] == "completed":
            try:
                latest_data = api_get(f"/reports/latest/{user_id}")
            except requests.RequestException:
                latest_data = {}

            if latest_data.get("success"):
                latest_report = latest_data["report"]
                st.session_state.health_report = latest_report["report_text"]
                st.session_state.health_report_timestamp = latest_report["created_at"]
            else:
                st.session_state.health_report = data.get("report")
                st.session_state.health_report_timestamp = datetime.now().strftime(
                    "%Y-%m-%d %I:%M %p"
                )

            st.session_state.last_completed_job_id = st.session_state.report_job_id
            st.session_state.report_job_id = None
            st.session_state.report_job_status = None
            st.success("AI report completed.")
            st.rerun()
        elif data["status"] == "failed":
            st.error(f"AI report failed: {data.get('report')}")
            st.session_state.report_job_id = None
            st.session_state.report_job_status = None
    else:
        try:
            latest_data = api_get(f"/reports/latest/{user_id}")
        except requests.RequestException:
            latest_data = {}

        if latest_data.get("success"):
            latest_report = latest_data["report"]
            st.session_state.health_report = latest_report["report_text"]
            st.session_state.health_report_timestamp = latest_report["created_at"]
            st.warning(
                "The report job status is no longer available, so the latest saved report was loaded."
            )
        else:
            st.warning(data.get("message", "Report job status unavailable."))

        st.session_state.report_job_id = None
        st.session_state.report_job_status = None


def render_reports_section(user_id: int) -> None:
    st.header("Reports")
    st.caption("Run the slower full report when you want a complete AI health summary.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Load Latest Saved Report", key="load_latest_report_button"):
            try:
                data = api_get(f"/reports/latest/{user_id}")
            except requests.RequestException as exc:
                st.error(
                    f"Failed to load latest report: {extract_api_error_message(exc)}"
                )
            else:
                if data.get("success"):
                    latest_report = data["report"]
                    st.session_state.health_report = latest_report["report_text"]
                    st.session_state.health_report_timestamp = latest_report[
                        "created_at"
                    ]
                    st.success("Latest saved report loaded.")
                else:
                    st.warning("No saved reports found.")

    with col2:
        if st.session_state.report_job_id is None:
            if st.button(
                "Generate Full AI Health Report",
                key="generate_ai_report_button",
                type="primary",
            ):
                try:
                    data = api_post(f"/reports/generate/{user_id}")
                except requests.RequestException as exc:
                    st.error(
                        f"Failed to start report generation: {extract_api_error_message(exc)}"
                    )
                else:
                    if data.get("success"):
                        st.session_state.report_job_id = data["job_id"]
                        st.session_state.report_job_status = data["status"]
                        st.rerun()
                    else:
                        st.error("Failed to start AI report generation.")
        else:
            st.info(f"Report job running: {st.session_state.report_job_id}")

    poll_report_status(user_id)

    if st.session_state.health_report_timestamp:
        st.caption(f"Last generated: {st.session_state.health_report_timestamp}")

    if st.session_state.health_report:
        st.markdown(st.session_state.health_report)
    elif st.session_state.report_job_id is None:
        st.info("No report loaded yet.")

    st.subheader("Report History")
    try:
        data = api_get(f"/reports/history/{user_id}")
    except requests.RequestException as exc:
        st.error(f"Failed to load report history: {extract_api_error_message(exc)}")
        return

    reports = data.get("reports") or []
    if reports:
        for report in reports:
            with st.expander(f"{report['created_at']}"):
                st.write(report["report_text"])
    else:
        st.info("No report history found.")

    developer_details("Developer details: report history", data)


def render_developer_section(user_id: int) -> None:
    st.header("Developer")
    st.caption(
        "Developer details are hidden from the main UI unless Developer Mode is on."
    )

    if not st.session_state.get("developer_mode", False):
        st.info("Turn on Developer Mode in the sidebar to show raw backend responses.")
        return

    st.subheader("Session State")
    st.json(
        {
            "selected_user_id": st.session_state.selected_user_id,
            "report_job_id": st.session_state.report_job_id,
            "report_job_status": st.session_state.report_job_status,
            "last_completed_job_id": st.session_state.last_completed_job_id,
            "has_selected_workout_plan_response": st.session_state.selected_workout_plan_response
            is not None,
            "has_started_workout_plan_response": st.session_state.started_workout_plan_response
            is not None,
            "has_completed_workout_plan_response": st.session_state.completed_workout_plan_response
            is not None,
        }
    )

    st.subheader("Quick Endpoint Checks")
    endpoint_options = {
        "Health State": f"/health-state/{user_id}",
        "Daily Recommendation": f"/recommendations/daily/{user_id}",
        "Workout Preview": f"/workout-plans/preview/{user_id}",
        "Workout History": f"/workout-plans/history/{user_id}",
        "Equipment Profile": f"/users/{user_id}/equipment-profile",
    }

    selected_endpoint_label = st.selectbox(
        "Endpoint",
        options=list(endpoint_options.keys()),
    )

    if st.button("Run Endpoint Check"):
        try:
            response = api_get(endpoint_options[selected_endpoint_label])
        except requests.RequestException as exc:
            st.error(extract_api_error_message(exc))
        else:
            st.json(response)


# =====================================
# Main Navigation
# =====================================

(
    today_tab,
    workout_tab,
    nutrition_tab,
    history_tab,
    reports_tab,
    developer_tab,
) = st.tabs(
    [
        "Today",
        "Workout",
        "Nutrition",
        "History",
        "Reports",
        "Developer",
    ]
)

with today_tab:
    render_today_section(user_id)

with workout_tab:
    render_workout_plan_section(user_id)

with nutrition_tab:
    render_nutrition_section(user_id)

with history_tab:
    render_history_section(user_id)

with reports_tab:
    render_reports_section(user_id)

with developer_tab:
    render_developer_section(user_id)
