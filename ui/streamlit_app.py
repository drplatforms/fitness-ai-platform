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


def display_workout_plan_preview(workout_plan: dict) -> None:
    title = workout_plan.get("title", "Workout Plan Preview")
    session_focus = workout_plan.get("session_focus", "No focus available.")
    duration_minutes = workout_plan.get("duration_minutes", "Unknown")
    warmup = workout_plan.get("warmup")
    cooldown = workout_plan.get("cooldown")
    progression_guidance = workout_plan.get("progression_guidance")
    rationale = workout_plan.get("rationale")
    confidence = workout_plan.get("confidence", "Unknown")
    exercises = workout_plan.get("exercises") or []

    st.subheader(title)

    col1, col2 = st.columns(2)
    col1.metric("Duration", f"{duration_minutes} min")
    col2.metric("Confidence", confidence)

    st.write(f"**Focus:** {session_focus}")

    if warmup:
        st.write(f"**Warmup:** {warmup}")

    exercise_rows = []
    for exercise in exercises:
        rir_min = exercise.get("rir_min")
        rir_max = exercise.get("rir_max")
        reps_min = exercise.get("reps_min")
        reps_max = exercise.get("reps_max")

        exercise_rows.append(
            {
                "Exercise": exercise.get("name", "Unknown"),
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
                "Notes": exercise.get("notes", ""),
            }
        )

    if exercise_rows:
        st.dataframe(
            pd.DataFrame(exercise_rows),
            width="stretch",
            hide_index=True,
        )
    else:
        st.warning("No exercises are available for this workout preview.")

    if progression_guidance:
        st.write(f"**Progression guidance:** {progression_guidance}")

    if cooldown:
        st.write(f"**Cooldown:** {cooldown}")

    if rationale:
        st.write(f"**Why:** {rationale}")


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


def display_planned_exercises(planned_exercises: list[dict]) -> None:
    if not planned_exercises:
        st.warning("No planned exercises were returned.")
        return

    planned_rows = []

    for exercise in planned_exercises:
        reps_min = exercise.get("reps_min")
        reps_max = exercise.get("reps_max")
        rir_min = exercise.get("rir_min")
        rir_max = exercise.get("rir_max")
        equipment_required = exercise.get("equipment_required") or []

        planned_rows.append(
            {
                "Order": exercise.get("exercise_order", "Unknown"),
                "Exercise": exercise.get("name", "Unknown"),
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

    for actual_set in actual_sets:
        actual_rows.append(
            {
                "ID": actual_set.get("id", "Unknown"),
                "Planned Exercise ID": actual_set.get(
                    "planned_workout_exercise_id",
                    "None",
                ),
                "Exercise": actual_set.get("exercise_name", "Unknown"),
                "Set": actual_set.get("set_number", "Unknown"),
                "Actual Reps": actual_set.get("actual_reps", "Unknown"),
                "Actual Weight": actual_set.get("actual_weight", "Unknown"),
                "Actual RIR": actual_set.get("actual_rir", "Unknown"),
                "Completed": actual_set.get("completed", False),
                "Skipped": actual_set.get("skipped", False),
                "Substitution For": actual_set.get(
                    "substitution_for_planned_exercise_id",
                    "",
                )
                or "",
                "Notes": actual_set.get("notes") or "",
            }
        )

    st.dataframe(
        pd.DataFrame(actual_rows),
        width="stretch",
        hide_index=True,
    )


def display_planned_vs_actual_summary(summary: dict) -> None:
    st.subheader("Planned vs Actual Summary")

    if not summary:
        st.info("Planned-vs-actual summary is not available yet.")
        return

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Completion",
        f"{summary.get('completion_percentage', 0)}%",
    )
    col2.metric(
        "Planned Exercises",
        summary.get("planned_exercise_count", "Unknown"),
    )
    col3.metric(
        "Completed Exercises",
        summary.get("completed_exercise_count", "Unknown"),
    )
    col4.metric(
        "Skipped Exercises",
        summary.get("skipped_exercise_count", "Unknown"),
    )

    col5, col6, col7, col8 = st.columns(4)

    col5.metric(
        "Planned Sets",
        summary.get("planned_set_count", "Unknown"),
    )
    col6.metric(
        "Actual Sets",
        summary.get("actual_set_count", "Unknown"),
    )
    col7.metric(
        "Completed Sets",
        summary.get("completed_set_count", "Unknown"),
    )
    col8.metric(
        "Skipped Sets",
        summary.get("skipped_set_count", "Unknown"),
    )

    col9, col10, col11 = st.columns(3)

    col9.metric(
        "Avg Planned RIR",
        summary.get("average_planned_rir", "Unknown"),
    )
    col10.metric(
        "Avg Actual RIR",
        summary.get("average_actual_rir", "Unknown"),
    )
    col11.metric(
        "RIR Deviation",
        summary.get("rir_deviation", "Unknown"),
    )

    rep_deviation = summary.get("rep_deviation") or {}

    rep_rows = [
        {
            "Metric": "Sets Below Planned Reps",
            "Value": summary.get("sets_below_planned_reps", "Unknown"),
        },
        {
            "Metric": "Sets Inside Planned Reps",
            "Value": summary.get("sets_inside_planned_reps", "Unknown"),
        },
        {
            "Metric": "Sets Above Planned Reps",
            "Value": summary.get("sets_above_planned_reps", "Unknown"),
        },
    ]

    for key, value in rep_deviation.items():
        rep_rows.append(
            {
                "Metric": humanize_label(key),
                "Value": value,
            }
        )

    st.dataframe(
        pd.DataFrame(rep_rows),
        width="stretch",
        hide_index=True,
    )

    deviation_flags = summary.get("deviation_flags") or []
    notes = summary.get("notes") or []

    if deviation_flags:
        st.write("**Deviation Flags**")
        for flag in deviation_flags:
            st.warning(humanize_label(flag))

    if notes:
        st.write("**Summary Notes**")
        for note in notes:
            st.info(note)


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


def display_actual_set_logging(plan_instance_id: int) -> None:
    try:
        execution_response = api_get(f"/workout-plans/{plan_instance_id}/execution")
    except requests.RequestException as exc:
        st.error(f"Failed to load actual set logger: {extract_api_error_message(exc)}")
        return

    workout_plan_instance = execution_response.get("workout_plan_instance", {})
    execution_session = execution_response.get("execution_session", {})
    planned_exercises = execution_response.get("planned_exercises", [])

    plan_status = workout_plan_instance.get("status")
    execution_status = execution_session.get("status")

    st.subheader("Actual Set Logging")

    if plan_status not in {"started", "in_progress"} and execution_status not in {
        "started",
        "in_progress",
    }:
        st.info(
            "Actual set logging will appear after this selected plan is started. "
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

    planned_options = {
        planned_exercise_option_label(exercise): exercise
        for exercise in planned_exercises
    }

    with st.form(f"actual_set_logging_form_{plan_instance_id}"):
        logging_mode = st.radio(
            "Log Type",
            options=[
                "Completed planned set",
                "Skipped planned set",
                "Substitution",
            ],
            horizontal=True,
        )

        selected_planned_label = st.selectbox(
            "Planned Exercise",
            options=list(planned_options.keys()),
        )

        selected_planned_exercise = planned_options[selected_planned_label]

        set_number = st.number_input(
            "Set Number",
            min_value=1,
            value=1,
            step=1,
        )

        actual_exercise_name = None
        if logging_mode == "Substitution":
            actual_exercise_name = st.text_input(
                "Actual Exercise Name",
                value="",
                help="Use this when you performed a different exercise than planned.",
            )

        actual_reps = None
        actual_weight = None
        actual_rir = None

        if logging_mode != "Skipped planned set":
            default_reps = selected_planned_exercise.get("reps_min") or 1
            default_rir = selected_planned_exercise.get("rir_max") or 2

            col1, col2, col3 = st.columns(3)

            with col1:
                actual_reps = st.number_input(
                    "Actual Reps",
                    min_value=0,
                    value=int(default_reps),
                    step=1,
                )

            with col2:
                actual_weight = st.number_input(
                    "Actual Weight",
                    min_value=0.0,
                    value=0.0,
                    step=5.0,
                )

            with col3:
                actual_rir = st.slider(
                    "Actual RIR",
                    min_value=0,
                    max_value=10,
                    value=int(default_rir),
                )
        else:
            st.info(
                "Skipped sets are recorded without reps, weight, or RIR. "
                "Use notes to explain why the set or exercise was skipped."
            )

        actual_set_notes = st.text_area("Actual Set Notes")

        submit_actual_set = st.form_submit_button("Log Actual Set")

    if submit_actual_set:
        payload = {
            "set_number": int(set_number),
            "notes": actual_set_notes or None,
        }

        if logging_mode == "Skipped planned set":
            payload.update(
                {
                    "planned_workout_exercise_id": selected_planned_exercise["id"],
                    "completed": False,
                    "skipped": True,
                }
            )

        elif logging_mode == "Substitution":
            if not actual_exercise_name or not actual_exercise_name.strip():
                st.error("Actual Exercise Name is required for substitutions.")
                return

            payload.update(
                {
                    "substitution_for_planned_exercise_id": selected_planned_exercise[
                        "id"
                    ],
                    "exercise_name": actual_exercise_name.strip(),
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
                actual_set_id = actual_set.get("id", "Unknown")
                st.session_state.actual_set_logging_message = (
                    f"Actual set logged successfully. Actual set ID: {actual_set_id}."
                )
                st.rerun()
            else:
                st.error("Actual set logging failed.")

        except requests.RequestException as exc:
            st.error(f"Actual set logging failed: {extract_api_error_message(exc)}")

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
    st.subheader("Actual Set Corrections")

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

    with st.expander("Developer details: actual set correction"):
        st.subheader("Raw Execution Response Used By Correction Form")
        st.json(execution_response)

        if st.session_state.actual_set_edit_response:
            st.subheader("Latest Raw PATCH Response")
            st.json(st.session_state.actual_set_edit_response)


def display_complete_workout_control(plan_instance_id: int) -> None:
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
            key=f"complete_workout_plan_button_{plan_instance_id}",
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

        display_planned_vs_actual_summary(summary)

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

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Plan Status",
        humanize_label(workout_plan_instance.get("status")),
    )
    col2.metric(
        "Execution Status",
        humanize_label(execution_session.get("status")),
    )
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

    st.write("**Planned Exercises**")
    display_planned_exercises(planned_exercises)
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
            planned_vs_actual_response.get("planned_vs_actual_summary", {})
        )
    except requests.RequestException as exc:
        planned_vs_actual_error = extract_api_error_message(exc)
        st.info(
            f"Planned-vs-actual summary is not available yet: {planned_vs_actual_error}"
        )

    with st.expander("Developer details: workout execution review"):
        st.subheader("Raw Execution Response")
        st.json(execution_response)

        if planned_vs_actual_response:
            st.subheader("Raw Planned-vs-Actual Response")
            st.json(planned_vs_actual_response)

        if planned_vs_actual_error:
            st.subheader("Planned-vs-Actual Error")
            st.write(planned_vs_actual_error)


def display_workout_execution_history_item(history_item: dict) -> None:
    workout_plan_instance = history_item.get("workout_plan_instance", {})
    execution_session = history_item.get("execution_session") or {}
    planned_vs_actual_summary = history_item.get("planned_vs_actual_summary")

    plan_instance_id = workout_plan_instance.get("id", "Unknown")
    plan_status = workout_plan_instance.get("status")
    execution_status = execution_session.get("status")

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

    col4.metric(
        "Scenario",
        scenario_display_name(workout_plan_instance.get("scenario")),
    )
    col5.metric(
        "Confidence",
        workout_plan_instance.get("confidence", "Unknown"),
    )
    col6.metric(
        "Workout Session ID",
        execution_session.get("workout_session_id") or "Not created",
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
            context_key=f"history_{plan_instance_id}",
        )


def display_workout_execution_history(user_id: int) -> None:
    st.header("📜 Workout Execution History")

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

            expander_label = (
                f"Plan {plan_instance_id} — {title} — "
                f"{plan_status} — selected {selected_at}"
            )

            with st.expander(expander_label):
                display_workout_execution_history_item(history_item)

                if execution_session.get("completed_at"):
                    st.caption(f"Completed at: {execution_session['completed_at']}")

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
    "barbell",
    "bodyweight",
    "cable",
    "dumbbell",
    "kettlebell",
    "machine",
]


def equipment_display_name(value: str) -> str:
    return value.replace("_", " ").title()


# =====================================
# Session State Initialization
# =====================================

if "health_report" not in st.session_state:
    st.session_state.health_report = None

if "health_report_timestamp" not in st.session_state:
    st.session_state.health_report_timestamp = None

if "report_job_id" not in st.session_state:
    st.session_state.report_job_id = None

if "report_job_status" not in st.session_state:
    st.session_state.report_job_status = None

if "last_completed_job_id" not in st.session_state:
    st.session_state.last_completed_job_id = None

if "current_sets" not in st.session_state:
    st.session_state.current_sets = []

if "food_search_results" not in st.session_state:
    st.session_state.food_search_results = []

if "equipment_profile_saved" not in st.session_state:
    st.session_state.equipment_profile_saved = False

if "selected_workout_plan_response" not in st.session_state:
    st.session_state.selected_workout_plan_response = None

if "started_workout_plan_response" not in st.session_state:
    st.session_state.started_workout_plan_response = None

if "workout_plan_action_error" not in st.session_state:
    st.session_state.workout_plan_action_error = None

if "actual_set_logging_message" not in st.session_state:
    st.session_state.actual_set_logging_message = None

if "completed_workout_plan_response" not in st.session_state:
    st.session_state.completed_workout_plan_response = None

if "workout_completion_message" not in st.session_state:
    st.session_state.workout_completion_message = None

if "workout_completion_error" not in st.session_state:
    st.session_state.workout_completion_error = None

if "actual_set_editing_message" not in st.session_state:
    st.session_state.actual_set_editing_message = None

if "actual_set_editing_error" not in st.session_state:
    st.session_state.actual_set_editing_error = None

if "actual_set_edit_response" not in st.session_state:
    st.session_state.actual_set_edit_response = None

# =====================================
# App Configuration
# =====================================

st.set_page_config(
    page_title="Fitness AI",
    layout="wide",
)

st.title("🏋️ Fitness AI Platform")


# =====================================
# User Selection
# =====================================

USER_OPTIONS = {
    "User 1": 1,
    "User 2": 2,
    "QA 101 — Under-recovered lifter": 101,
    "QA 102 — Well-recovered baseline": 102,
    "QA 103 — Nutrition/training mismatch": 103,
    "QA 104 — Improving after deload": 104,
    "QA 105 — Messy/incomplete logging": 105,
}

selected_user_label = st.selectbox(
    "Select User",
    options=list(USER_OPTIONS.keys()),
    index=0,
)

user_id = USER_OPTIONS[selected_user_label]

if "selected_user_id" not in st.session_state:
    st.session_state.selected_user_id = user_id

if st.session_state.selected_user_id != user_id:
    st.session_state.selected_user_id = user_id

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

    st.rerun()

# =====================================
# Load Cached Report
# =====================================

if st.button(
    "Load Latest Saved Report",
    key="load_latest_report_button",
):
    response = requests.get(f"http://127.0.0.1:8000/reports/latest/{user_id}")

    data = response.json()

    if data["success"]:
        latest_report = data["report"]

        st.session_state.health_report = latest_report["report_text"]

        st.session_state.health_report_timestamp = latest_report["created_at"]

        st.success("Latest saved report loaded.")

    else:
        st.warning("No saved reports found.")


# =====================================
# AI Health Coordinator
# =====================================

st.header("🧠 AI Health Insights")

response = requests.get(f"http://127.0.0.1:8000/health-state/{user_id}")

data = response.json()

if data["success"]:
    health_state = data["health_state"]

    recovery = health_state["recovery_state"]
    training = health_state["training_state"]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Recovery Score",
        recovery["recovery_score"],
    )

    col2.metric(
        "Fatigue Risk",
        recovery["fatigue_risk"],
    )

    col3.metric(
        "Readiness",
        recovery["readiness_level"],
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Sleep Trend",
        recovery["sleep_trend"],
    )

    col5.metric(
        "Weight Trend",
        recovery["weight_trend"],
    )

    col6.metric(
        "System Stress",
        health_state.get("system_stress_level", "Unknown"),
    )

    st.caption(
        f"Training adherence: "
        f"{training['adherence_level']} | "
        f"Training trend: "
        f"{training['training_trend']}"
    )

st.write(
    "Current Job ID:",
    st.session_state.report_job_id,
)

st.write(
    "Last Completed Job:",
    st.session_state.last_completed_job_id,
)

if st.session_state.health_report_timestamp:
    st.caption(f"Last Generated: {st.session_state.health_report_timestamp}")

# =====================================
# Daily Grounded Recommendation
# =====================================

st.header("✅ Daily Grounded Recommendation")

try:
    recommendation_data = api_get(f"/recommendations/daily/{user_id}")

    if recommendation_data.get("success"):
        scenario = recommendation_data.get("scenario")
        confidence = recommendation_data.get("confidence", "Unknown")
        approved_plan = recommendation_data.get("approved_action_plan", {})
        nutrition_targets = recommendation_data.get("nutrition_targets", {})
        training_constraints = recommendation_data.get("training_constraints", {})

        col1, col2 = st.columns(2)

        col1.metric(
            "Status",
            scenario_display_name(scenario),
        )

        col2.metric(
            "Confidence",
            confidence,
        )

        st.subheader("Daily Coaching Recommendation")
        st.write(
            approved_plan.get(
                "daily_coaching_recommendation",
                "No daily coaching recommendation available.",
            )
        )

        st.subheader("Workout Recommendation")
        st.write(
            approved_plan.get(
                "workout_recommendation",
                "No workout recommendation available.",
            )
        )

        st.subheader("Nutrition Action")
        st.write(
            approved_plan.get(
                "nutrition_action",
                "No nutrition action available.",
            )
        )

        st.subheader("Why")
        st.write(
            approved_plan.get(
                "rationale",
                "No rationale available.",
            )
        )

        display_nutrition_targets(nutrition_targets)
        display_training_constraints(training_constraints)

        with st.expander("Developer details"):
            st.json(recommendation_data)

    else:
        st.warning("No daily recommendation is available for this user yet.")

except requests.RequestException as exc:
    st.error(f"Failed to load daily recommendation: {exc}")


# =====================================
# Equipment Profile Editor
# =====================================

st.header("🏋️ Equipment Profile")

if st.session_state.equipment_profile_saved:
    st.success(
        "Equipment profile saved. Workout Plan Preview will use the updated profile."
    )
    st.session_state.equipment_profile_saved = False

try:
    equipment_profile_response = api_get(f"/users/{user_id}/equipment-profile")

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

    current_available_equipment = equipment_profile.get(
        "available_equipment",
        [],
    )

    current_unavailable_equipment = equipment_profile.get(
        "unavailable_equipment",
        [],
    )

    training_environment_keys = list(TRAINING_ENVIRONMENT_OPTIONS.keys())

    if current_training_environment in training_environment_keys:
        training_environment_index = training_environment_keys.index(
            current_training_environment
        )
    else:
        training_environment_index = training_environment_keys.index("unknown")

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
            save_response = api_put(
                f"/users/{user_id}/equipment-profile",
                payload,
            )

            if save_response.get("success"):
                st.session_state.equipment_profile_saved = True
                st.session_state.selected_workout_plan_response = None
                st.session_state.started_workout_plan_response = None
                st.session_state.workout_plan_action_error = None
                st.session_state.actual_set_logging_message = None
                st.session_state.completed_workout_plan_response = None
                st.session_state.workout_completion_message = None
                st.session_state.workout_completion_error = None
                st.rerun()
            else:
                st.error("Equipment profile save failed.")

        except requests.RequestException as exc:
            st.error(f"Equipment profile save failed: {exc}")

    with st.expander("Developer details: equipment profile"):
        st.json(equipment_profile_response)

except requests.RequestException as exc:
    st.error(f"Failed to load equipment profile: {exc}")


# =====================================
# Workout Plan Preview
# =====================================

st.header("🏋️ Workout Plan Preview")

try:
    workout_plan_data = api_get(f"/workout-plans/preview/{user_id}")

    if workout_plan_data.get("success"):
        scenario = workout_plan_data.get("scenario")
        confidence = workout_plan_data.get("confidence", "Unknown")
        approved_workout_plan = workout_plan_data.get("approved_workout_plan", {})
        training_constraints = workout_plan_data.get("training_constraints", {})
        workout_constraints = workout_plan_data.get("workout_constraints", {})

        col1, col2 = st.columns(2)

        col1.metric(
            "Plan Context",
            scenario_display_name(scenario),
        )

        col2.metric(
            "Confidence",
            confidence,
        )

        display_workout_plan_preview(approved_workout_plan)

        if st.button("Select This Plan", key="select_workout_plan_button"):
            try:
                select_response = api_post(f"/workout-plans/{user_id}/select")

                if select_response.get("success"):
                    st.session_state.selected_workout_plan_response = select_response
                    st.session_state.started_workout_plan_response = None
                    st.session_state.workout_plan_action_error = None
                    st.session_state.actual_set_logging_message = None
                    st.session_state.completed_workout_plan_response = None
                    st.session_state.workout_completion_message = None
                    st.session_state.workout_completion_error = None
                    st.success("Workout plan selected.")
                    st.rerun()
                else:
                    st.session_state.workout_plan_action_error = (
                        "Workout plan selection failed."
                    )

            except requests.RequestException as exc:
                st.session_state.workout_plan_action_error = (
                    f"Workout plan selection failed: {extract_api_error_message(exc)}"
                )

        active_plan_response = (
            st.session_state.started_workout_plan_response
            or st.session_state.selected_workout_plan_response
        )

        if active_plan_response:
            display_selected_workout_plan_state(active_plan_response)

            workout_plan_instance = active_plan_response.get(
                "workout_plan_instance",
                {},
            )
            plan_instance_id = workout_plan_instance.get("id")

            if plan_instance_id is not None:
                start_button_label = (
                    "Start Selected Plan"
                    if workout_plan_instance.get("status") == "selected"
                    else "Start Again"
                )

                if st.button(
                    start_button_label,
                    key=f"start_workout_plan_button_{plan_instance_id}",
                ):
                    try:
                        start_response = api_post(
                            f"/workout-plans/{plan_instance_id}/start"
                        )

                        if start_response.get("success"):
                            st.session_state.started_workout_plan_response = (
                                start_response
                            )
                            st.session_state.workout_plan_action_error = None
                            st.session_state.actual_set_logging_message = None
                            st.session_state.completed_workout_plan_response = None
                            st.session_state.workout_completion_message = None
                            st.session_state.workout_completion_error = None
                            st.success("Workout plan started.")
                            st.rerun()
                        else:
                            st.session_state.workout_plan_action_error = (
                                "Workout plan start failed."
                            )

                    except requests.RequestException as exc:
                        st.session_state.workout_plan_action_error = (
                            "Workout plan start failed: "
                            f"{extract_api_error_message(exc)}"
                        )

                display_actual_set_logging(plan_instance_id)
                display_complete_workout_control(plan_instance_id)
                display_workout_execution_review(plan_instance_id)

        if st.session_state.workout_plan_action_error:
            st.error(st.session_state.workout_plan_action_error)

        with st.expander("Developer details: workout plan preview/select/start"):
            st.subheader("Training Constraints")
            st.json(training_constraints)
            st.subheader("Workout Constraints")
            st.json(workout_constraints)
            st.subheader("Raw Workout Plan Preview Response")
            st.json(workout_plan_data)

            if st.session_state.selected_workout_plan_response:
                st.subheader("Raw Select Response")
                st.json(st.session_state.selected_workout_plan_response)

            if st.session_state.started_workout_plan_response:
                st.subheader("Raw Start Response")
                st.json(st.session_state.started_workout_plan_response)

    else:
        st.warning("No workout plan preview is available for this user yet.")

except requests.RequestException as exc:
    st.error(f"Failed to load workout plan preview: {exc}")


# =====================================
# Workout Execution History
# =====================================

display_workout_execution_history(user_id)


# =====================================
# Generate Report Button
# =====================================

if st.session_state.report_job_id is None:
    if st.button(
        "Generate AI Health Report",
        key="generate_ai_report_button",
    ):
        response = requests.post(f"http://127.0.0.1:8000/reports/generate/{user_id}")

        data = response.json()

        if data["success"]:
            st.session_state.report_job_id = data["job_id"]

            st.session_state.report_job_status = data["status"]

        else:
            st.error("Failed to start AI report generation.")


# =====================================
# Active Report Polling
# =====================================

if st.session_state.report_job_id:
    response = requests.get(
        f"{API_BASE_URL}/reports/status/{st.session_state.report_job_id}"
    )

    data = response.json()

    if data["success"]:
        st.session_state.report_job_status = data["status"]

        # ---------------------------------
        # Running
        # ---------------------------------

        if data["status"] == "running":
            st.info("Generating report...")

            st_autorefresh(interval=3000, key="report_refresh")

        # ---------------------------------
        # Completed
        # ---------------------------------

        elif data["status"] == "completed":
            latest_response = requests.get(f"{API_BASE_URL}/reports/latest/{user_id}")
            latest_data = latest_response.json()

            if latest_data.get("success"):
                latest_report = latest_data["report"]

                st.session_state.health_report = latest_report["report_text"]
                st.session_state.health_report_timestamp = latest_report["created_at"]

            else:
                st.session_state.health_report = data["report"]
                st.session_state.health_report_timestamp = datetime.now().strftime(
                    "%Y-%m-%d %I:%M %p"
                )

            st.session_state.last_completed_job_id = st.session_state.report_job_id

            st.session_state.report_job_id = None

            st.session_state.report_job_status = None

            st.success("AI report completed.")

        # ---------------------------------
        # Failed
        # ---------------------------------

        elif data["status"] == "failed":
            st.error(f"AI report failed: {data['report']}")

            st.session_state.report_job_id = None

            st.session_state.report_job_status = None

    else:
        latest_response = requests.get(f"{API_BASE_URL}/reports/latest/{user_id}")
        latest_data = latest_response.json()

        if latest_data.get("success"):
            latest_report = latest_data["report"]

            st.session_state.health_report = latest_report["report_text"]
            st.session_state.health_report_timestamp = latest_report["created_at"]
            st.session_state.report_job_id = None
            st.session_state.report_job_status = None

            st.warning(
                "The report job status is no longer available, "
                "so the latest saved report was loaded."
            )

        else:
            st.warning(data.get("message", "Report job status unavailable."))
            st.session_state.report_job_id = None
            st.session_state.report_job_status = None


# =====================================
# Display Health Report
# =====================================

if st.session_state.health_report:
    st.write(st.session_state.health_report)

elif st.session_state.report_job_id is None:
    st.info("Click the button to generate a new AI health report.")

# =====================================
# Recovery Check-In
# =====================================

st.header("🛌 Recovery Check-In")

with st.form("recovery_checkin_form"):
    body_weight = st.number_input(
        "Body Weight",
        min_value=0.0,
        value=200.0,
        step=0.5,
    )

    sleep_hours = st.number_input(
        "Sleep Hours",
        min_value=0.0,
        max_value=24.0,
        value=7.0,
        step=0.5,
    )

    energy_level = st.slider(
        "Energy Level",
        min_value=1,
        max_value=10,
        value=6,
    )

    soreness_level = st.slider(
        "Soreness Level",
        min_value=1,
        max_value=10,
        value=4,
    )

    mood = st.text_input("Mood", value="Okay")

    notes = st.text_area("Recovery Notes")

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

        if data.get("success", True):
            st.success("Recovery check-in saved.")
        else:
            st.error(data.get("message", "Recovery check-in failed."))

    except requests.RequestException as exc:
        st.error(f"Recovery check-in failed: {exc}")

# =====================================
# Nutrition Logger
# =====================================

st.header("🍽️ Log Food")

with st.form("food_search_form"):
    food_query = st.text_input("Search Food", value="")
    search_food = st.form_submit_button("Search Food")

if search_food:
    if not food_query.strip():
        st.warning("Enter a food search term.")
    else:
        try:
            data = api_get(
                "/foods/search",
                params={"query": food_query},
            )

            st.session_state.food_search_results = data.get("foods", [])

            if not st.session_state.food_search_results:
                st.warning("No foods found.")

        except requests.RequestException as exc:
            st.error(f"Food search failed: {exc}")

if st.session_state.food_search_results:
    food_options = {
        f"{food['id']} - {food['name']}": food
        for food in st.session_state.food_search_results
    }

    selected_food_label = st.selectbox(
        "Select Food",
        list(food_options.keys()),
    )

    selected_food = food_options[selected_food_label]

    grams = st.number_input(
        "Grams Consumed",
        min_value=1.0,
        value=100.0,
        step=5.0,
    )

    if st.button("Log Food", key="log_food_button"):
        payload = {
            "user_id": user_id,
            "food_id": selected_food["id"],
            "grams": grams,
        }

        try:
            data = api_post("/nutrition/log", payload)

            if data.get("success", True):
                st.success("Food logged successfully.")
                st.session_state.food_search_results = []
                st.rerun()
            else:
                st.error(data.get("message", "Food logging failed."))

        except requests.RequestException as exc:
            st.error(f"Food logging failed: {exc}")

# =====================================
# Nutrition Section
# =====================================

st.header("🍎 Nutrition")

today = datetime.now().strftime("%Y-%m-%d")

response = requests.get(f"http://127.0.0.1:8000/nutrition/{user_id}/{today}")

data = response.json()

nutrition = data.get("nutrition") or {}

if nutrition:
    nutrition_rows = []

    for nutrient_name, nutrient_data in nutrition.items():
        nutrition_rows.append(
            {
                "Nutrient": nutrient_name,
                "Amount": nutrient_data["amount"],
                "Unit": nutrient_data["unit"],
            }
        )

    nutrition_df = pd.DataFrame(nutrition_rows)

    st.dataframe(
        nutrition_df,
        width="stretch",
    )

else:
    st.warning("No nutrition data found.")

# =====================================
# Workout Logger
# =====================================

st.header("📝 Log Workout")

try:
    exercise_response = api_get("/exercises")
    exercise_data = exercise_response.get("exercises", [])

except requests.RequestException as exc:
    st.error(f"Failed to load exercises: {exc}")
    exercise_data = []

exercise_options = {
    f"{exercise['name']} ({exercise['equipment']})": exercise
    for exercise in exercise_data
}

if exercise_options:
    with st.form("workout_logger_form"):
        workout_name = st.text_input(
            "Workout Name",
            value="Test Workout",
        )

        duration_minutes = st.number_input(
            "Duration (minutes)",
            min_value=1,
            value=30,
        )

        selected_label = st.selectbox(
            "Exercise",
            list(exercise_options.keys()),
        )

        reps = st.number_input(
            "Reps",
            min_value=1,
            value=10,
        )

        weight = st.number_input(
            "Weight",
            min_value=0.0,
            value=50.0,
            step=5.0,
        )

        rir = st.slider(
            "RIR",
            min_value=0,
            max_value=5,
            value=2,
        )

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

    if st.session_state.current_sets:
        st.subheader("Current Workout")

        workout_preview = pd.DataFrame(st.session_state.current_sets)

        st.dataframe(
            workout_preview,
            width="stretch",
        )

        notes = st.text_area("Workout Notes")

        if st.button("Save Workout"):
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

                if data.get("success", True):
                    st.success("Workout saved successfully.")
                    st.session_state.current_sets = []
                    st.rerun()
                else:
                    st.error(data.get("message", "Workout save failed."))

            except requests.RequestException as exc:
                st.error(f"Workout save failed: {exc}")

else:
    st.warning("No exercises found. Make sure the /exercises endpoint is working.")


# =====================================
# Workout Section
# =====================================

st.header("🏋️ Recent Workouts")

response = requests.get(f"http://127.0.0.1:8000/workouts/{user_id}")

data = response.json()

workouts = data.get("workouts") or []

if workouts:
    for workout in workouts:
        session = workout["session"]

        st.subheader(session["workout_name"])

        st.write(f"Date: {session['workout_date']}")

        st.write(f"Duration: {session['duration_minutes']} minutes")

        workout_rows = []

        for set_data in workout["sets"]:
            workout_rows.append(
                {
                    "Exercise": set_data["name"],
                    "Set": set_data["set_number"],
                    "Reps": set_data["reps"],
                    "Weight": set_data["weight"],
                    "RIR": set_data["rir"],
                }
            )

        workout_df = pd.DataFrame(workout_rows)

        st.dataframe(
            workout_df,
            width="stretch",
        )

else:
    st.warning("No workout data found.")


# =====================================
# Report History Section
# =====================================

st.header("📚 Report History")

response = requests.get(f"http://127.0.0.1:8000/reports/history/{user_id}")

data = response.json()

reports = data.get("reports") or []

if reports:
    for report in reports:
        with st.expander(f"{report['created_at']}"):
            st.write(report["report_text"])

else:
    st.warning("No report history found.")
