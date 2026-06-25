# =====================================
# Imports
# =====================================

from datetime import date, datetime
from html import escape
from time import perf_counter

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from services.daily_coach_async_persistence_service import (
    DailyCoachAsyncPersistenceError,
    get_approved_narrative_by_job_id,
    get_async_job,
    get_latest_async_jobs,
    get_latest_displayable_approved_narrative,
)
from services.daily_coach_async_provider_runtime_service import (
    build_daily_coach_async_approved_preview,
    create_developer_mode_provider_runtime_job,
    resolve_daily_coach_async_approved_preview_config,
    resolve_daily_coach_async_provider_runtime_config,
    run_daily_coach_async_provider_runtime_prototype,
)
from services.daily_narrative_feedback_service import (
    DailyNarrativeFeedbackInput,
    list_daily_narrative_feedback,
    save_daily_narrative_feedback,
    summarize_daily_narrative_feedback,
)
from services.daily_narrative_voice_lab_service import (
    build_daily_narrative_voice_lab_result,
    list_daily_narrative_voice_lab_scenarios,
)
from services.runtime_diagnostics_service import build_runtime_db_diagnostics
from services.weekly_coach_summary_persistence_service import (
    WeeklyCoachSummaryPersistenceError,
    get_latest_approved_weekly_summary,
    save_approved_weekly_summary,
)
from services.weekly_coach_summary_service import (
    approved_weekly_summary_to_public_sections,
    generate_approved_weekly_summary,
)
from ui.daily_coach_session_approval import (
    clear_daily_coach_session_approved_narrative,
    daily_coach_preview_approval_eligibility,
    get_daily_coach_session_approved_narrative,
    store_daily_coach_session_approved_narrative,
)

API_BASE_URL = "http://127.0.0.1:8000"


def api_get(
    path: str,
    params: dict | None = None,
    request_timeout: float = 120,
) -> dict:
    response = requests.get(
        f"{API_BASE_URL}{path}",
        params=params,
        timeout=request_timeout,
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


def portfolio_chip_class(tone: str | None = None) -> str:
    if tone == "green":
        return "portfolio-chip portfolio-chip-green"
    if tone == "amber":
        return "portfolio-chip portfolio-chip-amber"
    if tone == "purple":
        return "portfolio-chip portfolio-chip-purple"
    return "portfolio-chip"


def portfolio_chip(label: object, tone: str | None = None) -> str:
    text = escape(str(label or "Unknown"))
    return f'<span class="{portfolio_chip_class(tone)}">{text}</span>'


def portfolio_card_html(
    eyebrow: object,
    title: object,
    body: object = "",
    chips: list[str] | None = None,
    accent_class: str = "portfolio-card-accent",
) -> str:
    chip_html = " ".join(chips or [])
    body_html = f'<div class="portfolio-body">{escape(str(body))}</div>' if body else ""
    return (
        f'<div class="portfolio-card {accent_class}">'
        f'<div class="portfolio-eyebrow">{escape(str(eyebrow or ""))}</div>'
        f'<div class="portfolio-title">{escape(str(title or ""))}</div>'
        f"{body_html}"
        f"<div>{chip_html}</div>"
        f"</div>"
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
    summary_chips = [
        portfolio_chip(f"{duration_minutes} min", "green"),
        portfolio_chip(f"{len(exercises)} exercises", "purple"),
        portfolio_chip(f"Confidence: {confidence}"),
    ]
    st.markdown(
        portfolio_card_html(
            "Backend-approved workout preview",
            title,
            session_focus,
            summary_chips,
            "portfolio-card-purple",
        ),
        unsafe_allow_html=True,
    )
    count_reason = workout_plan.get("exercise_count_user_reason")
    if count_reason:
        st.caption(count_reason)

    if user_id is not None:
        display_workout_plan_explanation(user_id)

    st.markdown("#### Exercises")

    if not exercises:
        st.warning("No exercises are available for this workout preview.")
    else:
        for row_start in range(0, len(exercises), 2):
            columns = st.columns(2)
            for offset, (column, exercise) in enumerate(
                zip(columns, exercises[row_start : row_start + 2], strict=False)
            ):
                index = row_start + offset
                role = workout_exercise_role_label(index, exercise)
                exercise_name = exercise.get("name", "Unknown")
                reps = format_workout_range(
                    exercise.get("reps_min"),
                    exercise.get("reps_max"),
                )
                rir = format_workout_range(
                    exercise.get("rir_min"),
                    exercise.get("rir_max"),
                )
                equipment = format_equipment_required(exercise)
                sets = exercise.get("sets", "Unknown")
                notes = exercise.get("notes")

                chips = [
                    portfolio_chip(f"{sets} sets", "green"),
                    portfolio_chip(f"{reps} reps"),
                    portfolio_chip(f"RIR {rir}", "amber"),
                    portfolio_chip(equipment, "purple"),
                ]
                with column:
                    st.markdown(
                        portfolio_card_html(
                            role,
                            exercise_name,
                            notes or "Approved plan exercise.",
                            chips,
                            "portfolio-card-accent",
                        ),
                        unsafe_allow_html=True,
                    )

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
        st.info(
            "No replacement candidates are available for this exercise yet. "
            "Keep the original exercise or regenerate the workout."
        )
        return

    top_candidates = candidates[:5]
    summary_rows = []

    for candidate in top_candidates:
        reason_codes = candidate.get("compatibility_reason_codes") or []
        first_reason = (
            substitution_reason_label(reason_codes[0])
            if reason_codes
            else "Fits the current workout constraints"
        )
        summary_rows.append(
            {
                "Replacement": candidate.get("name", "Unknown"),
                "Equipment": format_substitution_list(
                    candidate.get("required_equipment")
                ),
                "Why it fits": first_reason,
            }
        )

    st.markdown("##### Suggested replacements")
    st.caption(
        "Pick one compatible option, or keep the original exercise if none feels right."
    )
    st.dataframe(
        pd.DataFrame(summary_rows),
        width="stretch",
        hide_index=True,
    )

    with st.expander("Compare all suggested replacements", expanded=False):
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
                    or "Fits the current workout constraints",
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

    return f"{candidate.get('name', 'Unknown')} ({movement_pattern}; {equipment})"


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

    st.success(f"Workout updated: swapped {original_name} for {replacement_name}.")

    if apply_response.get("previous_active_substitution_replaced"):
        st.caption("This replaced a previous swap for the same exercise.")


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
        if st.session_state.get("developer_mode", False):
            st.session_state.substitution_apply_error_detail = (
                extract_api_error_message(exc)
            )
        st.session_state.substitution_apply_error = "That swap could not be applied. Keep the original exercise or try another replacement."
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
            f"Swapped {planned_exercise_name} for {replacement_name}."
        )
        st.session_state.substitution_apply_error = None
        st.session_state.substitution_apply_error_detail = None
        st.session_state.substitution_flow_ready_to_do_workout = True
        request_workout_flow_step("2. Do Workout")
        st.rerun()

    st.session_state.substitution_apply_error = "That swap could not be applied. Keep the original exercise or try another replacement."
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
            "You can review replacement options now. Apply becomes available once the plan is selected, started, or in progress."
        )
        return

    candidate_options = [
        candidate
        for candidate in candidates
        if candidate.get("catalog_exercise_id") is not None
    ]

    if not candidate_options:
        st.info(
            "No replacement candidates are available for this exercise yet. "
            "Keep the original exercise or regenerate the workout."
        )
        return

    st.markdown("##### Suggested swaps")
    st.caption(
        f"Replacing: **{planned_exercise_name}**. Choose one replacement below, or keep the original."
    )

    for index, candidate in enumerate(candidate_options[:5], start=1):
        reason_codes = candidate.get("compatibility_reason_codes") or []
        first_reason = (
            substitution_reason_label(reason_codes[0])
            if reason_codes
            else "Fits the current workout constraints"
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
                "Apply swap",
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

    keep_col, more_col = st.columns([1, 3])
    with keep_col:
        if st.button(
            "Keep original",
            key=f"substitution_keep_original_{apply_response_key}",
        ):
            st.session_state.substitution_apply_message = (
                f"Keeping {planned_exercise_name} in the workout."
            )
            st.session_state.substitution_apply_error = None
            st.rerun()

    with more_col:
        with st.expander("Compare more replacement options", expanded=False):
            candidate_option_map = {
                substitution_candidate_option_label(candidate): candidate
                for candidate in candidate_options
            }
            selected_candidate_label = st.selectbox(
                "Choose a replacement exercise",
                options=list(candidate_option_map.keys()),
                key=f"substitution_apply_select_{apply_response_key}",
            )
            selected_candidate = candidate_option_map[selected_candidate_label]

            if st.button(
                f"Apply swap for {planned_exercise_name}",
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
    title: str = "Need a swap?",
) -> None:
    st.markdown(f"#### {title}")

    if not planned_exercises:
        st.info("No planned exercises are available for swap lookup.")
        return

    if st.session_state.substitution_apply_message:
        st.success(st.session_state.substitution_apply_message)
        st.session_state.substitution_apply_message = None

    if st.session_state.substitution_apply_error:
        st.error(st.session_state.substitution_apply_error)
        if st.session_state.get("developer_mode", False) and st.session_state.get(
            "substitution_apply_error_detail"
        ):
            st.caption(
                f"Developer detail: {st.session_state.substitution_apply_error_detail}"
            )
        st.session_state.substitution_apply_error = None

    allow_apply = can_apply_substitution(plan_status, execution_status)
    active_substitutions = active_substitutions or {}

    st.caption(
        "Pick the exercise you want to replace, then choose a similar option that fits today’s workout."
    )

    selectable_exercises = [
        exercise for exercise in planned_exercises if exercise.get("id") is not None
    ]

    if not selectable_exercises:
        st.info("No replacement candidates are available for this workout yet.")
        return

    option_labels = [
        f"{exercise.get('exercise_order', index + 1)}. {exercise.get('name', 'Unknown')}"
        for index, exercise in enumerate(selectable_exercises)
    ]
    selected_label = st.selectbox(
        "Choose an exercise to replace",
        options=option_labels,
        key=f"substitution_target_select_{context_key}_{plan_instance_id}",
    )
    selected_index = option_labels.index(selected_label)
    planned_exercise = selectable_exercises[selected_index]

    planned_exercise_id = planned_exercise.get("id")
    planned_exercise_name = planned_exercise.get("name", "Unknown")

    try:
        planned_exercise_id_int = int(planned_exercise_id)
    except (TypeError, ValueError):
        st.info(
            "No replacement candidates are available for this exercise yet. "
            "Keep the original exercise or regenerate the workout."
        )
        return

    active_substitution = active_substitutions.get(planned_exercise_id_int)

    # Replace: user-selected exercise target.
    # Original exercise remains preserved until a swap is applied.
    st.markdown(
        portfolio_card_html(
            "Selected exercise",
            f"Replacing: {planned_exercise_name}",
            "Review suggested replacements below, apply a swap, or keep the original exercise.",
            [
                portfolio_chip("Swap target", "purple"),
                portfolio_chip("Backend behavior unchanged"),
            ],
            "portfolio-card-action",
        ),
        unsafe_allow_html=True,
    )

    if not allow_apply:
        st.caption(
            "Replacement options can be reviewed here, but Apply is only available for selected, started, or in-progress workout plans."
        )

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
        if st.session_state.get("developer_mode", False):
            st.caption(f"Developer detail: {extract_api_error_message(exc)}")
        st.info(
            "No replacement candidates are available for this exercise yet. "
            "Keep the original exercise or regenerate the workout."
        )
        return

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

            latest_apply_response = st.session_state.applied_substitution_responses.get(
                apply_response_key
            )
            if latest_apply_response:
                st.subheader("Latest apply response")
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

st.title("AI Health Coach")
st.caption(
    "Backend-grounded coaching across training, nutrition, and recovery. "
    "The backend owns facts, AI explains approved context, and validators decide "
    "what reaches the user."
)
st.markdown(
    "**Portfolio view:** start with QA 102 for the happy path, then QA 105 for "
    "limited-confidence safety boundaries."
)
# Portfolio visual tightening v3
st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 0.7rem;
        padding: 0.55rem 0.65rem;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.78rem;
        color: #a7b0bd;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.15rem;
    }
    .portfolio-card {
        border: 1px solid rgba(148, 163, 184, 0.24);
        border-radius: 0.85rem;
        padding: 0.72rem 0.82rem;
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.74), rgba(15, 23, 42, 0.42));
        margin-bottom: 0.55rem;
    }
    .portfolio-card-accent { border-left: 4px solid #38bdf8; }
    .portfolio-card-green { border-left: 4px solid #22c55e; }
    .portfolio-card-amber { border-left: 4px solid #f59e0b; }
    .portfolio-card-purple { border-left: 4px solid #a78bfa; }
    .portfolio-eyebrow {
        color: #93c5fd;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .portfolio-title {
        font-size: 1.02rem;
        font-weight: 750;
        line-height: 1.2;
        margin-bottom: 0.28rem;
        color: #f8fafc;
    }
    .portfolio-body {
        font-size: 0.86rem;
        line-height: 1.35;
        color: #cbd5e1;
        margin-bottom: 0.26rem;
    }
    .portfolio-chip {
        display: inline-block;
        border-radius: 999px;
        padding: 0.12rem 0.45rem;
        margin: 0.08rem 0.15rem 0.08rem 0;
        font-size: 0.72rem;
        font-weight: 650;
        color: #dbeafe;
        background: rgba(59, 130, 246, 0.14);
        border: 1px solid rgba(96, 165, 250, 0.28);
    }
    .portfolio-chip-green {
        color: #dcfce7;
        background: rgba(34, 197, 94, 0.13);
        border-color: rgba(74, 222, 128, 0.30);
    }
    .portfolio-chip-amber {
        color: #fef3c7;
        background: rgba(245, 158, 11, 0.13);
        border-color: rgba(251, 191, 36, 0.30);
    }
    .portfolio-chip-purple {
        color: #ede9fe;
        background: rgba(167, 139, 250, 0.13);
        border-color: rgba(196, 181, 253, 0.30);
    }
    .portfolio-muted {
        color: #94a3b8;
        font-size: 0.78rem;
        margin-top: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# Public UI Polish for Portfolio Screenshot Capture v1

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
    "workout_plan_preview_by_user": {},
    "main_navigation_page_override": None,
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
    "substitution_apply_error_detail": None,
    "substitution_flow_ready_to_do_workout": False,
    "workout_flow_step": "1. Plan",
    "workout_flow_step_selector": "1. Plan",
    "workout_flow_step_override": None,
    "workout_daily_state_response": None,
    "workout_daily_state_message": None,
    "developer_mode": False,
    "current_user_id": None,
    "last_user_id": None,
    "daily_recommendation_by_user": {},
    "daily_recommendation_error_by_user": {},
    "daily_coach_narrative_preview_by_user": {},
    "daily_coach_narrative_preview_error_by_user": {},
    "daily_coach_async_developer_job_by_user": {},
    "daily_coach_async_developer_error_by_user": {},
    "daily_coach_async_provider_runtime_result_by_user": {},
    "daily_coach_async_provider_runtime_error_by_user": {},
    "daily_coach_async_provider_runtime_job_id_by_user": {},
    "daily_coach_session_approved_narratives": {},
    "workout_explanation_by_user": {},
    "workout_explanation_error_by_user": {},
    "weekly_coach_summary_preview_by_user": {},
    "weekly_coach_summary_persisted_by_user": {},
    "weekly_coach_summary_message_by_user": {},
    "weekly_coach_summary_qa_inventory_by_range": {},
    "weekly_coach_summary_timing_by_user": {},
    "weekly_coach_summary_provider_preview_by_range": {},
    "runtime_db_diagnostics": None,
    "developer_mode_latency_timing": {},
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


def request_main_navigation_page(page: str) -> None:
    """Request a top-level navigation change for the next Streamlit rerun."""

    st.session_state.main_navigation_page_override = page


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
    st.session_state.workout_plan_preview_by_user = {}
    st.session_state.main_navigation_page_override = None
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
    st.session_state.workout_daily_state_response = None
    st.session_state.workout_daily_state_message = None


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
        "Demo user",
        options=list(USER_OPTIONS.keys()),
        index=list(USER_OPTIONS.keys()).index("QA 102 — Well-recovered baseline"),
        help="QA 102 is the primary portfolio screenshot user.",
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


def clear_workout_transient_state_for_daily_lifecycle() -> None:
    st.session_state.selected_workout_plan_response = None
    st.session_state.started_workout_plan_response = None
    st.session_state.completed_workout_plan_response = None
    st.session_state.visible_substitution_candidates = []
    st.session_state.applied_substitution_responses = {}
    st.session_state.substitution_apply_message = None
    st.session_state.substitution_apply_error = None
    st.session_state.substitution_apply_error_detail = None
    st.session_state.substitution_flow_ready_to_do_workout = False
    st.session_state.actual_set_logging_message = None
    st.session_state.actual_set_editing_message = None
    st.session_state.actual_set_editing_error = None
    st.session_state.actual_set_edit_response = None


def apply_workout_daily_state_response(daily_state_response: dict | None) -> None:
    if not daily_state_response:
        return

    st.session_state.workout_daily_state_response = daily_state_response
    daily_state = daily_state_response.get("workout_daily_state") or {}

    if daily_state.get("stale_state_detected"):
        clear_workout_transient_state_for_daily_lifecycle()
        st.session_state.workout_daily_state_message = (
            daily_state.get("user_safe_message")
            or "An unfinished workout from a previous day was cleared so you can start fresh today."
        )


def get_active_plan_response(user_id: int) -> dict | None:
    try:
        daily_state_response = api_get(f"/workout-plans/current/{user_id}")
    except requests.RequestException:
        daily_state_response = None

    if daily_state_response:
        apply_workout_daily_state_response(daily_state_response)
        current_execution_state = daily_state_response.get("current_execution_state")
        if current_execution_state:
            workout_plan_instance = (
                current_execution_state.get("workout_plan_instance") or {}
            )
            status = workout_plan_instance.get("status")
            if status == "selected":
                st.session_state.selected_workout_plan_response = (
                    current_execution_state
                )
                st.session_state.started_workout_plan_response = None
            elif status in {"started", "in_progress", "completed"}:
                st.session_state.started_workout_plan_response = current_execution_state
                st.session_state.selected_workout_plan_response = None
            return current_execution_state

        clear_workout_transient_state_for_daily_lifecycle()
        return None

    active_response = (
        st.session_state.started_workout_plan_response
        or st.session_state.selected_workout_plan_response
    )

    if active_response:
        return active_response

    return None


def has_current_workout_selection(active_plan_response: dict | None) -> bool:
    """Return true only when today's daily state has a selected/active workout."""

    daily_state_response = st.session_state.get("workout_daily_state_response") or {}
    daily_state = daily_state_response.get("workout_daily_state") or {}
    daily_state_name = str(daily_state.get("state") or "").strip().lower()

    if daily_state_name in {"selected_today", "active_today", "completed_today"}:
        return bool(active_plan_response)

    if daily_state_name in {
        "expired_uncompleted_prior",
        "no_workout_today",
        "none",
    }:
        return False

    return bool(active_plan_response)


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


WORKOUT_SIZE_OPTION_LABELS = {
    "quick": "Quick — 3 to 4 exercises",
    "standard": "Standard — 5 exercises",
    "full": "Full — 6 to 7 exercises",
}


def workout_size_query(workout_size_preference: str | None) -> str:
    normalized = (workout_size_preference or "standard").strip().lower()
    if normalized not in WORKOUT_SIZE_OPTION_LABELS:
        normalized = "standard"
    return f"workout_size_preference={normalized}"


def render_workout_size_preference_control(context_key: str) -> str:
    options = list(WORKOUT_SIZE_OPTION_LABELS)
    selected = st.radio(
        "Workout size",
        options=options,
        index=(
            options.index(st.session_state.get("workout_size_preference", "standard"))
            if st.session_state.get("workout_size_preference", "standard") in options
            else options.index("standard")
        ),
        format_func=lambda value: WORKOUT_SIZE_OPTION_LABELS[value],
        horizontal=True,
        key=f"workout_size_preference_{context_key}",
    )
    st.session_state.workout_size_preference = selected
    st.caption(
        "Pick the session size. Recovery and equipment rules still apply, "
        "so the coach may shorten the workout when needed."
    )
    return selected


def workout_count_reason_from_payload(
    workout_plan_data: dict,
    approved_workout_plan: dict,
) -> str | None:
    count_payload = workout_plan_data.get("workout_exercise_count") or {}
    return approved_workout_plan.get("exercise_count_user_reason") or count_payload.get(
        "user_safe_reason"
    )


def normalized_workout_size_preference(workout_size_preference: str | None) -> str:
    normalized_size = (workout_size_preference or "standard").strip().lower()
    if normalized_size not in WORKOUT_SIZE_OPTION_LABELS:
        return "standard"
    return normalized_size


def workout_preview_base_key(
    user_id: int,
    workout_size_preference: str | None,
) -> str:
    normalized_size = normalized_workout_size_preference(workout_size_preference)
    return f"{user_id}:{normalized_size}"


def workout_preview_cache_key(
    user_id: int,
    workout_size_preference: str | None,
    preview_variation_index: int = 0,
) -> str:
    base_key = workout_preview_base_key(user_id, workout_size_preference)
    return f"{base_key}:variation:{max(0, int(preview_variation_index))}"


def clear_workout_preview_cache(user_id: int | None = None) -> None:
    cache = st.session_state.get("workout_plan_preview_by_user", {})
    if user_id is None:
        st.session_state.workout_plan_preview_by_user = {}
        return

    prefix = f"{user_id}:"
    st.session_state.workout_plan_preview_by_user = {
        key: value for key, value in cache.items() if not str(key).startswith(prefix)
    }


def get_workout_preview_variation_index(
    user_id: int, workout_size_preference: str | None
) -> int:
    variation_by_key = st.session_state.setdefault(
        "workout_plan_preview_variation_index_by_user", {}
    )
    base_key = workout_preview_base_key(user_id, workout_size_preference)
    return int(variation_by_key.get(base_key, 0))


def bump_workout_preview_variation_index(
    user_id: int, workout_size_preference: str | None
) -> int:
    variation_by_key = st.session_state.setdefault(
        "workout_plan_preview_variation_index_by_user", {}
    )
    base_key = workout_preview_base_key(user_id, workout_size_preference)
    next_index = int(variation_by_key.get(base_key, 0)) + 1
    variation_by_key[base_key] = next_index
    return next_index


def get_stable_workout_plan_preview(
    user_id: int,
    workout_size_preference: str | None,
    force_refresh: bool = False,
) -> dict:
    """Return a stable preview until the user explicitly requests variation."""

    cache = st.session_state.setdefault("workout_plan_preview_by_user", {})
    preview_variation_index = (
        bump_workout_preview_variation_index(user_id, workout_size_preference)
        if force_refresh
        else get_workout_preview_variation_index(user_id, workout_size_preference)
    )
    cache_key = workout_preview_cache_key(
        user_id, workout_size_preference, preview_variation_index
    )

    if not force_refresh and cache_key in cache:
        cached_preview = cache[cache_key]
        if isinstance(cached_preview, dict):
            return cached_preview

    query = workout_size_query(workout_size_preference)
    query = f"{query}&preview_variation_index={preview_variation_index}"
    workout_plan_data = api_get(f"/workout-plans/preview/{user_id}?{query}")
    if workout_plan_data.get("success"):
        cache[cache_key] = workout_plan_data
    return workout_plan_data


def select_today_workout(
    user_id: int,
    button_key: str,
    workout_size_preference: str | None = None,
    approved_workout_plan: dict | None = None,
) -> None:
    if st.button("Select This Workout", key=button_key, type="primary"):
        try:
            if approved_workout_plan:
                select_response = api_post(
                    f"/workout-plans/{user_id}/select-preview",
                    {"approved_workout_plan": approved_workout_plan},
                )
            else:
                query = workout_size_query(workout_size_preference)
                select_response = api_post(f"/workout-plans/{user_id}/select?{query}")
        except requests.RequestException as exc:
            st.session_state.workout_plan_action_error = (
                f"Workout plan selection failed: {extract_api_error_message(exc)}"
            )
            st.rerun()

        if select_response.get("success"):
            st.session_state.selected_workout_plan_response = select_response
            st.session_state.started_workout_plan_response = None
            st.session_state.workout_daily_state_response = None
            st.session_state.workout_daily_state_message = None
            st.session_state.workout_plan_action_error = None
            # Keep the visible preview cache intact after selection. Clearing it here
            # makes the next rerun load a fresh preview, which looks like the select
            # action regenerated or swapped the exercises the user just chose.
            st.session_state.actual_set_logging_message = None
            st.session_state.completed_workout_plan_response = None
            st.session_state.workout_completion_message = None
            st.session_state.workout_completion_error = None
            st.session_state.visible_substitution_candidates = []
            st.session_state.applied_substitution_responses = {}
            st.session_state.substitution_apply_message = None
            st.session_state.substitution_apply_error = None
            st.session_state.substitution_flow_ready_to_do_workout = False
            request_workout_flow_step("2. Do Workout")
            st.success("Workout plan selected. Opening the active workout.")
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
            st.session_state.workout_plan_preview_by_user = {}
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


DAILY_NEXT_ACTION_WORKFLOW_LABELS = {
    "today_recovery_checkin": "Today → Recovery Check-In",
    "today_recovery_aware_workout": "Today → Today’s Workout",
    "nutrition_quick_log": "Nutrition → Quick Log Food",
    "nutrition_target_vs_actual": "Nutrition → Target vs Actual",
    "workout_preview": "Workout → Preview / Start Workout",
    "reports_guidance": "Reports → Full Report Guidance",
}

DAILY_NEXT_ACTION_SEVERITY_LABELS = {
    "info": "Next step",
    "warning": "Recovery priority",
    "success": "Ready when you are",
}


DAILY_COACH_NARRATIVE_LANES = {
    "deterministic": {
        "label": "Deterministic fallback",
        "provider": "deterministic",
        "model": None,
        "timeout_seconds": 0,
        "request_timeout": 120,
        "description": "Immediate backend fallback. No provider call is made.",
    },
    "qwen3_8b_fast": {
        "label": "Fast preview: qwen3:8b",
        "provider": "direct_ollama",
        "model": "qwen3:8b",
        "timeout_seconds": 180,
        "request_timeout": 210,
        "description": "Lower-latency developer preview lane. Probe only; not bridge approval eligible.",
    },
    "qwen3_32b_premium": {
        "label": "Premium preview: qwen3:32b",
        "provider": "direct_ollama",
        "model": "qwen3:32b",
        "timeout_seconds": 420,
        "request_timeout": 450,
        "description": "Higher-quality slow/manual preview lane. Probe only; not bridge approval eligible.",
        "warning": (
            "Premium preview may take several minutes. The deterministic fallback "
            "remains available while generation runs."
        ),
    },
    "qwen25_3b_baseline": {
        "label": "Baseline/regression: qwen2.5:3b",
        "provider": "direct_ollama",
        "model": "qwen2.5:3b",
        "timeout_seconds": 180,
        "request_timeout": 210,
        "description": "Small-model validator and same-session bridge baseline lane.",
    },
}


def daily_coach_narrative_lane_labels() -> list[str]:
    return [str(lane["label"]) for lane in DAILY_COACH_NARRATIVE_LANES.values()]


def daily_coach_narrative_lane_key_from_label(label: str) -> str:
    for lane_key, lane in DAILY_COACH_NARRATIVE_LANES.items():
        if lane["label"] == label:
            return lane_key

    return "deterministic"


def build_daily_coach_narrative_preview_params(
    lane_key: str,
    *,
    target_date: str | None = None,
    qa_preview: bool = False,
    lookback_days: int = 1,
) -> dict[str, object]:
    lane = DAILY_COACH_NARRATIVE_LANES.get(
        lane_key, DAILY_COACH_NARRATIVE_LANES["deterministic"]
    )
    params: dict[str, object] = {"provider": lane["provider"]}

    if lane.get("model"):
        params["model"] = lane["model"]

    timeout_seconds = lane.get("timeout_seconds")
    if timeout_seconds:
        params["timeout_seconds"] = timeout_seconds
    if target_date:
        params["date"] = target_date
    if qa_preview:
        params["qa_preview"] = True
        params["lookback_days"] = max(1, min(int(lookback_days or 1), 7))

    return params


def daily_coach_narrative_request_timeout(lane_key: str) -> float:
    lane = DAILY_COACH_NARRATIVE_LANES.get(
        lane_key, DAILY_COACH_NARRATIVE_LANES["deterministic"]
    )
    return float(lane.get("request_timeout") or 120)


def daily_coach_narrative_lane_description(lane_key: str) -> str:
    lane = DAILY_COACH_NARRATIVE_LANES.get(
        lane_key, DAILY_COACH_NARRATIVE_LANES["deterministic"]
    )
    return str(lane.get("description") or "Developer-only preview lane.")


def daily_coach_narrative_lane_warning(lane_key: str) -> str | None:
    lane = DAILY_COACH_NARRATIVE_LANES.get(
        lane_key, DAILY_COACH_NARRATIVE_LANES["deterministic"]
    )
    warning = lane.get("warning")
    return str(warning) if warning else None


def daily_coach_narrative_fallback_display(preview: dict) -> str:
    return (
        preview.get("deterministic_fallback_note")
        or "Deterministic fallback narrative is not available yet."
    )


def daily_coach_narrative_approved_display(preview: dict) -> dict:
    narrative = preview.get("approved_narrative")
    return narrative if isinstance(narrative, dict) else {}


def build_daily_coach_session_approval_context(
    user_id: int, today_card_date: str | None = None
) -> dict[str, object] | None:
    """Build the deterministic active context used to invalidate session approval."""

    try:
        response = api_get(f"/daily-coach/{user_id}/next-action", request_timeout=30)
    except requests.RequestException:
        return None

    action = response.get("daily_next_action") or {}
    next_action_id = action.get("action_id")
    workflow_target = action.get("workflow_target")
    if not next_action_id or not workflow_target:
        return None

    return {
        "user_id": user_id,
        "date": today_card_date or datetime.today().date().isoformat(),
        "next_action_id": next_action_id,
        "workflow_target": workflow_target,
    }


def daily_coach_session_approved_card_text(record: dict) -> str:
    return (
        record.get("coach_note")
        or "Session-approved coach note is not available for this context."
    )


def fetch_daily_coach_narrative_preview(
    user_id: int,
    lane_key: str = "deterministic",
    *,
    target_date: str | None = None,
    qa_preview: bool = False,
    lookback_days: int = 1,
) -> dict | None:
    params = build_daily_coach_narrative_preview_params(
        lane_key,
        target_date=target_date,
        qa_preview=qa_preview,
        lookback_days=lookback_days,
    )
    errors = st.session_state.daily_coach_narrative_preview_error_by_user

    try:
        response = api_get(
            f"/daily-coach/{user_id}/narrative-preview/debug",
            params=params,
            request_timeout=daily_coach_narrative_request_timeout(lane_key),
        )
    except requests.RequestException as exc:
        errors[user_id] = extract_api_error_message(exc)
        return None

    errors.pop(user_id, None)
    return response.get("daily_coach_narrative_preview") or {}


def daily_coach_preview_table_value(value: object) -> str:
    """Return an Arrow-safe string for mixed Developer Mode diagnostics."""

    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return ""
    if isinstance(value, list | tuple | set):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return ", ".join(f"{key}: {item}" for key, item in value.items())
    return str(value)


def render_daily_coach_narrative_preview_status(preview: dict) -> None:
    status_rows = [
        {"Status": "Provider attempted", "Value": preview.get("provider_attempted")},
        {"Status": "Selected provider", "Value": preview.get("selected_provider")},
        {"Status": "Selected model", "Value": preview.get("selected_model")},
        {"Status": "Parse success", "Value": preview.get("parse_success")},
        {"Status": "Validation success", "Value": preview.get("validation_success")},
        {"Status": "Fallback used", "Value": preview.get("fallback_used")},
        {"Status": "Fallback reason", "Value": preview.get("fallback_reason")},
        {"Status": "Latency ms", "Value": preview.get("latency_ms")},
    ]
    status_df = pd.DataFrame(status_rows)
    status_df["Value"] = status_df["Value"].map(daily_coach_preview_table_value)
    st.dataframe(status_df, width="stretch", hide_index=True)

    developer_diagnostics = preview.get("developer_diagnostics") or {}
    if developer_diagnostics:
        with st.expander("Sanitized preview diagnostics", expanded=False):
            diagnostic_rows = [
                {"Diagnostic": key, "Value": daily_coach_preview_table_value(value)}
                for key, value in developer_diagnostics.items()
            ]
            st.dataframe(
                pd.DataFrame(diagnostic_rows),
                width="stretch",
                hide_index=True,
            )


def render_daily_coach_narrative_context_summary(preview: dict) -> None:
    context_summary = preview.get("context_summary") or {}
    summary_rows = [
        {
            "Context": "Approved facts",
            "Count": context_summary.get("approved_facts_count"),
            "Summary": ", ".join(context_summary.get("approved_facts_summary") or []),
        },
        {
            "Context": "Approved limitations",
            "Count": context_summary.get("approved_limitations_count"),
            "Summary": ", ".join(
                context_summary.get("approved_limitations_summary") or []
            ),
        },
        {
            "Context": "Forbidden claim categories",
            "Count": context_summary.get("forbidden_claim_categories_count"),
            "Summary": ", ".join(
                context_summary.get("forbidden_claim_categories_summary") or []
            ),
        },
    ]
    metadata_rows = [
        ("Selected date", context_summary.get("selected_date")),
        ("Start date", context_summary.get("start_date")),
        ("End date", context_summary.get("end_date")),
        ("Lookback days", context_summary.get("lookback_days")),
        ("Data quality label", context_summary.get("data_quality_label")),
        (
            "Weekly inventory label",
            context_summary.get("weekly_inventory_data_quality_label"),
        ),
        ("Recommended test label", context_summary.get("recommended_test_label")),
        ("Richness score", context_summary.get("richness_score")),
        ("Domains present", context_summary.get("domains_present_count")),
        ("Recovery entries", context_summary.get("recovery_checkins_count")),
        ("Nutrition entries", context_summary.get("nutrition_entries_count")),
        ("Workout sessions", context_summary.get("workout_sessions_count")),
        ("Planned workouts", context_summary.get("planned_workouts_count")),
        ("Planned exercises", context_summary.get("planned_exercises_count")),
        ("Actual sets", context_summary.get("actual_sets_count")),
        ("Next-action reason", context_summary.get("next_action_reason")),
        ("Reason codes", ", ".join(context_summary.get("reason_codes") or [])),
    ]
    for label, value in metadata_rows:
        if value not in (None, ""):
            summary_rows.append(
                {
                    "Context": label,
                    "Count": "",
                    "Summary": daily_coach_preview_table_value(value),
                }
            )
    st.dataframe(pd.DataFrame(summary_rows), width="stretch", hide_index=True)


DAILY_COACH_ASYNC_PERSISTENCE_JOB_DISPLAY_FIELDS = (
    "job_id",
    "user_id",
    "target_date",
    "workflow_target",
    "next_action_id",
    "status",
    "context_hash",
    "context_version",
    "prompt_contract_version",
    "validator_version",
    "created_at",
    "updated_at",
    "started_at",
    "completed_at",
    "expires_at",
    "stale_after",
    "stale",
    "expired",
    "displayable",
    "public_safe",
    "fallback_used",
    "fallback_reason",
    "provider_attempted",
    "provider_name",
    "provider_model",
    "parse_status",
    "validation_status",
    "final_narrative_source",
    "sanitized_error_category",
    "raw_output_length",
    "raw_output_preview_truncated",
    "markdown_wrapper_detected",
)

DAILY_COACH_ASYNC_PERSISTENCE_NARRATIVE_DISPLAY_FIELDS = (
    "narrative_id",
    "job_id",
    "user_id",
    "target_date",
    "context_hash",
    "context_version",
    "approved_text",
    "approved_narrative_json",
    "reason_codes_json",
    "action_refs_json",
    "validator_version",
    "prompt_contract_version",
    "created_at",
    "expires_at",
    "stale",
    "expired",
    "displayable",
    "public_safe",
    "final_narrative_source",
)

DAILY_COACH_ASYNC_PERSISTENCE_FORBIDDEN_UI_FIELDS = frozenset(
    {
        "raw_provider_output",
        "provider_raw_output",
        "rejected_provider_output",
        "raw_model_output",
        "raw_llm_output",
        "full_prompt",
        "prompt_text",
        "raw_prompt",
        "raw_context",
        "raw_database_rows",
        "raw_user_notes",
        "scratchpad",
        "chain_of_thought",
        "validation_bypass",
        "secrets",
        "environment_values",
        "stack_trace",
        "traceback",
    }
)


def daily_coach_async_persistence_table_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def daily_coach_async_persistence_forbidden_fields_present(
    payload: dict[str, object],
) -> list[str]:
    return sorted(
        field_name
        for field_name in payload
        if field_name.lower() in DAILY_COACH_ASYNC_PERSISTENCE_FORBIDDEN_UI_FIELDS
    )


def daily_coach_async_persistence_safe_job_payload(job: object) -> dict[str, object]:
    payload = job.to_dict() if hasattr(job, "to_dict") else dict(job or {})
    return {
        field_name: payload.get(field_name)
        for field_name in DAILY_COACH_ASYNC_PERSISTENCE_JOB_DISPLAY_FIELDS
    }


def daily_coach_async_persistence_safe_narrative_payload(
    narrative: object,
) -> dict[str, object] | None:
    payload = (
        narrative.to_dict() if hasattr(narrative, "to_dict") else dict(narrative or {})
    )
    if not payload.get("displayable") or not payload.get("public_safe"):
        return None
    return {
        field_name: payload.get(field_name)
        for field_name in DAILY_COACH_ASYNC_PERSISTENCE_NARRATIVE_DISPLAY_FIELDS
    }


def render_daily_coach_async_persistence_table(payload: dict[str, object]) -> None:
    unsafe_fields = daily_coach_async_persistence_forbidden_fields_present(payload)
    if unsafe_fields:
        st.error(
            "Developer persistence inspection blocked unsafe field(s): "
            + ", ".join(unsafe_fields)
        )
        return

    rows = [
        {"Field": field_name, "Value": daily_coach_async_persistence_table_value(value)}
        for field_name, value in payload.items()
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def fetch_daily_coach_async_developer_latest(
    user_id: int,
    *,
    target_date: str | None = None,
    provider: str = "deterministic",
    model: str = "deterministic",
) -> dict | None:
    errors = st.session_state.daily_coach_async_developer_error_by_user
    params = {
        "provider": provider,
        "model": model,
    }
    if target_date:
        params["target_date"] = target_date

    try:
        response = api_get(
            f"/daily-coach/{user_id}/async-narrative/developer/jobs/latest",
            params=params,
            request_timeout=30,
        )
    except requests.RequestException as exc:
        errors[user_id] = extract_api_error_message(exc)
        return None

    errors.pop(user_id, None)
    return response


def create_daily_coach_async_developer_job(
    user_id: int,
    *,
    target_date: str | None = None,
    provider: str = "deterministic",
    model: str = "deterministic",
) -> dict | None:
    errors = st.session_state.daily_coach_async_developer_error_by_user
    params = {
        "provider": provider,
        "model": model,
        "expires_seconds": 3600,
    }
    if target_date:
        params["target_date"] = target_date

    try:
        response = requests.post(
            f"{API_BASE_URL}/daily-coach/{user_id}/async-narrative/developer/jobs",
            params=params,
            json={},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        errors[user_id] = extract_api_error_message(exc)
        return None

    errors.pop(user_id, None)
    return response.json()


def simulate_daily_coach_async_developer_job(
    user_id: int,
    job_id: str,
    *,
    action: str,
    target_date: str | None = None,
    provider: str = "deterministic",
    model: str = "deterministic",
) -> dict | None:
    errors = st.session_state.daily_coach_async_developer_error_by_user
    params = {
        "provider": provider,
        "model": model,
    }
    if target_date:
        params["target_date"] = target_date

    try:
        response = requests.post(
            f"{API_BASE_URL}/daily-coach/{user_id}"
            f"/async-narrative/developer/jobs/{job_id}/simulate",
            params=params,
            json={"action": action},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        errors[user_id] = extract_api_error_message(exc)
        return None

    errors.pop(user_id, None)
    return response.json()


def render_daily_coach_async_developer_lifecycle_panel(user_id: int) -> None:
    with st.expander(
        "Developer Prototype: Async Daily Coach Lifecycle",
        expanded=False,
    ):
        st.caption(
            "Developer-only lifecycle harness around the async service shell. "
            "No provider is called, no worker runs, no job is persisted, and "
            "normal Today behavior is unchanged."
        )

        target_date = st.text_input(
            "Async prototype target date",
            value=datetime.today().date().isoformat(),
            key=f"daily_coach_async_developer_target_date_{user_id}",
            help="Manual Developer Mode context identity date only.",
        )
        provider = st.text_input(
            "Requested provider metadata",
            value="deterministic",
            key=f"daily_coach_async_developer_provider_{user_id}",
            help="Metadata only for this prototype. No provider call is made.",
        )
        model = st.text_input(
            "Requested model metadata",
            value="deterministic",
            key=f"daily_coach_async_developer_model_{user_id}",
            help="Metadata only for lane/context inspection. No model call is made.",
        )

        first_col, second_col = st.columns(2)
        with first_col:
            if st.button(
                "Create async job shell",
                key=f"create_daily_coach_async_developer_job_{user_id}",
            ):
                response = create_daily_coach_async_developer_job(
                    user_id,
                    target_date=target_date,
                    provider=provider,
                    model=model,
                )
                if response:
                    st.session_state.daily_coach_async_developer_job_by_user[
                        user_id
                    ] = response
        with second_col:
            if st.button(
                "Inspect latest async job shell",
                key=f"inspect_daily_coach_async_developer_job_{user_id}",
            ):
                response = fetch_daily_coach_async_developer_latest(
                    user_id,
                    target_date=target_date,
                    provider=provider,
                    model=model,
                )
                if response:
                    st.session_state.daily_coach_async_developer_job_by_user[
                        user_id
                    ] = response

        error = st.session_state.daily_coach_async_developer_error_by_user.get(user_id)
        if error:
            st.warning(f"Async lifecycle prototype call failed safely: {error}")

        response = st.session_state.daily_coach_async_developer_job_by_user.get(user_id)
        if not response:
            return

        job = response.get("async_narrative_job") or {}
        display_state = response.get("display_state") or "fallback_available"
        st.write(f"**Display state:** {display_state}")
        st.write(
            "**Boundary:** developer-only, provider execution "
            f"{response.get('provider_execution')}, persistence {response.get('persistence')}."
        )

        if job:
            status_rows = [
                {"Field": "job_id", "Value": job.get("job_id")},
                {"Field": "status", "Value": job.get("status")},
                {"Field": "target_date", "Value": job.get("target_date")},
                {"Field": "next_action_id", "Value": job.get("next_action_id")},
                {"Field": "workflow_target", "Value": job.get("workflow_target")},
                {"Field": "context_hash", "Value": job.get("context_hash")},
                {"Field": "model_lane", "Value": job.get("model_lane")},
                {"Field": "bridge_approved", "Value": job.get("bridge_approved")},
                {"Field": "approval_eligible", "Value": job.get("approval_eligible")},
                {"Field": "expires_at", "Value": job.get("expires_at")},
            ]
            status_df = pd.DataFrame(status_rows)
            status_df["Value"] = status_df["Value"].map(daily_coach_preview_table_value)
            st.dataframe(status_df, width="stretch", hide_index=True)

            simulation_action = st.selectbox(
                "Safe lifecycle simulation",
                options=["approve_deterministic", "mark_stale", "expire"],
                key=f"daily_coach_async_developer_simulation_{user_id}",
                help="Manual Developer Mode simulation only. This is not provider output.",
            )
            if st.button(
                "Run lifecycle simulation",
                key=f"simulate_daily_coach_async_developer_job_{user_id}",
            ):
                simulated = simulate_daily_coach_async_developer_job(
                    user_id,
                    str(job.get("job_id")),
                    action=simulation_action,
                    target_date=target_date,
                    provider=provider,
                    model=model,
                )
                if simulated:
                    st.session_state.daily_coach_async_developer_job_by_user[
                        user_id
                    ] = simulated

        with st.expander("Sanitized async lifecycle payload", expanded=False):
            st.json(response)


def render_daily_coach_async_approved_preview_bridge(user_id: int) -> None:
    """Render an optional secondary Today preview from approved persistence only."""

    target_date = datetime.today().date().isoformat()
    config = resolve_daily_coach_async_approved_preview_config()
    try:
        preview = build_daily_coach_async_approved_preview(
            user_id=user_id,
            target_date=target_date,
        )
    except Exception:
        if st.session_state.get("developer_mode", False):
            with st.expander(
                "Developer details: approved preview bridge", expanded=False
            ):
                st.write("Approved preview bridge failed safely.")
                st.write(
                    "Sanitized failure only; stack traces, raw provider output, rejected output, full prompts, raw context, and scratchpad text are not displayed."
                )
        return

    normal_preview = preview.to_normal_ui_dict()
    if (
        normal_preview.get("enabled")
        and normal_preview.get("eligible")
        and normal_preview.get("preview_text")
    ):
        st.markdown(
            portfolio_card_html(
                "Daily Coach Narrative Preview",
                "AI-assisted coach preview",
                str(normal_preview.get("preview_text")),
                [
                    portfolio_chip("Secondary preview", "purple"),
                    portfolio_chip("Read-only persisted", "green"),
                ],
                "portfolio-card-purple",
            ),
            unsafe_allow_html=True,
        )
        st.caption(
            "Preview is secondary. Deterministic Daily Next Action remains primary."
        )
    elif normal_preview.get("enabled") and normal_preview.get("safe_user_message"):
        st.info(str(normal_preview.get("safe_user_message")))

    if st.session_state.get("developer_mode", False):
        with st.expander("Developer details: approved preview bridge", expanded=False):
            st.caption(
                "Developer Mode-only sanitized diagnostics. Today preview reads only "
                "persisted approved narratives and never calls a provider, creates "
                "jobs, queues work, schedules work, or polls in the render path."
            )
            render_daily_coach_async_persistence_table(config.to_dict())
            diagnostics_payload = preview.to_dict()
            render_daily_coach_async_persistence_table(
                {
                    "enabled": diagnostics_payload.get("enabled"),
                    "eligible": diagnostics_payload.get("eligible"),
                    "fallback_used": diagnostics_payload.get("fallback_used"),
                    "fallback_reason": diagnostics_payload.get("fallback_reason"),
                    "gate_status": diagnostics_payload.get("gate_status"),
                    "safe_user_message": diagnostics_payload.get("safe_user_message"),
                }
            )
            diagnostics = diagnostics_payload.get("developer_diagnostics") or {}
            if diagnostics:
                render_daily_coach_async_persistence_table(diagnostics)
            st.caption(
                "Normal UI does not show provider/model diagnostics, raw provider output, "
                "rejected output, full prompt, raw context, scratchpad, stack traces, or secrets."
            )


def render_daily_coach_async_provider_runtime_panel(user_id: int) -> None:
    if not st.session_state.get("developer_mode", False):
        return

    with st.expander(
        "Developer Prototype: Daily Coach Async Provider Runtime",
        expanded=False,
    ):
        st.caption(
            "Developer Mode-only manual provider prototype. It never runs on page load, "
            "never changes normal Today behavior, and never displays raw provider output. "
            "Rejected provider output, full prompts, raw context, and scratchpad text are never shown."
        )

        config = resolve_daily_coach_async_provider_runtime_config()
        config_payload = config.to_dict()
        st.write("**Runtime configuration**")
        render_daily_coach_async_persistence_table(config_payload)

        if not config.enabled:
            st.info(
                "Provider runtime is disabled. Set "
                "DAILY_COACH_ASYNC_PROVIDER_RUNTIME_ENABLED=true for manual "
                "Developer Mode provider QA."
            )

        target_date = st.text_input(
            "Provider runtime target date",
            value=datetime.today().date().isoformat(),
            key=f"daily_coach_provider_runtime_target_date_{user_id}",
            help="Used only when creating a persisted Developer Mode provider job.",
        )

        first_col, second_col = st.columns([1, 1])
        with first_col:
            if st.button(
                "Create persisted provider job",
                key=f"daily_coach_provider_runtime_create_job_{user_id}",
            ):
                try:
                    job = create_developer_mode_provider_runtime_job(
                        user_id=user_id,
                        target_date=target_date or None,
                    )
                    st.session_state.daily_coach_async_provider_runtime_job_id_by_user[
                        user_id
                    ] = job.job_id
                    st.session_state.daily_coach_async_provider_runtime_result_by_user[
                        user_id
                    ] = {
                        "created_job": daily_coach_async_persistence_safe_job_payload(
                            job
                        ),
                        "provider_runtime": "not_attempted",
                    }
                    st.session_state.daily_coach_async_provider_runtime_error_by_user.pop(
                        user_id,
                        None,
                    )
                except Exception:
                    st.session_state.daily_coach_async_provider_runtime_error_by_user[
                        user_id
                    ] = "sanitized_create_job_failure"
        stored_job_id = (
            st.session_state.daily_coach_async_provider_runtime_job_id_by_user.get(
                user_id,
                "",
            )
        )
        job_id = st.text_input(
            "Provider runtime job_id",
            value=stored_job_id,
            key=f"daily_coach_provider_runtime_job_id_{user_id}",
            help="Manual trigger requires an existing persisted Daily Coach async job_id.",
        ).strip()
        if job_id:
            st.session_state.daily_coach_async_provider_runtime_job_id_by_user[
                user_id
            ] = job_id

        with second_col:
            if st.button(
                "Run manual provider attempt",
                key=f"daily_coach_provider_runtime_run_{user_id}",
            ):
                if not job_id:
                    st.session_state.daily_coach_async_provider_runtime_error_by_user[
                        user_id
                    ] = "A persisted job_id is required before provider runtime can run."
                else:
                    try:
                        result = run_daily_coach_async_provider_runtime_prototype(
                            job_id
                        )
                        st.session_state.daily_coach_async_provider_runtime_result_by_user[
                            user_id
                        ] = result.to_dict()
                        st.session_state.daily_coach_async_provider_runtime_error_by_user.pop(
                            user_id,
                            None,
                        )
                    except Exception:
                        st.session_state.daily_coach_async_provider_runtime_error_by_user[
                            user_id
                        ] = "sanitized_provider_runtime_failure"

        error = st.session_state.daily_coach_async_provider_runtime_error_by_user.get(
            user_id
        )
        if error:
            st.warning(f"Provider runtime prototype failed safely: {error}")
            st.caption(
                "Sanitized Developer Mode failure only; raw provider output, rejected "
                "output, prompts, raw context, scratchpad, stack traces, and secrets "
                "are not displayed."
            )

        result_payload = (
            st.session_state.daily_coach_async_provider_runtime_result_by_user.get(
                user_id
            )
        )
        if result_payload:
            st.write("**Sanitized provider runtime result**")
            render_daily_coach_async_persistence_table(result_payload)
            with st.expander("Sanitized provider runtime JSON", expanded=False):
                st.json(result_payload)

        st.caption(
            "Boundary: manual Developer Mode action only. No qwen3/qwen3:32b, "
            "no worker/queue/scheduler, no normal Today provider call, and no "
            "public async narrative display."
        )


def render_daily_coach_async_persistence_inspection_panel(user_id: int) -> None:
    if not st.session_state.get("developer_mode", False):
        return

    with st.expander(
        "Developer Persistence Inspection: Daily Coach Async",
        expanded=False,
    ):
        st.caption(
            "Developer Mode-only read-only inspection of persisted Daily Coach "
            "async jobs and approved narratives. No provider is called, no job "
            "is created, and normal Today behavior is unchanged."
        )

        target_date = st.text_input(
            "Persistence inspection target date",
            value=datetime.today().date().isoformat(),
            key=f"daily_coach_persistence_inspection_target_date_{user_id}",
            help="Read-only Developer Mode filter for persisted async records.",
        )
        job_id = st.text_input(
            "Inspect specific job_id",
            value="",
            key=f"daily_coach_persistence_inspection_job_id_{user_id}",
            help="Optional read-only lookup by persisted async job_id.",
        ).strip()

        try:
            latest_jobs = get_latest_async_jobs(
                user_id=user_id,
                target_date=target_date or None,
                limit=5,
            )
        except DailyCoachAsyncPersistenceError as exc:
            st.warning(f"Persistence inspection failed safely: {exc}")
            return

        st.write("**Latest persisted async jobs**")
        if latest_jobs:
            latest_job_rows = [
                daily_coach_async_persistence_safe_job_payload(job)
                for job in latest_jobs
            ]
            compact_fields = [
                "job_id",
                "target_date",
                "status",
                "stale",
                "expired",
                "displayable",
                "public_safe",
                "fallback_used",
                "provider_attempted",
                "parse_status",
                "validation_status",
                "final_narrative_source",
            ]
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            field_name: row.get(field_name)
                            for field_name in compact_fields
                        }
                        for row in latest_job_rows
                    ]
                ),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No persisted Daily Coach async jobs found for this user/date.")

        if job_id:
            st.write("**Specific persisted async job**")
            job = get_async_job(job_id)
            if job is None:
                st.info("No persisted Daily Coach async job found for that job_id.")
            else:
                render_daily_coach_async_persistence_table(
                    daily_coach_async_persistence_safe_job_payload(job)
                )

                narrative = get_approved_narrative_by_job_id(job_id)
                safe_narrative = (
                    daily_coach_async_persistence_safe_narrative_payload(narrative)
                    if narrative
                    else None
                )
                st.write("**Approved narrative for job_id**")
                if safe_narrative:
                    render_daily_coach_async_persistence_table(safe_narrative)
                elif narrative:
                    st.info(
                        "Approved narrative exists but is not displayable/public_safe, "
                        "so content is withheld."
                    )
                else:
                    st.info("No approved narrative exists for this job_id.")

        st.write("**Latest displayable approved narrative for user/date**")
        latest_narrative = get_latest_displayable_approved_narrative(
            user_id=user_id,
            target_date=target_date or None,
        )
        safe_latest_narrative = (
            daily_coach_async_persistence_safe_narrative_payload(latest_narrative)
            if latest_narrative
            else None
        )
        if safe_latest_narrative:
            render_daily_coach_async_persistence_table(safe_latest_narrative)
        else:
            st.info(
                "No displayable public-safe approved Daily Coach async narrative "
                "found for this user/date."
            )


def daily_narrative_qa_user_options() -> dict[int, str]:
    from services.weekly_coach_summary_qa_data_service import QA_USER_LABELS

    return dict(QA_USER_LABELS)


def daily_narrative_rich_day_candidates(
    *,
    user_id: int,
    start_date: str = "2026-05-31",
    end_date: str = "2026-06-06",
    top: int = 5,
) -> list[dict]:
    from services.daily_narrative_rich_day_service import (
        scan_daily_narrative_rich_days,
    )

    result = scan_daily_narrative_rich_days(
        user_id=int(user_id),
        start_date=start_date,
        end_date=end_date,
        top=top,
    )
    return [candidate.to_dict() for candidate in result.top_candidates]


def render_daily_narrative_rich_day_candidates(candidates: list[dict]) -> None:
    if not candidates:
        st.info("No Daily Narrative rich-day candidates found for this user/range.")
        return
    columns = [
        "date",
        "richness_score",
        "data_quality_label",
        "recommended_test_label",
        "recovery_checkins_count",
        "nutrition_entries_count",
        "workout_sessions_count",
        "planned_workouts_count",
        "planned_exercises_count",
        "actual_sets_count",
    ]
    st.dataframe(
        pd.DataFrame(
            [
                {column: candidate.get(column) for column in columns}
                for candidate in candidates
            ]
        ),
        width="stretch",
        hide_index=True,
    )
    best = candidates[0]
    st.caption(
        "Best rich-data candidate: "
        f"{best.get('date')} ({best.get('recommended_test_label')}, "
        f"score {best.get('richness_score')})."
    )
    with st.expander("Rich-day reason codes", expanded=False):
        for candidate in candidates:
            reason_codes = ", ".join(candidate.get("reason_codes") or [])
            st.write(
                f"- {candidate.get('date')} / {candidate.get('recommended_test_label')}: "
                f"{reason_codes}"
            )


def render_daily_narrative_voice_lab() -> None:
    """Developer Mode-only Daily Narrative copy lab.

    This panel is intentionally deterministic on render. It never calls a
    provider when the page opens or when a scenario is selected.
    """

    st.write("**Daily Narrative Voice Lab**")
    st.caption(
        "Developer Mode only. Synthetic copy fixtures and safe scenario facts. "
        "No provider call happens on page open or scenario selection."
    )
    scenarios = list_daily_narrative_voice_lab_scenarios()
    scenario_ids = [scenario.scenario_id for scenario in scenarios]
    labels = {
        scenario.scenario_id: f"{scenario.scenario_label} ({scenario.scenario_id})"
        for scenario in scenarios
    }
    selected_scenario_id = st.selectbox(
        "Voice Lab scenario",
        options=scenario_ids,
        format_func=lambda value: labels.get(value, value),
        key="daily_narrative_voice_lab_scenario",
        help="Synthetic safe scenario fixtures for copy testing. These are not real users.",
    )
    result = build_daily_narrative_voice_lab_result(selected_scenario_id)
    scenario = result.scenario

    st.write("**Scenario facts**")
    fact_rows = [
        {"Field": "Situation", "Value": scenario.situation_summary},
        {"Field": "Data quality", "Value": scenario.data_quality},
        {"Field": "Confidence", "Value": scenario.confidence},
        {
            "Field": "Domains present",
            "Value": ", ".join(scenario.domains_present) or "none",
        },
        {
            "Field": "Missing pieces",
            "Value": ", ".join(scenario.missing_domains) or "none",
        },
        {"Field": "Coaching angle", "Value": scenario.desired_coaching_angle},
    ]
    st.dataframe(pd.DataFrame(fact_rows), width="stretch", hide_index=True)
    with st.expander("Reason codes and safe aggregate facts", expanded=False):
        st.write("Reason codes:")
        st.json(list(scenario.reason_codes))
        st.write("Safe aggregate facts:")
        st.json(list(scenario.safe_aggregate_facts))
        st.write("Prohibited claims:")
        st.json(list(scenario.prohibited_claims))

    st.write("**Deterministic candidates**")
    for candidate in result.candidates:
        st.markdown(f"**{candidate.title}**")
        st.write(candidate.body)
        qa_rows = [
            {"Check": "copy_family", "Result": candidate.copy_family},
            {
                "Check": "banned_phrase_hits",
                "Result": ", ".join(candidate.banned_phrase_hits) or "none",
            },
            {
                "Check": "awkward_phrase_hits",
                "Result": ", ".join(candidate.awkward_phrase_hits) or "none",
            },
            {
                "Check": "quality_notes",
                "Result": " | ".join(candidate.quality_notes) or "none",
            },
        ]
        st.dataframe(pd.DataFrame(qa_rows), width="stretch", hide_index=True)

        with st.expander(
            f"Capture feedback for {candidate.variant_id}", expanded=False
        ):
            feedback_key = f"daily_narrative_feedback_{scenario.scenario_id}_{candidate.variant_id}"
            with st.form(feedback_key, clear_on_submit=False):
                feedback_label = st.selectbox(
                    "Feedback label",
                    options=["bad", "better", "approved"],
                    key=f"{feedback_key}_label",
                )
                rejected_phrase = st.text_input(
                    "Rejected phrase",
                    key=f"{feedback_key}_rejected_phrase",
                    help="Optional. Example: adding random data",
                )
                preferred_rewrite = st.text_area(
                    "Preferred rewrite",
                    key=f"{feedback_key}_preferred_rewrite",
                    help="Optional. Paste a better direction or exact replacement.",
                )
                user_notes = st.text_area(
                    "Notes",
                    key=f"{feedback_key}_notes",
                    help="Optional. Capture why the copy worked or failed.",
                )
                save_feedback = st.form_submit_button("Save feedback")

            if save_feedback:
                warnings = tuple(
                    list(candidate.banned_phrase_hits)
                    + list(candidate.awkward_phrase_hits)
                    + list(candidate.quality_notes)
                )
                feedback = DailyNarrativeFeedbackInput(
                    scenario_id=scenario.scenario_id,
                    scenario_label=scenario.scenario_label,
                    scenario_source="synthetic",
                    candidate_id=candidate.variant_id,
                    candidate_source="deterministic",
                    candidate_text=f"{candidate.title}\n\n{candidate.body}",
                    feedback_label=feedback_label,
                    rejected_phrase=rejected_phrase,
                    preferred_rewrite=preferred_rewrite,
                    user_notes=user_notes,
                    reason_codes=candidate.reason_codes,
                    data_quality=scenario.data_quality,
                    confidence=scenario.confidence,
                    domains_present=scenario.domains_present,
                    domains_missing=scenario.missing_domains,
                    coaching_angle=scenario.desired_coaching_angle,
                    copy_quality_warnings=warnings,
                )
                try:
                    saved = save_daily_narrative_feedback(feedback)
                except ValueError as exc:
                    st.error(f"Feedback was not saved: {exc}")
                else:
                    st.success(
                        "Feedback saved: " f"{saved.feedback_id} at {saved.created_at}"
                    )

    recent_feedback = list_daily_narrative_feedback(
        scenario_id=scenario.scenario_id, limit=5
    )
    feedback_summary = summarize_daily_narrative_feedback()
    st.write("**Recent feedback for this scenario**")
    if recent_feedback:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "created_at": item.created_at,
                        "label": item.feedback_label,
                        "candidate": item.candidate_id,
                        "rejected_phrase": item.rejected_phrase,
                        "preferred_rewrite": item.preferred_rewrite,
                    }
                    for item in recent_feedback
                ]
            ),
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption("No feedback saved for this scenario yet.")
    st.caption(
        f"Total saved Daily Narrative feedback records: {feedback_summary['count']}"
    )

    st.info(
        "Provider candidate generation is intentionally not automatic in this lab. "
        "Saving feedback does not call a provider or regenerate the candidate."
    )


def render_daily_coach_narrative_developer_panel(user_id: int) -> None:
    if not st.session_state.get("developer_mode", False):
        return

    with st.expander("Developer Preview: Daily Coach Narrative", expanded=False):
        st.caption(
            "Developer-only, manual, fallback-first preview. Provider output is "
            "shown only after backend parse and validation pass."
        )

        render_daily_narrative_voice_lab()

        st.divider()

        st.write("**Daily Narrative QA Date Range Preview / Grounding**")
        st.caption(
            "Developer Mode only. QA seeded-date preview. Normal Today Daily Narrative is unchanged."
        )
        qa_preview_enabled = st.checkbox(
            "Use seeded QA date context",
            value=True,
            key=f"daily_narrative_qa_preview_enabled_{user_id}",
            help="Uses typed QA user/date inputs and backend-owned safe aggregate context.",
        )
        qa_user_options = daily_narrative_qa_user_options()
        qa_user_ids = list(qa_user_options.keys())
        default_qa_index = (
            qa_user_ids.index(user_id)
            if user_id in qa_user_ids
            else qa_user_ids.index(102)
        )
        qa_user_id = st.selectbox(
            "Daily Narrative QA user",
            options=qa_user_ids,
            index=default_qa_index,
            format_func=lambda value: qa_user_options.get(value, str(value)),
            key=f"daily_narrative_qa_user_{user_id}",
            help="Typed QA user id; UI label text is not parsed as source of truth.",
            disabled=not qa_preview_enabled,
        )
        qa_col, lookback_col = st.columns([1, 1])
        with qa_col:
            qa_selected_date = st.date_input(
                "Daily Narrative selected date",
                value=date(2026, 6, 6),
                key=f"daily_narrative_qa_selected_date_{user_id}",
                help="Known seeded QA window recently verified: 2026-05-31 through 2026-06-06.",
                disabled=not qa_preview_enabled,
            )
        with lookback_col:
            qa_lookback_days = st.selectbox(
                "Daily Narrative lookback",
                options=[1, 3, 7],
                index=0,
                key=f"daily_narrative_qa_lookback_days_{user_id}",
                disabled=not qa_preview_enabled,
            )
        st.caption(
            "Active seed bounds for Daily Narrative QA scan: 2026-05-31 through 2026-06-06"
        )
        if qa_preview_enabled:
            try:
                rich_day_candidates = daily_narrative_rich_day_candidates(
                    user_id=int(qa_user_id),
                    start_date="2026-05-31",
                    end_date="2026-06-06",
                    top=5,
                )
            except Exception as exc:
                st.warning(
                    "Daily Narrative rich-day scan failed safely: "
                    f"{extract_api_error_message(exc)}"
                )
                rich_day_candidates = []
            with st.expander(
                "Recommended Daily Narrative rich-data days", expanded=False
            ):
                st.caption(
                    "Read-only Developer Mode scan. It does not call a provider and does not "
                    "change normal Today behavior."
                )
                render_daily_narrative_rich_day_candidates(rich_day_candidates)

        preview_user_id = int(qa_user_id) if qa_preview_enabled else user_id
        preview_target_date = (
            qa_selected_date.isoformat()
            if qa_preview_enabled
            else datetime.today().date().isoformat()
        )
        preview_lookback_days = int(qa_lookback_days) if qa_preview_enabled else 1
        preview_cache_key = (
            f"{user_id}|qa:{qa_preview_enabled}|preview_user:{preview_user_id}|"
            f"date:{preview_target_date}|lookback:{preview_lookback_days}"
        )

        fallback_preview = fetch_daily_coach_narrative_preview(
            preview_user_id,
            target_date=preview_target_date,
            qa_preview=qa_preview_enabled,
            lookback_days=preview_lookback_days,
        )
        if fallback_preview:
            st.write("**Deterministic grounded preview**")
            st.info(daily_coach_narrative_fallback_display(fallback_preview))
            with st.expander("Public-safe QA context summary", expanded=False):
                render_daily_coach_narrative_context_summary(fallback_preview)
        else:
            fallback_error = (
                st.session_state.daily_coach_narrative_preview_error_by_user.get(
                    preview_user_id
                )
            )
            st.warning(
                "Daily Coach Narrative fallback preview is not available: "
                f"{fallback_error or 'Unknown error'}"
            )

        lane_label = st.selectbox(
            "Narrative lane",
            options=daily_coach_narrative_lane_labels(),
            key=f"daily_coach_narrative_lane_{user_id}",
            help="Manual Developer Mode preview only. This does not change normal Today UI.",
        )
        lane_key = daily_coach_narrative_lane_key_from_label(lane_label)
        st.caption(daily_coach_narrative_lane_description(lane_key))

        lane_warning = daily_coach_narrative_lane_warning(lane_key)
        if lane_warning:
            st.warning(lane_warning)

        if st.button(
            "Run selected narrative preview",
            key=f"run_daily_coach_narrative_preview_{user_id}",
        ):
            preview = fetch_daily_coach_narrative_preview(
                preview_user_id,
                lane_key,
                target_date=preview_target_date,
                qa_preview=qa_preview_enabled,
                lookback_days=preview_lookback_days,
            )
            if preview:
                st.session_state.daily_coach_narrative_preview_by_user[
                    preview_cache_key
                ] = preview
            else:
                st.session_state.daily_coach_narrative_preview_by_user.pop(
                    preview_cache_key, None
                )

        preview_error = (
            st.session_state.daily_coach_narrative_preview_error_by_user.get(
                preview_user_id
            )
        )
        preview = st.session_state.daily_coach_narrative_preview_by_user.get(
            preview_cache_key
        )

        if preview_error:
            st.warning(f"Narrative preview call failed safely: {preview_error}")

        render_daily_coach_async_developer_lifecycle_panel(user_id)

        if not preview:
            return

        approved_narrative = daily_coach_narrative_approved_display(preview)
        fallback_used = preview.get("fallback_used")

        if approved_narrative and not fallback_used:
            st.success("Approved provider narrative")
            st.write(approved_narrative.get("coach_note") or "No coach note returned.")
            key_takeaway = approved_narrative.get("key_takeaway")
            if key_takeaway:
                st.write(f"**Key takeaway:** {key_takeaway}")
            recommended_focus = approved_narrative.get("recommended_focus")
            if recommended_focus:
                st.write(f"**Recommended focus:** {recommended_focus}")
            confidence_language = approved_narrative.get("confidence_language")
            if confidence_language:
                st.caption(confidence_language)
        else:
            st.info(daily_coach_narrative_fallback_display(preview))

        st.write("**Public-safe preview status**")
        render_daily_coach_narrative_preview_status(preview)

        with st.expander("Public-safe context summary", expanded=False):
            render_daily_coach_narrative_context_summary(preview)

        eligibility = daily_coach_preview_approval_eligibility(preview)
        if eligibility.eligible:
            st.success("This qwen2.5:3b preview is eligible for session-only approval.")
            if st.button(
                "Approve for this session",
                key=f"approve_daily_coach_narrative_session_{user_id}",
            ):
                store_daily_coach_session_approved_narrative(st.session_state, preview)
                st.success(
                    "Session-approved coach note is active for this user/date/action until the session or context changes."
                )
        else:
            st.info("Session approval is not available for this preview.")
            with st.expander("Why approval is blocked", expanded=False):
                for reason in eligibility.reasons:
                    st.write(f"- {reason}")

        active_record = get_daily_coach_session_approved_narrative(
            st.session_state,
            {
                "user_id": preview.get("user_id"),
                "date": preview.get("date"),
                "next_action_id": preview.get("next_action_id"),
                "workflow_target": preview.get("workflow_target"),
            },
        )
        if active_record:
            st.caption("Session approval is active for this preview context.")
            if st.button(
                "Clear session-approved coach note",
                key=f"clear_daily_coach_narrative_session_{user_id}",
            ):
                clear_daily_coach_session_approved_narrative(
                    st.session_state, active_record["approval_key"]
                )
                st.info("Session-approved coach note cleared.")


def render_daily_coach_today_card(user_id: int) -> None:
    st.subheader("Today’s Coach Note")
    st.caption("A short note tied to your next action.")

    try:
        response = api_get(f"/daily-coach/{user_id}/today-card", request_timeout=30)
    except requests.RequestException as exc:
        st.info("Today’s plan is still available. Start with the next action above.")
        if st.session_state.get("developer_mode", False):
            with st.expander("Developer details: Today Coach Note error"):
                st.write(extract_api_error_message(exc))
        return

    if not response.get("success"):
        st.info("Today’s plan is still available. Start with the next action above.")
        developer_details("Developer details: Today Coach Note response", response)
        return

    card = response.get("today_card") or {}
    if not card:
        st.info("Today’s plan is still available. Start with the next action above.")
        developer_details("Developer details: Today Coach Note response", response)
        return

    card_title = card.get("card_title") or "Today’s Coach Note"
    coach_note = card.get("coach_note") or (
        "Today’s plan is still available. Start with the next action above."
    )
    next_action_title = card.get("next_action_title") or "Next action"
    cta_label = card.get("cta_label") or f"Next action: {next_action_title}"
    supporting_reason = card.get("supporting_reason")

    approval_context = build_daily_coach_session_approval_context(
        user_id, today_card_date=card.get("date")
    )
    session_record = (
        get_daily_coach_session_approved_narrative(st.session_state, approval_context)
        if approval_context
        else None
    )
    chips = [portfolio_chip(cta_label, "green")]
    if session_record:
        coach_note = daily_coach_session_approved_card_text(session_record)
        chips.append(portfolio_chip("Session-approved coach note", "purple"))

    st.markdown(
        portfolio_card_html(
            "Daily Coach",
            card_title,
            coach_note,
            chips,
            "portfolio-card-purple",
        ),
        unsafe_allow_html=True,
    )

    if supporting_reason:
        st.caption(f"Why this today: {supporting_reason}")

    if st.session_state.get("developer_mode", False) and session_record:
        st.caption(
            "Developer Mode: session-only Daily Coach narrative approval is active."
        )

    developer_details("Developer details: Today Coach Note response", response)


def render_daily_next_action_panel(user_id: int) -> None:
    st.subheader("Next Best Action")
    st.caption(
        "One selected action for today, grounded in your current check-in and logs."
    )

    try:
        response = api_get(f"/daily-coach/{user_id}/next-action")
    except requests.RequestException as exc:
        st.info("Daily next action is not available yet.")
        if st.session_state.get("developer_mode", False):
            with st.expander("Developer details: daily next action error"):
                st.write(extract_api_error_message(exc))
        return

    if not response.get("success"):
        st.info("Daily next action is not available yet.")
        developer_details("Developer details: daily next action response", response)
        return

    action = response.get("daily_next_action") or {}
    if not action:
        st.info("Daily next action is not available yet.")
        developer_details("Developer details: daily next action response", response)
        return

    severity = action.get("severity") or "info"
    severity_label = DAILY_NEXT_ACTION_SEVERITY_LABELS.get(severity, "Next step")
    workflow_target = action.get("workflow_target")
    workflow_label = DAILY_NEXT_ACTION_WORKFLOW_LABELS.get(
        workflow_target,
        humanize_label(workflow_target),
    )

    if severity == "warning":
        st.warning(f"**{action.get('title', 'Next action')}**")
    elif severity == "success":
        st.success(f"**{action.get('title', 'Next action')}**")
    else:
        st.info(f"**{action.get('title', 'Next action')}**")

    if action.get("summary"):
        st.write(action.get("summary"))
    if action.get("reason"):
        st.caption(action.get("reason"))

    meta_col, target_col = st.columns([1, 2])
    with meta_col:
        st.caption(f"**Priority:** {severity_label}")
    with target_col:
        st.caption(f"**Go to:** {workflow_label}")

    developer_details("Developer details: daily next action", response)


def render_daily_coach_synthesis_card(user_id: int) -> None:
    st.subheader("Coach’s Read for Today")
    st.caption(
        "Backend-approved Daily Coach Synthesis for today. This is the Coach’s Read surface, separate from the Developer Preview panel."
    )

    synthesis_response = None
    synthesis_error = None

    try:
        synthesis_response = api_get(f"/daily-coach/{user_id}/synthesis")
    except requests.RequestException as exc:
        synthesis_error = extract_api_error_message(exc)

    if synthesis_error:
        st.info(
            "Coach’s Read is not available yet. Daily Next Action and Today’s Coach Note still work."
        )
        if st.session_state.get("developer_mode", False):
            with st.expander(
                "Developer details: Coach’s Read / Daily Coach Synthesis error"
            ):
                st.write(synthesis_error)
        return

    if not synthesis_response or not synthesis_response.get("success"):
        st.info(
            "Coach’s Read is not available yet. Daily Next Action and Today’s Coach Note still work."
        )
        developer_details(
            "Developer details: Coach’s Read / Daily Coach Synthesis response",
            synthesis_response or {},
        )
        return

    synthesis = synthesis_response.get("daily_coach_synthesis") or {}
    if not synthesis:
        st.info(
            "Coach’s Read is not available yet. Daily Next Action and Today’s Coach Note still work."
        )
        developer_details(
            "Developer details: Coach’s Read / Daily Coach Synthesis response",
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
            st.markdown(
                portfolio_card_html(
                    "Coach’s Read",
                    "Daily Coach Synthesis",
                    today_summary,
                    [portfolio_chip("Backend-approved", "green")],
                    "portfolio-card-accent",
                ),
                unsafe_allow_html=True,
            )
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
        "Developer details: Coach’s Read / Daily Coach Synthesis response",
        synthesis_response,
    )


def render_daily_recommendation_snapshot(user_id: int) -> None:
    st.subheader("Daily Coaching Recommendation")
    st.caption(
        "Approved backend recommendation rendered from the deterministic coaching "
        "pipeline."
    )

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
        "Workout selection and execution now live on the Workout page so Today stays focused."
    )

    active_plan_response = get_active_plan_response(user_id)

    if active_plan_response:
        workout_plan_instance = active_plan_response.get("workout_plan_instance") or {}
        execution_session = active_plan_response.get("execution_session") or {}
        approved_plan = active_plan_response.get("approved_workout_plan") or {}
        planned_exercises = active_plan_response.get("planned_exercises") or []

        col1, col2, col3 = st.columns(3)
        col1.metric("Workout", approved_plan.get("title", "Selected Workout"))
        col2.metric(
            "Duration", f"{approved_plan.get('duration_minutes', 'Unknown')} min"
        )
        col3.metric("Status", humanize_label(workout_plan_instance.get("status")))

        st.write(
            approved_plan.get("session_focus")
            or "Continue the selected workout from the Workout page."
        )
        st.caption(
            f"{len(planned_exercises)} planned exercises. "
            "Open Workout to start, log sets, complete, or review details."
        )

        plan_status = workout_plan_instance.get("status")
        execution_status = execution_session.get("status")
        if plan_status == "completed" or execution_status == "completed":
            target_step = "3. Review"
            button_label = "Review in Workout"
        else:
            target_step = "2. Do Workout"
            button_label = "Continue in Workout"

        if st.button(button_label, key="today_go_to_workout_active", type="primary"):
            request_workout_flow_step(target_step)
            request_main_navigation_page("Workout")
            st.rerun()

        developer_details(
            "Developer details: compact Today workout state",
            {
                "workout_plan_instance": workout_plan_instance,
                "execution_session": execution_session,
                "planned_exercise_count": len(planned_exercises),
            },
        )
        return

    st.info("No active workout selected yet.")
    st.write("Open Workout to preview and select today's plan.")

    if st.button("Go to Workout", key="today_go_to_workout_no_active", type="primary"):
        request_workout_flow_step("1. Plan")
        request_main_navigation_page("Workout")
        st.rerun()


def render_recovery_checkin_card(user_id: int) -> None:
    st.subheader("Recovery Check-In")
    st.markdown(
        portfolio_card_html(
            "Start here",
            "Recovery drives today's coaching read",
            "Sleep, energy, soreness, and body weight help the backend adjust today's workout and nutrition guidance safely.",
            [
                portfolio_chip("Sleep", "purple"),
                portfolio_chip("Energy", "green"),
                portfolio_chip("Soreness", "amber"),
                portfolio_chip("Body weight"),
            ],
            "portfolio-card-amber",
        ),
        unsafe_allow_html=True,
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
        "Start with one clear action, then use recovery, nutrition, and workout context to follow through."
    )

    render_daily_next_action_panel(user_id)
    render_daily_coach_today_card(user_id)
    render_daily_coach_async_approved_preview_bridge(user_id)

    st.divider()

    top_recovery_col, top_coach_col = st.columns([1, 1.25])
    with top_recovery_col:
        render_recovery_checkin_card(user_id)
    with top_coach_col:
        render_daily_coach_synthesis_card(user_id)
        with st.expander("Daily Grounded Recommendation", expanded=True):
            render_daily_recommendation_snapshot(user_id)
        render_daily_coach_narrative_developer_panel(user_id)
        render_daily_coach_async_provider_runtime_panel(user_id)
        render_daily_coach_async_persistence_inspection_panel(user_id)

    st.divider()

    nutrition_col, reflection_col = st.columns([1, 1])
    with nutrition_col:
        render_quick_nutrition_status(user_id)
    with reflection_col:
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

    if st.session_state.workout_daily_state_message:
        st.info(st.session_state.workout_daily_state_message)
        st.session_state.workout_daily_state_message = None

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

        st.subheader("Workout Plan Preview")
        st.caption(
            "Deterministic workout plan built from the approved coaching scenario, "
            "training constraints, equipment profile, and validator boundaries."
        )
        workout_size_preference = render_workout_size_preference_control("plan")
        active_plan_response = get_active_plan_response(user_id)
        has_selected_workout = has_current_workout_selection(active_plan_response)
        force_preview_refresh = st.button(
            "Show different exercises",
            key="refresh_workout_plan_preview_button",
            help=(
                "Generate a new unselected preview variation. Selected and active "
                "workouts stay unchanged."
            ),
            disabled=has_selected_workout,
        )
        if has_selected_workout:
            st.caption(
                "A workout is already selected. The selected workout is frozen unless "
                "you explicitly replace it in a future workflow."
            )
        try:
            workout_plan_data = get_stable_workout_plan_preview(
                user_id,
                workout_size_preference,
                force_refresh=force_preview_refresh and not has_selected_workout,
            )
        except requests.RequestException as exc:
            st.error(
                f"Failed to load workout plan preview: {extract_api_error_message(exc)}"
            )
            return

        if workout_plan_data.get("success"):
            scenario = workout_plan_data.get("scenario")
            confidence = workout_plan_data.get("confidence", "Unknown")
            approved_workout_plan = workout_plan_data.get("approved_workout_plan", {})

            col1, col2, col3 = st.columns(3)
            col1.metric("Plan Context", scenario_display_name(scenario))
            col2.metric("Confidence", confidence)
            col3.metric(
                "Exercise Count",
                len(approved_workout_plan.get("exercises") or []),
            )
            count_reason = workout_count_reason_from_payload(
                workout_plan_data,
                approved_workout_plan,
            )
            if count_reason:
                st.caption(count_reason)

            display_workout_plan_preview(approved_workout_plan, user_id=user_id)

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
                        "Need a swap?",
                        expanded=bool(active_substitutions),
                    ):
                        st.caption(
                            "Optional: choose one exercise to replace before you start. "
                            "After you apply a swap, the active workout plan updates automatically "
                            "and the Do Workout step uses the active exercise choice for logging."
                        )
                        display_substitution_candidates(
                            plan_instance_id,
                            planned_exercises,
                            context_key="plan_step",
                            plan_status=workout_plan_instance.get("status"),
                            execution_status=execution_session.get("status"),
                            active_substitutions=active_substitutions,
                            always_visible=False,
                            title="Need a swap?",
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
                select_today_workout(
                    user_id,
                    "select_workout_plan_button",
                    workout_size_preference=workout_size_preference,
                    approved_workout_plan=approved_workout_plan,
                )

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

    range_fallback_keys = {
        "target",
        "target_amount",
        "target_value",
        "range",
        "approved_target",
        "target_range",
        "target_display",
    }

    if not any(key in range_fallback_keys for key in keys):
        return None

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
    normalized_candidates = {
        str(key).lower().replace(" ", "_") for key in candidate_keys
    }

    for key in candidate_keys:
        value = summary.get(key)
        if isinstance(value, dict):
            return value

    comparisons = summary.get("comparisons")
    if isinstance(comparisons, dict):
        for key in candidate_keys:
            value = comparisons.get(key)
            if isinstance(value, dict):
                return value

        for comparison_key, value in comparisons.items():
            if not isinstance(value, dict):
                continue
            normalized_key = str(comparison_key).lower().replace(" ", "_")
            if normalized_key in normalized_candidates:
                return value

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


def numeric_nutrition_amount(value: object) -> float | None:
    """Return a numeric nutrition amount when public response values permit it."""

    amount, _unit = nutrition_amount_parts(value)
    if amount is None or amount == "":
        return None

    try:
        numeric_value = float(amount)
    except (TypeError, ValueError):
        return None

    if numeric_value != numeric_value:
        return None

    return numeric_value


def format_nutrition_difference_amount(value: float, unit: str | None) -> str:
    rounded_value = round(abs(value), 1)
    if rounded_value.is_integer():
        rounded_value = int(rounded_value)

    return f"{rounded_value} {unit}".strip() if unit else str(rounded_value)


def format_nutrition_difference_range(
    lower_value: float,
    upper_value: float,
    unit: str | None,
) -> str:
    lower_value = abs(lower_value)
    upper_value = abs(upper_value)

    minimum_value = min(lower_value, upper_value)
    maximum_value = max(lower_value, upper_value)

    if round(minimum_value, 1) == round(maximum_value, 1):
        return format_nutrition_difference_amount(minimum_value, unit)

    return (
        f"{format_nutrition_difference_amount(minimum_value, None)}–"
        f"{format_nutrition_difference_amount(maximum_value, unit)}"
    )


def nutrition_limited_difference_label(comparison: dict) -> str:
    status = str(
        comparison.get("target_status")
        or comparison.get("status")
        or comparison.get("comparison_status")
        or ""
    ).lower()
    limitations = comparison.get("limitations") or []
    reason_codes = comparison.get("reason_codes") or []
    has_limiting_context = any(
        [
            limitations,
            reason_codes,
            comparison.get("limitation"),
            comparison.get("reason"),
            comparison.get("reason_code"),
        ]
    )

    if status in {"unavailable", "not_available"} and not has_limiting_context:
        return "Not available"

    return "Limited"


def nutrition_difference_values_from_keys(comparison: dict) -> list[float]:
    values = []
    for key in (
        "delta_min",
        "delta_max",
        "delta",
        "difference",
        "variance",
        "remaining",
    ):
        numeric_value = numeric_nutrition_amount(comparison.get(key))
        if numeric_value is not None:
            values.append(numeric_value)

    return values


def nutrition_difference_text(comparison: dict, unit: str | None) -> str:
    """Return user-facing target-vs-actual difference text.

    The backend remains the source of truth for whether a comparison is displayable.
    This helper only improves wording for approved range comparisons.
    """

    status = str(
        comparison.get("target_status")
        or comparison.get("status")
        or comparison.get("comparison_status")
        or ""
    ).lower()

    if status in {"blocked", "limited"}:
        return "Limited"

    if not comparison_is_displayable(comparison):
        return nutrition_limited_difference_label(comparison)

    actual = target_comparison_value(
        comparison,
        ["actual", "actual_amount", "actual_value", "logged", "logged_amount"],
    )
    actual_value = numeric_nutrition_amount(actual)
    target_min = numeric_nutrition_amount(comparison.get("target_min"))
    target_max = numeric_nutrition_amount(comparison.get("target_max"))

    if actual_value is not None and target_min is not None and target_max is not None:
        if actual_value < target_min:
            return (
                f"{format_nutrition_difference_range(target_min - actual_value, target_max - actual_value, unit)} "
                "below target"
            )
        if actual_value > target_max:
            return (
                f"{format_nutrition_difference_amount(actual_value - target_max, unit)} "
                "above target"
            )
        return "within target range"

    target = target_comparison_value(
        comparison,
        ["target", "target_amount", "target_value", "approved_target"],
    )
    target_value = numeric_nutrition_amount(target)

    if actual_value is not None and target_value is not None:
        difference = actual_value - target_value
        if difference < 0:
            return (
                f"{format_nutrition_difference_amount(difference, unit)} below target"
            )
        if difference > 0:
            return (
                f"{format_nutrition_difference_amount(difference, unit)} above target"
            )
        return "within target range"

    if status in {"within_target", "within_range", "on_target", "at_target"}:
        return "within target range"

    difference_values = nutrition_difference_values_from_keys(comparison)
    if status in {"below_target", "below_range", "under_target"}:
        if len(difference_values) >= 2:
            return (
                f"{format_nutrition_difference_range(difference_values[0], difference_values[1], unit)} "
                "below target"
            )
        if len(difference_values) == 1:
            return (
                f"{format_nutrition_difference_amount(difference_values[0], unit)} "
                "below target"
            )
        return "below target"

    if status in {"above_target", "above_range", "over_target"}:
        if difference_values:
            return (
                f"{format_nutrition_difference_amount(difference_values[0], unit)} "
                "above target"
            )
        return "above target"

    if status in {"unavailable", "not_available"}:
        return nutrition_limited_difference_label(comparison)

    if difference_values:
        return format_nutrition_difference_amount(difference_values[0], unit)

    return "Not available"


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
                "logged_calories",
                "calorie_actual",
                "total_calories",
                "energy",
                "energy_kcal",
                "kcal",
            ],
            "kcal",
        ),
        (
            "Protein",
            [
                "protein",
                "logged_protein",
                "protein_g",
                "protein_grams",
                "total_protein_g",
            ],
            "g",
        ),
        (
            "Carbs",
            [
                "carbs",
                "logged_carbs",
                "carbohydrates",
                "carbohydrate",
                "carbohydrate_g",
                "carbohydrate_grams",
                "total_carbohydrate_g",
            ],
            "g",
        ),
        (
            "Fat",
            ["fat", "logged_fat", "fat_g", "fat_grams", "total_fat_g"],
            "g",
        ),
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
            status = (
                comparison.get("status")
                or comparison.get("guidance")
                or comparison.get("target_status")
                or "Available"
            )
        else:
            target = None
            limitations = comparison.get("limitations") or []
            reason_codes = comparison.get("reason_codes") or []
            status = (
                comparison.get("limitation")
                or comparison.get("reason")
                or comparison.get("reason_code")
                or (limitations[0] if limitations else None)
                or (reason_codes[0] if reason_codes else None)
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
                "Difference": nutrition_difference_text(comparison, unit),
                "Status": status_text,
            }
        )

    return rows


def nutrition_target_band_target_bounds(
    comparison: dict,
) -> tuple[float | None, float | None]:
    target_min = numeric_nutrition_amount(comparison.get("target_min"))
    target_max = numeric_nutrition_amount(comparison.get("target_max"))

    if target_min is not None and target_max is not None:
        return target_min, target_max

    target = target_comparison_value(
        comparison,
        ["target", "target_amount", "target_value", "approved_target"],
    )
    target_value = numeric_nutrition_amount(target)
    if target_value is not None:
        return target_value, target_value

    return None, None


def nutrition_target_band_status_label(comparison: dict, unit: str | None) -> str:
    status_text = nutrition_difference_text(comparison, unit)
    if status_text and status_text != "Not available":
        return status_text.rstrip(".")

    status = (
        comparison.get("status")
        or comparison.get("guidance")
        or comparison.get("target_status")
        or "Available"
    )
    return nutrition_public_text(status).rstrip(".") or "Available"


def nutrition_target_band_status_tone(status_label: str) -> str:
    normalized = status_label.lower()
    if "within" in normalized or "on target" in normalized:
        return "green"
    if "below" in normalized or "above" in normalized:
        return "amber"
    return "purple"


def nutrition_target_band_specs(summary: dict) -> list[dict]:
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

    specs = []
    for label, keys, unit in macro_specs:
        comparison = macro_comparison_from_summary(summary, keys)
        if not comparison:
            continue

        actual = target_comparison_value(
            comparison,
            ["actual", "actual_amount", "actual_value", "logged", "logged_amount"],
        )
        actual_value = numeric_nutrition_amount(actual)
        displayable = comparison_is_displayable(comparison)
        target_min, target_max = nutrition_target_band_target_bounds(comparison)
        status_label = nutrition_target_band_status_label(comparison, unit)

        target_available = (
            displayable
            and actual_value is not None
            and target_min is not None
            and target_max is not None
        )

        if not target_available:
            specs.append(
                {
                    "label": label,
                    "unit": unit,
                    "limited": True,
                    "actual_label": format_nutrition_value(actual, unit),
                    "target_label": "Limited",
                    "status_label": status_label,
                    "tone": "purple",
                }
            )
            continue

        scale = max(actual_value, target_max, 1) * 1.15
        actual_pct = max(0.0, min(100.0, (actual_value / scale) * 100))
        target_start_pct = max(0.0, min(100.0, (target_min / scale) * 100))
        target_end_pct = max(0.0, min(100.0, (target_max / scale) * 100))
        if target_end_pct < target_start_pct:
            target_start_pct, target_end_pct = target_end_pct, target_start_pct

        specs.append(
            {
                "label": label,
                "unit": unit,
                "limited": False,
                "actual_value": actual_value,
                "actual_label": format_nutrition_value(actual, unit),
                "target_label": (
                    format_nutrition_value(target_min, unit)
                    if target_min == target_max
                    else f"{format_nutrition_value(target_min, unit)}–{format_nutrition_value(target_max, unit)}"
                ),
                "status_label": status_label,
                "tone": nutrition_target_band_status_tone(status_label),
                "actual_pct": actual_pct,
                "target_start_pct": target_start_pct,
                "target_end_pct": target_end_pct,
            }
        )

    return specs


def render_nutrition_target_band(spec: dict) -> None:
    label = escape(str(spec.get("label", "Target")))
    actual_label = escape(str(spec.get("actual_label") or "Not available"))
    target_label = escape(str(spec.get("target_label") or "Limited"))
    status_label = escape(str(spec.get("status_label") or "Limited"))
    tone = spec.get("tone") or "purple"
    accent_class = (
        "portfolio-card-green"
        if tone == "green"
        else "portfolio-card-amber"
        if tone == "amber"
        else "portfolio-card-purple"
    )

    if spec.get("limited"):
        st.markdown(
            portfolio_card_html(
                label,
                "Target band limited",
                "The backend did not approve this target for numeric visual display.",
                [
                    portfolio_chip(f"Logged: {actual_label}"),
                    portfolio_chip("Limited", "purple"),
                ],
                accent_class,
            ),
            unsafe_allow_html=True,
        )
        return

    actual_pct = float(spec.get("actual_pct") or 0)
    target_start_pct = float(spec.get("target_start_pct") or 0)
    target_end_pct = float(spec.get("target_end_pct") or 0)
    target_width_pct = max(1.0, target_end_pct - target_start_pct)
    chip_html = " ".join(
        [
            portfolio_chip(f"Logged: {actual_label}", "green"),
            portfolio_chip(f"Target: {target_label}"),
            portfolio_chip(status_label, tone),
        ]
    )

    st.markdown(
        f"""
        <div class="portfolio-card {accent_class}">
            <div class="portfolio-eyebrow">{label}</div>
            <div style="position: relative; height: 12px; border-radius: 999px; background: #111827; overflow: hidden; border: 1px solid rgba(148, 163, 184, 0.22); margin: 0.28rem 0 0.48rem 0;">
                <div title="Approved target band" style="position: absolute; left: {target_start_pct:.2f}%; width: {target_width_pct:.2f}%; height: 100%; background: rgba(34, 197, 94, 0.46);"></div>
                <div title="Logged actual" style="position: absolute; left: {actual_pct:.2f}%; width: 3px; height: 100%; background: #f8fafc;"></div>
            </div>
            <div>{chip_html}</div>
            <div class="portfolio-muted">target band = approved range · marker = logged actual</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_nutrition_target_band_chart(summary: dict) -> None:
    specs = nutrition_target_band_specs(summary)
    if not specs:
        return

    st.markdown("#### Target Bands")
    st.caption(
        "Visual comparison of logged actuals against backend-approved target ranges. "
        "Limited targets stay hidden."
    )

    for row_start in range(0, len(specs), 2):
        columns = st.columns(2)
        for column, spec in zip(
            columns, specs[row_start : row_start + 2], strict=False
        ):
            with column:
                render_nutrition_target_band(spec)


def display_target_vs_actual_table(summary: dict) -> None:
    rows = nutrition_comparison_rows_from_summary(summary)
    if not rows:
        st.caption(
            "Target comparisons are limited for this date. Keep logging meals to improve "
            "nutrition guidance."
        )
        return

    display_nutrition_target_band_chart(summary)

    st.markdown("#### Target vs Actual")
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
        st.markdown("**Confidence**")
        st.write(trend_calibration_metric_text(confidence))
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
        st.markdown("**Logging**")
        st.write(logging_metric_label)

    if logging_caption:
        st.caption(logging_caption)

    st.divider()

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
    """Short normal-user label for canonical food selection."""
    display_name = food.get("display_name") or "Unknown food"
    food_type = humanize_label(food.get("food_type"))
    serving_grams = food.get("default_grams")

    details = []
    if food_type != "Unknown":
        details.append(food_type)
    if serving_grams is not None:
        details.append(f"default {serving_grams:g}g")

    if details:
        return f"{display_name} ({'; '.join(details)})"

    return str(display_name)


def canonical_food_default_serving_text(food: dict) -> str:
    default_grams = food.get("default_grams")
    default_unit = food.get("default_unit") or "serving"

    if default_grams is None:
        return "Default serving unavailable"

    return f"Default: {default_grams:g}g {default_unit}"


def display_canonical_food_matches(canonical_foods: list[dict]) -> None:
    """Display canonical search results as a screenshot-friendly clean table."""
    if not canonical_foods:
        return

    st.markdown("#### Clean food matches")
    st.caption("Top app-facing foods from the approved canonical catalog.")

    rows = []
    for index, food in enumerate(canonical_foods[:5], start=1):
        display_name = food.get("display_name") or "Unknown food"
        food_type = humanize_label(food.get("food_type"))
        default_serving = canonical_food_default_serving_text(food)
        nutrient_summary = canonical_food_nutrient_summary_text(food)

        rows.append(
            {
                "Match": f"{index}. {display_name}",
                "Type": "" if food_type == "Unknown" else food_type,
                "Default": default_serving.replace("Default: ", ""),
                "Per 100g": nutrient_summary.replace(" per 100g", ""),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    if len(canonical_foods) > 5:
        with st.expander("Show additional clean matches", expanded=False):
            extra_rows = []
            for food in canonical_foods[5:]:
                display_name = food.get("display_name") or "Unknown food"
                food_type = humanize_label(food.get("food_type"))
                default_serving = canonical_food_default_serving_text(food)
                nutrient_summary = canonical_food_nutrient_summary_text(food)
                extra_rows.append(
                    {
                        "Food": display_name,
                        "Type": "" if food_type == "Unknown" else food_type,
                        "Default": default_serving.replace("Default: ", ""),
                        "Per 100g": nutrient_summary.replace(" per 100g", ""),
                    }
                )

            if extra_rows:
                st.dataframe(pd.DataFrame(extra_rows), width="stretch", hide_index=True)


def display_selected_canonical_food_summary(food: dict) -> None:
    display_name = food.get("display_name") or "Selected food"
    food_type = humanize_label(food.get("food_type"))
    nutrient_summary = canonical_food_nutrient_summary_text(food)
    default_serving = canonical_food_default_serving_text(food)

    st.markdown(f"**Selected:** {display_name}")
    summary_parts = [default_serving, nutrient_summary]
    if food_type != "Unknown":
        summary_parts.insert(0, food_type)
    st.caption(" · ".join(summary_parts))


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


def food_suggestion_macro_label(macro_name: object) -> str:
    labels = {
        "calories": "Calories",
        "protein_g": "Protein",
        "carbohydrate_g": "Carbs",
        "fat_g": "Fat",
        "none": "No approved gap",
        None: "No approved gap",
    }
    return labels.get(macro_name, humanize_label(str(macro_name)))


def food_suggestion_public_text(value: object) -> str:
    """Humanize public-safe food suggestion limitations/reason-style values."""
    if value is None or value == "":
        return ""

    if isinstance(value, dict):
        for key in ("message", "label", "description", "text", "reason", "code"):
            if value.get(key):
                return food_suggestion_public_text(value.get(key))
        return humanize_label(str(value))

    text_value = str(value).strip()
    if not text_value:
        return ""

    limitation_labels = {
        "no_macro_gap_detected": "No approved macro gap is available for food suggestions right now.",
        "no_approved_macro_gap": "No approved macro gap is available for food suggestions right now.",
        "target_not_approved": "Food suggestions are limited because the relevant target is not approved for display yet.",
        "protein_target_not_approved": "Protein food suggestions require an approved protein target.",
        "calorie_target_not_approved": "Calorie food suggestions require an approved calorie target.",
        "carbohydrate_target_not_approved": "Carbohydrate food suggestions require an approved carbohydrate target.",
        "fat_target_not_approved": "Fat food suggestions require an approved fat target.",
        "logging_incomplete_limits_suggestions": "Suggestions are limited because logging appears incomplete.",
        "nutrition_logging_incomplete": "Suggestions are limited because logging appears incomplete.",
        "nutrition_actuals_unavailable": "Suggestions are limited because logged nutrition actuals are unavailable for this date.",
        "canonical_food_catalog_unavailable": "Food suggestions are limited because the canonical food catalog is unavailable.",
        "canonical_food_nutrients_incomplete": "Some food nutrient estimates are incomplete.",
    }

    if text_value in limitation_labels:
        return limitation_labels[text_value]

    if " " in text_value and "_" not in text_value:
        return text_value if text_value.endswith((".", "!", "?")) else f"{text_value}."

    return nutrition_public_text(text_value)


def food_suggestion_amount(value: object, suffix: str = "") -> str:
    if value is None or value == "":
        return "Not available"

    if isinstance(value, float):
        value = round(value, 1)
        if value.is_integer():
            value = int(value)

    return f"{value}{suffix}"


def food_suggestion_estimate_text(suggestion: dict) -> str:
    estimate_specs = [
        ("estimated_calories", " kcal"),
        ("estimated_protein_g", "g protein"),
        ("estimated_carbohydrate_g", "g carbs"),
        ("estimated_fat_g", "g fat"),
    ]
    parts = []
    for key, label in estimate_specs:
        value = suggestion.get(key)
        if value is None:
            continue
        parts.append(food_suggestion_amount(value, label))

    if not parts:
        return "Estimated nutrients unavailable."

    return "Estimated: " + " / ".join(parts)


def food_suggestion_primary_gap_summary(suggestions_response: dict) -> str:
    primary_gap = suggestions_response.get("primary_gap")
    if not primary_gap or primary_gap == "none":
        return "No approved macro gap is available for food suggestions right now."

    primary_label = food_suggestion_macro_label(primary_gap)
    macro_gaps = suggestions_response.get("macro_gaps") or []
    matching_gap = None
    for macro_gap in macro_gaps:
        if macro_gap.get("macro_name") == primary_gap:
            matching_gap = macro_gap
            break

    if matching_gap and matching_gap.get("display_allowed"):
        target_status = matching_gap.get("target_status")
        gap_value = matching_gap.get("gap_value")
        unit = matching_gap.get("unit") or ""
        if target_status == "below_target" and gap_value is not None:
            gap_text = food_suggestion_amount(gap_value, f" {unit}" if unit else "")
            return (
                f"{primary_label} is below target by about {gap_text} based on logged meals. "
                "These foods may help close that approved gap."
            )
        if target_status:
            return (
                f"{primary_label} is the primary approved nutrition focus for this date. "
                "Suggestions are based on backend-approved target and actual data."
            )

    return (
        f"{primary_label} is the primary approved nutrition focus, but suggestion detail "
        "is limited by the current logging or target context."
    )


def render_food_suggestion_card(suggestion: dict, index: int) -> None:
    display_name = suggestion.get("display_name") or "Suggested food"
    suggested_grams = suggestion.get("suggested_grams")
    macro_gap = food_suggestion_macro_label(suggestion.get("macro_gap_addressed"))
    confidence = suggestion.get("confidence", "Unknown")
    suggestion_summary = suggestion.get("suggestion_summary")
    limitations = suggestion.get("limitations") or []

    chips = [
        portfolio_chip(f"{food_suggestion_amount(suggested_grams, 'g')}", "green"),
        portfolio_chip(f"Focus: {macro_gap}", "purple"),
        portfolio_chip(f"Confidence: {confidence}"),
    ]
    st.markdown(
        portfolio_card_html(
            "Approved food suggestion",
            display_name,
            food_suggestion_estimate_text(suggestion),
            chips,
            "portfolio-card-green",
        ),
        unsafe_allow_html=True,
    )

    if suggestion_summary:
        st.caption(food_suggestion_public_text(suggestion_summary))

    if limitations:
        with st.expander(f"Suggestion limitations #{index + 1}", expanded=False):
            for limitation in limitations:
                friendly = food_suggestion_public_text(limitation)
                if friendly:
                    st.caption(f"• {friendly}")


def nutrition_runtime_debug_value(value: object) -> str:
    """Format runtime debug values for compact Developer Mode display."""
    if value is None or value == "":
        return "Not available"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (list | tuple | set)):
        if not value:
            return "None"
        return ", ".join(str(item) for item in value)
    return str(value)


def render_nutrition_explanation_runtime_debug_view(user_id: int) -> None:
    """Developer-only nutrition explanation runtime metadata inspection."""
    if not st.session_state.get("developer_mode", False):
        return

    debug_date = selected_nutrition_summary_date_text(user_id)

    with st.expander(
        "Developer details: nutrition explanation runtime debug",
        expanded=False,
    ):
        st.caption(
            "Debug-only provider/runtime inspection. This section is hidden from "
            "normal Nutrition UI."
        )

        try:
            debug_response = api_get(
                f"/nutrition/{user_id}/explanation/debug",
                params={"date": debug_date},
            )
        except requests.RequestException as exc:
            st.warning(
                "Nutrition explanation runtime debug is not available: "
                f"{extract_api_error_message(exc)}"
            )
            return

        if not debug_response.get("success", True):
            st.warning("Nutrition explanation runtime debug did not return success.")
            st.json(debug_response)
            return

        approved_explanation = (
            debug_response.get("approved_nutrition_explanation") or {}
        )
        runtime_metadata = (
            debug_response.get("runtime_metadata")
            or debug_response.get("explanation_runtime_metadata")
            or {}
        )

        final_source = (
            runtime_metadata.get("final_explanation_source")
            or runtime_metadata.get("final_plan_source")
            or "Not available"
        )
        fallback_used = runtime_metadata.get("fallback_used")
        fallback_reason = runtime_metadata.get("fallback_reason")

        top_cols = st.columns(3)
        top_cols[0].metric(
            "Final source",
            nutrition_runtime_debug_value(final_source),
        )
        top_cols[1].metric(
            "Fallback used",
            nutrition_runtime_debug_value(fallback_used),
        )
        top_cols[2].metric(
            "Candidate valid",
            nutrition_runtime_debug_value(runtime_metadata.get("candidate_valid")),
        )

        provider_cols = st.columns(3)
        provider_cols[0].metric(
            "Configured provider",
            nutrition_runtime_debug_value(runtime_metadata.get("configured_provider")),
        )
        provider_cols[1].metric(
            "Selected provider",
            nutrition_runtime_debug_value(runtime_metadata.get("selected_provider")),
        )
        provider_cols[2].metric(
            "Provider attempted",
            nutrition_runtime_debug_value(
                runtime_metadata.get("provider_attempted")
                if "provider_attempted" in runtime_metadata
                else runtime_metadata.get("crewai_attempted")
            ),
        )

        status_rows = [
            {
                "Field": "Fallback reason",
                "Value": nutrition_runtime_debug_value(fallback_reason),
            },
            {
                "Field": "Candidate parse status",
                "Value": nutrition_runtime_debug_value(
                    runtime_metadata.get("candidate_parse_status")
                ),
            },
            {
                "Field": "Validation status",
                "Value": nutrition_runtime_debug_value(
                    runtime_metadata.get("validation_status")
                    if "validation_status" in runtime_metadata
                    else runtime_metadata.get("candidate_validation_status")
                ),
            },
            {
                "Field": "Raw output length",
                "Value": nutrition_runtime_debug_value(
                    runtime_metadata.get("raw_output_length")
                ),
            },
            {
                "Field": "Raw preview present",
                "Value": nutrition_runtime_debug_value(
                    bool(runtime_metadata.get("raw_output_preview_truncated"))
                ),
            },
            {
                "Field": "Markdown wrapper detected",
                "Value": nutrition_runtime_debug_value(
                    runtime_metadata.get("markdown_wrapper_detected")
                ),
            },
        ]
        st.dataframe(pd.DataFrame(status_rows), width="stretch", hide_index=True)

        validation_errors = runtime_metadata.get("validation_errors") or []
        if validation_errors:
            with st.expander("Validation errors", expanded=False):
                for error in validation_errors:
                    st.caption(f"• {nutrition_runtime_debug_value(error)}")
        else:
            st.caption("No validation errors reported.")

        if runtime_metadata.get("raw_output_preview_truncated"):
            st.caption(
                "A bounded provider-output preview exists in the debug payload, but it "
                "is intentionally not rendered in this portfolio UI view."
            )

        with st.expander("Approved nutrition explanation", expanded=False):
            st.json(approved_explanation)

        with st.expander("Runtime metadata", expanded=False):
            st.json(runtime_metadata)

        with st.expander("Raw public-safe debug response", expanded=False):
            st.json(debug_response)


def render_nutrition_food_suggestions_card(user_id: int) -> None:
    st.subheader("Food Suggestions")
    st.caption(
        "Backend-approved canonical food ideas for approved macro gaps. "
        "These are optional suggestions, not instructions."
    )

    suggestion_date = selected_nutrition_summary_date_text(user_id)

    try:
        suggestions_response = api_get(
            f"/nutrition/{user_id}/food-suggestions",
            params={"date": suggestion_date},
        )
    except requests.RequestException as exc:
        st.caption(
            f"Food suggestions are not available yet. {extract_api_error_message(exc)}"
        )
        return

    if not suggestions_response.get("success"):
        st.caption("Food suggestions are not available for this date yet.")
        developer_details(
            "Developer details: nutrition food suggestions response",
            suggestions_response,
        )
        return

    suggestions = suggestions_response.get("suggestions") or []
    confidence = suggestions_response.get("confidence", "Unknown")
    primary_gap = suggestions_response.get("primary_gap")
    limitations = suggestions_response.get("limitations") or []

    summary_chips = [
        portfolio_chip(suggestions_response.get("suggestion_date", suggestion_date)),
        portfolio_chip(
            f"Primary gap: {food_suggestion_macro_label(primary_gap)}", "purple"
        ),
        portfolio_chip(f"Confidence: {confidence}", "green"),
    ]
    st.markdown(
        portfolio_card_html(
            "Food suggestion context",
            "Approved canonical options",
            food_suggestion_primary_gap_summary(suggestions_response),
            summary_chips,
            "portfolio-card-green",
        ),
        unsafe_allow_html=True,
    )

    if limitations:
        with st.expander("Why suggestions may be limited", expanded=False):
            for limitation in limitations:
                friendly = food_suggestion_public_text(limitation)
                if friendly:
                    st.caption(f"• {friendly}")

    if not suggestions:
        st.caption(
            "No approved food suggestions are available for this date yet. "
            "Keep logging meals to improve nutrition guidance."
        )
        developer_details(
            "Developer details: nutrition food suggestions response",
            suggestions_response,
        )
        return

    st.markdown("#### Suggested canonical foods")
    for row_start in range(0, len(suggestions), 3):
        columns = st.columns(3)
        for offset, (column, suggestion) in enumerate(
            zip(columns, suggestions[row_start : row_start + 3], strict=False)
        ):
            with column:
                render_food_suggestion_card(suggestion, row_start + offset)

    st.caption(
        "Next UI idea: make these selectable for logging once Architecture approves "
        "a click-to-log interaction."
    )

    developer_details(
        "Developer details: nutrition food suggestions response",
        suggestions_response,
    )


def nutrition_explanation_public_text(value: object) -> str:
    """Humanize public-safe nutrition explanation text without exposing raw codes."""
    if value is None or value == "":
        return ""

    if isinstance(value, dict):
        for key in (
            "message",
            "label",
            "description",
            "text",
            "summary",
            "reason",
            "code",
        ):
            if value.get(key):
                return nutrition_explanation_public_text(value.get(key))
        return humanize_label(str(value))

    if isinstance(value, list):
        parts = [nutrition_explanation_public_text(item) for item in value]
        return " ".join(part for part in parts if part)

    text_value = str(value).strip()
    if not text_value:
        return ""

    explanation_labels = {
        "incomplete_actual_set_logging_limits_inference": "Workout logging is incomplete, so recent training trends are limited.",
        "nutrition_targets_limited_by_logging_quality": "Nutrition guidance is limited because recent logging quality is incomplete.",
        "nutrition_actuals_unavailable": "Logged nutrition actuals are unavailable for this date.",
        "no_nutrition_logs_today": "No nutrition logs were found for this date.",
        "no_logs": "No nutrition logs were found for this date.",
        "no_approved_macro_gap": "No approved macro gap is available for this date.",
        "target_not_approved": "Some targets are not approved for display yet.",
        "calibration_not_ready": "Calibration is not ready yet because more consistent logs or weigh-ins are needed.",
        "calibration_read_only": "Calibration context is read-only and does not change targets.",
        "trend_context_limited": "Trend context is limited with the current logging window.",
        "food_suggestions_limited": "Food suggestion context is limited for this date.",
    }

    if text_value in explanation_labels:
        return explanation_labels[text_value]

    if " " in text_value and "_" not in text_value:
        return text_value if text_value.endswith((".", "!", "?")) else f"{text_value}."

    return nutrition_public_text(text_value)


def display_nutrition_explanation_context(
    explanation: dict,
    field_name: str,
    label: str,
) -> None:
    value = explanation.get(field_name)
    friendly_value = nutrition_explanation_public_text(value)
    if friendly_value:
        st.write(f"**{label}:** {friendly_value}")


def render_nutrition_explanation_preview_card(user_id: int) -> None:
    st.subheader("Nutrition Explanation")
    st.caption(
        "Approved explanation for the selected nutrition date. This explains context only; "
        "it does not change targets or create a meal plan."
    )

    explanation_date = selected_nutrition_summary_date_text(user_id)

    try:
        explanation_response = api_get(
            f"/nutrition/{user_id}/explanation/preview",
            params={"date": explanation_date},
        )
    except requests.RequestException as exc:
        st.caption(
            "Nutrition explanation is not available yet. "
            f"{extract_api_error_message(exc)}"
        )
        return

    if not explanation_response.get("success"):
        st.caption("Nutrition explanation is not available for this date yet.")
        developer_details(
            "Developer details: nutrition explanation preview response",
            explanation_response,
        )
        return

    explanation = explanation_response.get("approved_nutrition_explanation") or {}
    confidence = explanation.get("confidence") or explanation_response.get(
        "confidence", "Unknown"
    )
    response_date = explanation_response.get("explanation_date", explanation_date)

    metric_cols = st.columns(2)
    metric_cols[0].metric("Date", response_date)
    metric_cols[1].metric("Confidence", confidence)

    summary = nutrition_explanation_public_text(explanation.get("explanation_summary"))
    if summary:
        st.write(summary)
    else:
        st.caption("Approved nutrition explanation copy is limited for this date.")

    with st.expander("Explanation context", expanded=True):
        display_nutrition_explanation_context(
            explanation,
            "macro_context",
            "Macro context",
        )
        display_nutrition_explanation_context(
            explanation,
            "food_suggestion_context",
            "Food suggestion context",
        )
        display_nutrition_explanation_context(
            explanation,
            "trend_context",
            "Trend context",
        )
        display_nutrition_explanation_context(
            explanation,
            "calibration_context",
            "Calibration context",
        )
        display_nutrition_explanation_context(
            explanation,
            "limitations_context",
            "Limitations context",
        )

    limitations = []
    limitations.extend(explanation.get("limitations") or [])
    limitations.extend(explanation_response.get("limitations") or [])

    friendly_limitations = []
    for limitation in limitations:
        friendly = nutrition_explanation_public_text(limitation)
        if friendly and friendly not in friendly_limitations:
            friendly_limitations.append(friendly)

    if friendly_limitations:
        with st.expander("Nutrition explanation limitations", expanded=False):
            for limitation in friendly_limitations:
                st.caption(f"• {limitation}")

    developer_details(
        "Developer details: nutrition explanation preview response",
        explanation_response,
    )


TREND_CALIBRATION_LABELS = {
    "not_ready": "Not ready",
    "early_signal": "Early signal",
    "usable": "Usable",
    "strong": "Strong",
    "insufficient_data": "More data needed",
    "keep_current_targets": "Keep current formula targets",
    "maintain_broad_range": "Maintain broad range",
    "eligible_for_future_refinement": "Eligible for future refinement",
    "no_logs": "No nutrition logs are available in this window.",
    "partial_day": "Some days may only have partial nutrition logging.",
    "likely_incomplete": "Nutrition logging may be incomplete for this window.",
    "reasonably_complete": "Nutrition logging is reasonably complete.",
    "complete_enough_for_guidance": "Logging is complete enough for guidance.",
    "insufficient": "More consistent logging is needed.",
    "inconsistent": "Logging consistency is still developing.",
    "usable_logging": "Logging consistency is usable.",
    "strong_logging": "Logging consistency is strong.",
    "decreasing": "Decreasing",
    "stable": "Stable",
    "increasing": "Increasing",
    "unavailable": "Unavailable",
    "minimum_window_not_met": "More days are needed before calibration readiness can be assessed.",
    "logging_quality_not_met": "More consistent nutrition logging is needed.",
    "bodyweight_trend_unavailable": (
        "More weigh-ins are needed to understand the bodyweight trend."
    ),
    "goal_context_missing": "Goal context is needed before calibration can be considered.",
    "training_context_missing": "Training context is limited for this window.",
    "target_mutation_not_performed": (
        "Targets are still formula-derived; no target changes were applied."
    ),
    "calibration_assessment_read_only": (
        "Calibration assessment is read-only and does not change targets."
    ),
    "read_only_calibration": "Calibration assessment is read-only and does not change targets.",
}


def trend_calibration_public_text(value: object) -> str:
    """Humanize public-safe trend/calibration values without exposing raw codes."""
    if value is None or value == "":
        return ""

    if isinstance(value, dict):
        for key in ("message", "label", "description", "text", "reason", "code"):
            if value.get(key):
                return trend_calibration_public_text(value.get(key))
        return humanize_label(str(value))

    text_value = str(value).strip()
    if not text_value:
        return ""

    if text_value in TREND_CALIBRATION_LABELS:
        return TREND_CALIBRATION_LABELS[text_value]

    if " " in text_value and "_" not in text_value:
        return text_value if text_value.endswith((".", "!", "?")) else f"{text_value}."

    return humanize_label(text_value).rstrip(".") + "."


def trend_calibration_metric_text(value: object, fallback: str = "Unknown") -> str:
    if value is None or value == "":
        return fallback
    friendly = trend_calibration_public_text(value)
    return friendly.rstrip(".") if friendly else fallback


def trend_calibration_number_text(
    value: object,
    suffix: str = "",
    fallback: str = "Unavailable",
) -> str:
    if value is None or value == "":
        return fallback

    if isinstance(value, float):
        value = round(value, 1)
        if value.is_integer():
            value = int(value)

    return f"{value}{suffix}"


def trend_calibration_rate_text(value: object) -> str:
    if value is None or value == "":
        return "Unavailable"

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return trend_calibration_metric_text(value)

    if 0 <= numeric_value <= 1:
        numeric_value *= 100

    return f"{round(numeric_value, 1):g}%"


def render_trend_window_summary(trend_response: dict) -> None:
    st.markdown("#### Trend Window Summary")

    summary_cols = st.columns(4)
    summary_cols[0].metric(
        "Window",
        f"{trend_response.get('window_days', 'Unknown')} days",
    )
    summary_cols[1].metric(
        "Logged days",
        trend_calibration_number_text(trend_response.get("logged_day_count")),
    )
    summary_cols[2].metric(
        "Complete days",
        trend_calibration_number_text(trend_response.get("complete_logging_day_count")),
    )
    summary_cols[3].metric(
        "Confidence",
        trend_response.get("confidence", "Unknown"),
    )

    detail_cols = st.columns(3)
    detail_cols[0].caption(
        f"Partial logging days: "
        f"{trend_calibration_number_text(trend_response.get('partial_logging_day_count'))}"
    )
    detail_cols[1].caption(
        f"No-log days: "
        f"{trend_calibration_number_text(trend_response.get('no_log_day_count'))}"
    )

    intake_summary = trend_response.get("intake_trend_summary") or {}
    detail_cols[2].caption(
        "Complete logging rate: "
        + trend_calibration_rate_text(intake_summary.get("complete_logging_rate"))
    )

    start_date = trend_response.get("start_date")
    end_date = trend_response.get("end_date")
    if start_date or end_date:
        st.caption(f"Window: {start_date or 'Unknown'} through {end_date or 'Unknown'}")

    consistency = intake_summary.get("logging_consistency_status")
    if consistency:
        st.caption("Logging consistency: " + trend_calibration_metric_text(consistency))


def render_bodyweight_trend_summary(trend_response: dict) -> None:
    st.markdown("#### Bodyweight Trend")

    bodyweight_summary = trend_response.get("bodyweight_trend_summary") or {}
    direction = bodyweight_summary.get("trend_direction")
    weekly_rate = bodyweight_summary.get("weekly_rate_lb")

    cols = st.columns(4)
    cols[0].metric(
        "Direction",
        trend_calibration_metric_text(direction, fallback="Unavailable"),
    )
    cols[1].metric(
        "Weigh-ins",
        trend_calibration_number_text(
            bodyweight_summary.get("weigh_in_count"),
            fallback="0",
        ),
    )
    cols[2].metric(
        "Weekly rate",
        (
            trend_calibration_number_text(weekly_rate, " lb/wk")
            if weekly_rate is not None
            else "Unavailable"
        ),
    )
    cols[3].metric(
        "Confidence",
        bodyweight_summary.get("confidence", "Unknown"),
    )

    if direction in {None, "", "unavailable"}:
        st.caption(
            "Bodyweight trend is limited until there are enough consistent weigh-ins."
        )


def render_calibration_readiness_summary(
    trend_response: dict,
    calibration_response: dict,
) -> None:
    st.markdown("#### Calibration Readiness")

    readiness = trend_response.get("calibration_readiness") or {}
    readiness_level = calibration_response.get("readiness_level") or readiness.get(
        "readiness_level"
    )
    recommended_action = calibration_response.get("recommended_action")
    calibration_allowed = calibration_response.get("calibration_allowed")
    confidence = calibration_response.get("confidence", "Unknown")

    cols = st.columns(4)
    cols[0].metric(
        "Readiness",
        trend_calibration_metric_text(readiness_level),
    )
    cols[1].metric(
        "Action",
        trend_calibration_metric_text(recommended_action),
    )
    cols[2].metric(
        "Calibration allowed",
        "Yes" if calibration_allowed else "No",
    )
    cols[3].metric("Confidence", confidence)

    st.caption(
        "Targets are still formula-derived. This calibration view is read-only and "
        "does not apply target changes."
    )

    if calibration_response.get("calibrated_targets") is not None:
        st.caption(
            "Calibration target payloads are intentionally not displayed as active targets."
        )


def trend_calibration_limitations(
    trend_response: dict,
    calibration_response: dict,
) -> list[str]:
    raw_values = []

    raw_values.extend(trend_response.get("limitations") or [])
    raw_values.extend(calibration_response.get("limitations") or [])

    intake_summary = trend_response.get("intake_trend_summary") or {}
    bodyweight_summary = trend_response.get("bodyweight_trend_summary") or {}
    readiness = trend_response.get("calibration_readiness") or {}

    raw_values.extend(intake_summary.get("limitations") or [])
    raw_values.extend(bodyweight_summary.get("limitations") or [])
    raw_values.extend(readiness.get("limitations") or [])

    if bodyweight_summary.get("trend_direction") == "unavailable":
        raw_values.append("bodyweight_trend_unavailable")

    if readiness:
        if not readiness.get("minimum_window_met", True):
            raw_values.append("minimum_window_not_met")
        if not readiness.get("logging_quality_met", True):
            raw_values.append("logging_quality_not_met")
        if not readiness.get("bodyweight_trend_available", True):
            raw_values.append("bodyweight_trend_unavailable")
        if not readiness.get("goal_context_available", True):
            raw_values.append("goal_context_missing")
        if not readiness.get("training_context_available", True):
            raw_values.append("training_context_missing")

    friendly_values = []
    for raw_value in raw_values:
        friendly = trend_calibration_public_text(raw_value)
        if friendly and friendly not in friendly_values:
            friendly_values.append(friendly)

    return friendly_values


def render_trend_calibration_limitations(
    trend_response: dict,
    calibration_response: dict,
) -> None:
    limitations = trend_calibration_limitations(trend_response, calibration_response)

    with st.expander("Why calibration may be limited", expanded=False):
        if limitations:
            for limitation in limitations:
                st.caption(f"• {limitation}")
        else:
            st.caption(
                "No major limitations were reported for this trend window. "
                "This still does not mean targets were changed."
            )

        st.caption(
            "Calibration readiness is informational only. It does not estimate exact "
            "maintenance calories or mutate nutrition targets."
        )


def render_nutrition_trend_calibration_card(user_id: int) -> None:
    with st.expander("Trend & Calibration Readiness", expanded=False):
        st.caption(
            "Review nutrition trend evidence and calibration readiness. Targets remain "
            "formula-derived unless a future backend flow explicitly changes them."
        )

        end_date = selected_nutrition_summary_date_text(user_id)
        window_days = st.selectbox(
            "Trend window",
            options=[28, 14],
            index=0,
            key=f"nutrition_trend_calibration_window_days_{user_id}",
            format_func=lambda value: f"{value} days",
            help="Seeded QA scenarios use 2026-06-06 as the reference end date.",
        )

        try:
            trend_response = api_get(
                f"/nutrition/{user_id}/trend-window",
                params={"end_date": end_date, "window_days": window_days},
            )
        except requests.RequestException as exc:
            st.caption(
                "Nutrition trend window is not available yet. "
                f"{extract_api_error_message(exc)}"
            )
            return

        try:
            calibration_response = api_get(
                f"/nutrition/{user_id}/target-calibration",
                params={"end_date": end_date, "window_days": window_days},
            )
        except requests.RequestException as exc:
            st.caption(
                "Nutrition calibration readiness is not available yet. "
                f"{extract_api_error_message(exc)}"
            )
            developer_details(
                "Developer details: nutrition trend-window response",
                trend_response,
            )
            return

        if not trend_response.get("success"):
            st.caption("Nutrition trend window is not available for this date.")
            developer_details(
                "Developer details: nutrition trend-window response",
                trend_response,
            )
            return

        if not calibration_response.get("success"):
            st.caption(
                "Nutrition calibration readiness is not available for this date."
            )
            developer_details(
                "Developer details: nutrition target-calibration response",
                calibration_response,
            )
            return

        render_trend_window_summary(trend_response)
        render_bodyweight_trend_summary(trend_response)
        render_calibration_readiness_summary(trend_response, calibration_response)
        render_trend_calibration_limitations(trend_response, calibration_response)

        developer_details(
            "Developer details: nutrition trend-window response",
            trend_response,
        )
        developer_details(
            "Developer details: nutrition target-calibration response",
            calibration_response,
        )


def render_nutrition_section(user_id: int) -> None:
    st.header("Nutrition")
    st.caption(
        "Log clean foods first, then review backend-approved targets, suggestions, "
        "and nutrition explanations."
    )

    st.subheader("Quick Log Food")
    st.caption(
        "Search the clean canonical catalog, choose a food, enter grams, and log it "
        "without touching noisy source records."
    )
    st.markdown(
        """
        <div class="quick-log-panel">
            <div class="quick-log-title">Clean canonical food logging</div>
            <div class="quick-log-copy">Use the approved app-facing catalog first. Source-food fallback stays tucked away for edge cases.</div>
            <span class="quick-log-step">1 Search</span>
            <span class="quick-log-step">2 Select</span>
            <span class="quick-log-step">3 Log grams</span>
            <span class="quick-log-step">4 Review targets</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    canonical_results_key = "canonical_food_search_results"
    canonical_response_key = "canonical_food_search_response"
    canonical_error_key = "canonical_food_search_error"
    raw_fallback_query_key = "raw_food_fallback_query"

    with st.form("nutrition_canonical_food_search_form"):
        search_col, button_col = st.columns([4, 1])
        with search_col:
            food_query = st.text_input(
                "Search clean foods",
                value="",
                key="nutrition_canonical_food_query",
                placeholder="chicken breast, rice, egg, oats",
            )
        with button_col:
            st.write("")
            search_food = st.form_submit_button("Search", type="primary")

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
        st.success(f"Found {len(canonical_results)} clean canonical match(es).")

        canonical_options = {}
        used_canonical_labels = set()
        for food in canonical_results:
            if food.get("canonical_food_id") is None:
                continue
            label = unique_food_option_label(
                canonical_food_option_label(food),
                used_canonical_labels,
            )
            canonical_options[label] = food

        if canonical_options:
            with st.form("nutrition_log_canonical_food_form"):
                st.markdown("#### Select and log")
                select_col, grams_col, date_col, action_col = st.columns(
                    [2.4, 0.8, 1, 0.8]
                )
                with select_col:
                    selected_food_label = st.selectbox(
                        "Clean food",
                        list(canonical_options.keys()),
                        key="nutrition_selected_canonical_food",
                    )
                selected_food = canonical_options[selected_food_label]
                selected_food_name = selected_food.get("display_name", "Selected food")
                selected_food_type = humanize_label(selected_food.get("food_type"))
                selected_default_grams = selected_food.get("default_grams")
                selected_nutrients = canonical_food_nutrient_summary_text(selected_food)
                default_grams = float(selected_food.get("default_grams") or 100.0)

                try:
                    default_entry_date = datetime.fromisoformat(
                        selected_nutrition_summary_date_text(user_id)
                    ).date()
                except ValueError:
                    default_entry_date = datetime.now().date()

                with grams_col:
                    grams = st.number_input(
                        "Grams",
                        min_value=1.0,
                        value=default_grams,
                        step=5.0,
                        key="nutrition_canonical_grams",
                    )
                with date_col:
                    entry_date = st.date_input(
                        "Date",
                        value=default_entry_date,
                        key=f"nutrition_canonical_log_date_{user_id}",
                        help="Defaults to the Nutrition Today Summary date when available.",
                    )
                with action_col:
                    st.write("")
                    log_canonical_food = st.form_submit_button(
                        "Log",
                        type="primary",
                    )

                detail_parts = []
                if selected_food_type and selected_food_type != "Unknown":
                    detail_parts.append(selected_food_type)
                if selected_default_grams is not None:
                    detail_parts.append(f"default {selected_default_grams:g}g")
                if selected_nutrients and selected_nutrients != "Nutrients unavailable":
                    detail_parts.append(
                        f"per 100g: {selected_nutrients.replace(' per 100g', '')}"
                    )

                st.caption(f"Selected: {selected_food_name}")
                if detail_parts:
                    st.caption(" · ".join(detail_parts))
                st.caption(
                    "Nutrition values come from the approved canonical food record."
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
                    st.error(f"Food logging failed: {extract_api_error_message(exc)}")
                else:
                    if data.get("success", True):
                        st.success(f"Logged {selected_food_name}.")
                        st.session_state[canonical_results_key] = []
                        st.session_state[canonical_response_key] = {}
                        st.session_state[canonical_error_key] = None
                        st.session_state.food_search_results = []
                        st.rerun()
                    else:
                        st.error(data.get("message", "Food logging failed."))

        with st.expander("Clean matches from the canonical catalog", expanded=False):
            rows = []
            for index, food in enumerate(canonical_results[:10], start=1):
                display_name = food.get("display_name") or "Unknown food"
                food_type = humanize_label(food.get("food_type"))
                default_serving = canonical_food_default_serving_text(food)
                nutrient_summary = canonical_food_nutrient_summary_text(food)
                rows.append(
                    {
                        "Match": f"{index}. {display_name}",
                        "Type": "" if food_type == "Unknown" else food_type,
                        "Default": default_serving.replace("Default: ", ""),
                        "Per 100g": nutrient_summary.replace(" per 100g", ""),
                    }
                )
            if rows:
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

        developer_details(
            "Developer details: canonical food search response",
            canonical_response,
        )
    elif search_food and not canonical_error:
        st.caption("No clean food match found yet. Use existing food database for now.")
    else:
        st.caption(
            "Try common seeded foods like chicken breast, rice, egg, oats, banana, or Greek yogurt."
        )

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
                        f"Existing food search failed: {extract_api_error_message(exc)}"
                    )
                else:
                    st.session_state.food_search_results = data.get("foods", [])
                    if not st.session_state.food_search_results:
                        st.caption(
                            "No existing foods found. Try a simpler search term."
                        )

        if st.session_state.food_search_results:
            food_options = {}
            used_raw_labels = set()
            for food in st.session_state.food_search_results:
                label = unique_food_option_label(
                    raw_food_option_label(food),
                    used_raw_labels,
                )
                food_options[label] = food

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
                    "Use this fallback only when a clean canonical food is not available. "
                    "Clean foods remain the preferred logging path."
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
                    st.error(f"Food logging failed: {extract_api_error_message(exc)}")
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

    render_nutrition_food_suggestions_card(user_id)

    render_nutrition_explanation_preview_card(user_id)
    render_nutrition_explanation_runtime_debug_view(user_id)

    render_nutrition_trend_calibration_card(user_id)

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
    st.caption(
        "Run the full sectionized report when you want the complete validated health "
        "summary. Deterministic fallback and provider gates remain mandatory."
    )

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


def weekly_coach_summary_qa_user_options() -> dict[int, str]:
    from services.weekly_coach_summary_qa_data_service import QA_USER_LABELS

    return dict(QA_USER_LABELS)


def weekly_coach_summary_qa_range_presets() -> dict[str, dict[str, date | str]]:
    from services.weekly_coach_summary_qa_data_service import (
        DEFAULT_QA_DATE_RANGE_PRESET_KEY,
        QA_DATE_RANGE_PRESET_LABELS,
        QA_DATE_RANGE_PRESETS,
        qa_range_preset_dates,
    )

    presets: dict[str, dict[str, date | str]] = {}
    for key, (start_date, end_date) in QA_DATE_RANGE_PRESETS.items():
        presets[key] = {
            "label": QA_DATE_RANGE_PRESET_LABELS[key],
            "start_date": date.fromisoformat(start_date),
            "end_date": date.fromisoformat(end_date),
        }
    default_start, default_end = qa_range_preset_dates(DEFAULT_QA_DATE_RANGE_PRESET_KEY)
    presets["custom"] = {
        "label": QA_DATE_RANGE_PRESET_LABELS["custom"],
        "start_date": default_start,
        "end_date": default_end,
    }
    return presets


def _weekly_coach_summary_selected_range(
    preset_key: str,
    start_date_value: date,
    end_date_value: date,
) -> tuple[date, date]:
    from services.weekly_coach_summary_qa_data_service import qa_range_preset_dates

    if preset_key == "custom":
        return start_date_value, end_date_value
    return qa_range_preset_dates(preset_key)


def _render_weekly_coach_summary_qa_inventory(inventory: dict[str, object]) -> None:
    metadata_rows = [
        {"Field": "User ID", "Value": inventory.get("user_id")},
        {"Field": "Scenario", "Value": inventory.get("scenario")},
        {"Field": "Selected Start", "Value": inventory.get("start_date")},
        {"Field": "Selected End", "Value": inventory.get("end_date")},
        {"Field": "Available Start", "Value": inventory.get("available_start_date")},
        {"Field": "Available End", "Value": inventory.get("available_end_date")},
        {"Field": "Data Quality", "Value": inventory.get("data_quality_label")},
        {"Field": "Source", "Value": inventory.get("source")},
        {
            "Field": "Provider Free",
            "Value": str(inventory.get("deterministic_provider_free")).lower(),
        },
        {"Field": "Public Safe", "Value": str(inventory.get("public_safe")).lower()},
        {"Field": "Displayable", "Value": str(inventory.get("displayable")).lower()},
    ]
    st.markdown("**Selected QA Range Inventory**")
    st.dataframe(pd.DataFrame(metadata_rows), width="stretch", hide_index=True)

    fact_counts = inventory.get("fact_counts") or {}
    fact_date_bounds = inventory.get("fact_date_bounds") or {}
    distinct_logged_days = inventory.get("distinct_logged_days") or {}
    completed_counts = inventory.get("completed_counts") or {}
    fact_rows = []
    if isinstance(fact_counts, dict):
        for domain, count in fact_counts.items():
            bounds = (
                fact_date_bounds.get(domain, {})
                if isinstance(fact_date_bounds, dict)
                else {}
            )
            fact_rows.append(
                {
                    "Domain": domain,
                    "Count": count,
                    "Distinct Days": (
                        distinct_logged_days.get(domain)
                        if isinstance(distinct_logged_days, dict)
                        else None
                    ),
                    "Completed": (
                        completed_counts.get(domain)
                        if isinstance(completed_counts, dict)
                        else None
                    ),
                    "Min Date": (
                        bounds.get("min_date") if isinstance(bounds, dict) else None
                    ),
                    "Max Date": (
                        bounds.get("max_date") if isinstance(bounds, dict) else None
                    ),
                    "Reason": (
                        bounds.get("reason") if isinstance(bounds, dict) else None
                    ),
                }
            )
    if fact_rows:
        st.dataframe(pd.DataFrame(fact_rows), width="stretch", hide_index=True)

    diagnosis_codes = inventory.get("diagnosis_codes") or []
    limitations = inventory.get("limitations") or []
    st.markdown("**Diagnosis Codes:**")
    st.write(", ".join(diagnosis_codes) or "None")
    st.markdown("**Limitations:**")
    st.write(", ".join(limitations) or "None")

    if "selected_range_out_of_bounds" in diagnosis_codes:
        st.warning(
            "Selected range has no data for this user. Available data exists from "
            f"{inventory.get('available_start_date')} to "
            f"{inventory.get('available_end_date')}."
        )
    elif not inventory.get("selected_range_has_data"):
        st.warning("Selected range has no data for this user.")


def _render_weekly_coach_summary_sections(sections: dict[str, object]) -> None:
    st.markdown("**Headline:**")
    st.write(sections["headline"])
    st.markdown("**Weekly Overview:**")
    st.write(sections["weekly_overview"])
    st.markdown("**Recovery Observation:**")
    st.write(sections["recovery_observation"])
    st.markdown("**Nutrition Observation:**")
    st.write(sections["nutrition_observation"])
    st.markdown("**Training Observation:**")
    st.write(sections["training_observation"])
    st.markdown("**Primary Pattern:**")
    st.write(sections["primary_pattern"])
    st.markdown("**Recommended Focus:**")
    st.write(sections["recommended_focus"])
    st.markdown("**Next Week Guidance:**")
    st.write(sections["next_week_guidance"])


def _weekly_coach_summary_elapsed_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 2)


def _store_weekly_coach_summary_timing(
    cache_key: str,
    action: str,
    timings: dict[str, float],
) -> None:
    timing_cache = st.session_state.weekly_coach_summary_timing_by_user
    timing_cache[cache_key] = {"action": action, **timings}


def _render_weekly_coach_summary_timing(cache_key: str) -> None:
    timings = st.session_state.weekly_coach_summary_timing_by_user.get(cache_key)
    if not timings:
        return

    st.markdown("**Weekly Coach Summary Timing:**")
    timing_rows = [
        {"Step": key.replace("_", " ").title(), "Milliseconds": value}
        for key, value in timings.items()
        if key != "action"
    ]
    st.caption(f"Last measured action: {timings.get('action', 'unknown')}")
    if timing_rows:
        st.dataframe(pd.DataFrame(timing_rows), width="stretch", hide_index=True)


def weekly_coach_summary_streamlit_fragment(function):
    """Use Streamlit fragment reruns when available to avoid full-app rerender latency.

    Streamlit tabs execute all tab bodies during a normal rerun. The Weekly Coach
    Summary Developer Mode panel has isolated button interactions, so fragment
    reruns are a safe targeted fix: clicks inside this panel rerun only this panel
    on Streamlit versions that support st.fragment. Older Streamlit versions fall
    back to normal behavior without changing product boundaries.
    """

    fragment = getattr(st, "fragment", None)
    if callable(fragment):
        return fragment(function)
    return function


@weekly_coach_summary_streamlit_fragment
def render_weekly_coach_summary_developer_inspection(user_id: int) -> None:
    if not st.session_state.get("developer_mode", False):
        return

    from services.weekly_coach_summary_qa_context_service import (
        build_weekly_summary_context_from_qa_range,
        weekly_summary_context_to_safe_metadata,
    )
    from services.weekly_coach_summary_qa_data_service import (
        DEFAULT_QA_DATE_RANGE_PRESET_KEY,
        DEFAULT_QA_DATE_RANGE_USER_ID,
        inspect_weekly_summary_qa_range,
        qa_date_range_cache_key,
    )

    panel_start = perf_counter()
    st.subheader("Developer Mode: Weekly Coach Summary QA Date Range Debug")
    st.caption(
        "Developer Mode-only Weekly Coach Summary QA inspection. Deterministic "
        "actions and provider preview actions are manual, selected user/date "
        "values are typed, and normal/default UI remains unchanged."
    )

    user_options = weekly_coach_summary_qa_user_options()
    user_ids = list(user_options.keys())
    selected_user_id = st.selectbox(
        "QA user",
        options=user_ids,
        index=user_ids.index(DEFAULT_QA_DATE_RANGE_USER_ID),
        format_func=lambda option: user_options[int(option)],
        key="weekly_coach_summary_qa_user_id",
    )
    range_presets = weekly_coach_summary_qa_range_presets()
    preset_keys = list(range_presets.keys())
    selected_preset_key = st.selectbox(
        "Range preset",
        options=preset_keys,
        index=preset_keys.index(DEFAULT_QA_DATE_RANGE_PRESET_KEY),
        format_func=lambda option: str(range_presets[str(option)]["label"]),
        key="weekly_coach_summary_qa_range_preset",
    )
    selected_preset = range_presets[selected_preset_key]
    is_custom_range = selected_preset_key == "custom"

    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date_input = st.date_input(
            "Start date",
            value=selected_preset["start_date"],
            disabled=not is_custom_range,
            key=f"weekly_coach_summary_qa_start_date_{selected_preset_key}",
        )
    with date_col2:
        end_date_input = st.date_input(
            "End date",
            value=selected_preset["end_date"],
            disabled=not is_custom_range,
            key=f"weekly_coach_summary_qa_end_date_{selected_preset_key}",
        )

    selected_start_date, selected_end_date = _weekly_coach_summary_selected_range(
        selected_preset_key,
        start_date_input,
        end_date_input,
    )
    range_key = qa_date_range_cache_key(
        int(selected_user_id),
        selected_start_date,
        selected_end_date,
    )

    inventory_cache = st.session_state.weekly_coach_summary_qa_inventory_by_range
    preview_cache = st.session_state.weekly_coach_summary_preview_by_user
    persisted_cache = st.session_state.weekly_coach_summary_persisted_by_user
    message_cache = st.session_state.weekly_coach_summary_message_by_user
    provider_preview_cache = (
        st.session_state.weekly_coach_summary_provider_preview_by_range
    )

    st.caption(
        "Selected QA range: "
        f"user {selected_user_id}, {selected_start_date.isoformat()} through "
        f"{selected_end_date.isoformat()}."
    )

    inspect_col, generate_col = st.columns(2)
    with inspect_col:
        if st.button(
            "Inspect selected QA range",
            key="weekly_coach_summary_inspect_selected_range_button",
        ):
            inspect_start = perf_counter()
            inventory = inspect_weekly_summary_qa_range(
                user_id=int(selected_user_id),
                start_date=selected_start_date,
                end_date=selected_end_date,
            )
            inventory_cache[range_key] = inventory.to_dict()
            message_cache[range_key] = "Selected QA range inventory inspected."
            _store_weekly_coach_summary_timing(
                range_key,
                "inspect_selected_range",
                {
                    "inspect_selected_range_ms": _weekly_coach_summary_elapsed_ms(
                        inspect_start
                    )
                },
            )

    with generate_col:
        if st.button(
            "Generate deterministic weekly summary from selected QA range",
            key="weekly_coach_summary_generate_selected_range_button",
        ):
            action_start = perf_counter()
            inventory_start = perf_counter()
            inventory = inspect_weekly_summary_qa_range(
                user_id=int(selected_user_id),
                start_date=selected_start_date,
                end_date=selected_end_date,
            )
            inventory_ms = _weekly_coach_summary_elapsed_ms(inventory_start)
            context_start = perf_counter()
            context = build_weekly_summary_context_from_qa_range(
                user_id=int(selected_user_id),
                start_date=selected_start_date,
                end_date=selected_end_date,
            )
            context_ms = _weekly_coach_summary_elapsed_ms(context_start)
            generation_start = perf_counter()
            summary = generate_approved_weekly_summary(context)
            generation_ms = _weekly_coach_summary_elapsed_ms(generation_start)
            sections_start = perf_counter()
            sections = approved_weekly_summary_to_public_sections(summary)
            sections_ms = _weekly_coach_summary_elapsed_ms(sections_start)
            inventory_cache[range_key] = inventory.to_dict()
            preview_cache[range_key] = {
                "range_key": range_key,
                "inventory": inventory.to_dict(),
                "context_metadata": weekly_summary_context_to_safe_metadata(context),
                "period": context.period.to_dict(),
                "summary": summary,
                "sections": sections,
            }
            message_cache[range_key] = (
                "Approved deterministic weekly summary generated."
            )
            _store_weekly_coach_summary_timing(
                range_key,
                "generate_selected_range",
                {
                    "inventory_ms": inventory_ms,
                    "context_build_ms": context_ms,
                    "deterministic_generation_ms": generation_ms,
                    "section_build_ms": sections_ms,
                    "total_action_ms": _weekly_coach_summary_elapsed_ms(action_start),
                },
            )

    cached_inventory = inventory_cache.get(range_key)
    cached_preview = preview_cache.get(range_key)
    if cached_inventory:
        if cached_preview:
            st.success("Selected QA range inventory used for this generated summary.")
        else:
            st.success(message_cache.get(range_key, "Selected QA range inspected."))
        _render_weekly_coach_summary_qa_inventory(cached_inventory)

    if cached_preview:
        sections = cached_preview["sections"]
        period = cached_preview["period"]
        context_metadata = cached_preview.get("context_metadata") or {}
        st.success(
            message_cache.get(
                range_key,
                "Approved deterministic weekly summary ready.",
            )
        )
        st.caption("Generated from selected QA date-range context.")
        st.write(f"**Period:** {period['week_start']} to {period['week_end']}")
        st.markdown("**Selected-Range Persistence Controls:**")
        save_col, load_col = st.columns(2)
        with save_col:
            if st.button(
                "Save selected-range approved summary",
                key="weekly_coach_summary_save_selected_range_button",
            ):
                save_start = perf_counter()
                try:
                    saved = save_approved_weekly_summary(
                        summary=cached_preview["summary"],
                        user_id=int(selected_user_id),
                        week_start=period["week_start"],
                        week_end=period["week_end"],
                        sanitized_metadata={
                            "provider_attempted": False,
                            "fallback_used": sections["source"]
                            == "deterministic_fallback",
                            "fallback_reason": (
                                "deterministic fallback"
                                if sections["source"] == "deterministic_fallback"
                                else None
                            ),
                            "parse_status": "not_attempted",
                            "validation_status": "approved",
                            "final_summary_source": sections["source"],
                            "generated_by": (
                                "developer_mode_weekly_summary_qa_date_range_debug"
                            ),
                        },
                    )
                except WeeklyCoachSummaryPersistenceError:
                    st.error(
                        "Weekly summary was not saved because it failed safety checks."
                    )
                else:
                    persisted_cache[range_key] = saved
                    _store_weekly_coach_summary_timing(
                        range_key,
                        "save_selected_range",
                        {"save_ms": _weekly_coach_summary_elapsed_ms(save_start)},
                    )
                    st.success(f"Saved weekly summary record {saved.record_id}.")
        with load_col:
            if st.button(
                "Load latest selected-range summary",
                key="weekly_coach_summary_load_selected_range_button",
            ):
                load_start = perf_counter()
                latest = get_latest_approved_weekly_summary(
                    user_id=int(selected_user_id),
                    week_start=period["week_start"],
                    week_end=period["week_end"],
                )
                if latest is None:
                    _store_weekly_coach_summary_timing(
                        range_key,
                        "load_selected_range_empty",
                        {
                            "load_latest_ms": _weekly_coach_summary_elapsed_ms(
                                load_start
                            )
                        },
                    )
                    st.warning(
                        "No persisted approved weekly summary found for this "
                        "selected user/range."
                    )
                else:
                    persisted_cache[range_key] = latest
                    _store_weekly_coach_summary_timing(
                        range_key,
                        "load_selected_range",
                        {
                            "load_latest_ms": _weekly_coach_summary_elapsed_ms(
                                load_start
                            )
                        },
                    )
                    st.success(f"Loaded weekly summary record {latest.record_id}.")
        if context_metadata:
            st.markdown("**Selected-Range Context Metadata:**")
            context_rows = [
                {"Field": "User ID", "Value": context_metadata.get("user_id")},
                {"Field": "Scenario", "Value": context_metadata.get("scenario")},
                {"Field": "Start Date", "Value": context_metadata.get("start_date")},
                {"Field": "End Date", "Value": context_metadata.get("end_date")},
                {"Field": "Source", "Value": context_metadata.get("source")},
                {"Field": "Confidence", "Value": context_metadata.get("confidence")},
                {
                    "Field": "Data Quality Limited",
                    "Value": str(context_metadata.get("data_quality_limited")).lower(),
                },
                {
                    "Field": "Deterministic Provider Free",
                    "Value": str(
                        context_metadata.get("deterministic_provider_free")
                    ).lower(),
                },
            ]
            st.dataframe(
                pd.DataFrame(context_rows),
                width="stretch",
                hide_index=True,
            )
        metadata_rows = [
            {"Field": "User ID", "Value": period["user_id"]},
            {"Field": "Source", "Value": sections["source"]},
            {"Field": "Confidence", "Value": sections["confidence"]},
            {"Field": "Public Safe", "Value": str(sections["public_safe"]).lower()},
            {"Field": "Displayable", "Value": str(sections["displayable"]).lower()},
            {"Field": "Provider Attempted", "Value": "false"},
        ]
        st.dataframe(pd.DataFrame(metadata_rows), width="stretch", hide_index=True)
        _render_weekly_coach_summary_sections(sections)
        st.markdown("**Reason Codes:**")
        st.write(", ".join(sections["reason_codes"]) or "None")
        st.markdown("**Limitations:**")
        st.write(", ".join(sections["limitations"]) or "None")

        st.markdown("**Weekly Coach Summary Provider Preview:**")
        from services.weekly_coach_summary_provider_service import (
            generate_weekly_summary_provider_preview,
            resolve_weekly_summary_provider_preview_config,
            weekly_provider_preview_result_to_display_rows,
        )

        provider_config = resolve_weekly_summary_provider_preview_config()
        provider_config_payload = provider_config.to_safe_dict()
        st.caption(
            "Developer Mode only. Manual provider preview. Deterministic fallback remains authoritative."
        )
        lifecycle_policy = provider_config_payload["lifecycle_policy"]
        lifecycle_rows = [
            {"Field": "Provider model", "Value": provider_config.model_name},
            {"Field": "Preview enabled", "Value": str(provider_config.enabled).lower()},
            {
                "Field": "Keep alive policy",
                "Value": lifecycle_policy.get("keep_alive_policy"),
            },
            {
                "Field": "Keep alive value",
                "Value": str(lifecycle_policy.get("keep_alive_value")),
            },
            {
                "Field": "Unload after request",
                "Value": str(lifecycle_policy.get("unload_after_request")).lower(),
            },
        ]
        st.dataframe(pd.DataFrame(lifecycle_rows), width="stretch", hide_index=True)
        if not provider_config.enabled:
            st.warning(
                "Provider preview is disabled. Set FITNESS_AI_WEEKLY_SUMMARY_PROVIDER_PREVIEW_ENABLED=true in the Streamlit runtime environment to run the manual qwen2.5:3b preview."
            )
        if st.button(
            "Generate provider candidate — qwen2.5:3b",
            key="weekly_coach_summary_generate_provider_candidate_button",
            disabled=not provider_config.enabled,
        ):
            provider_start = perf_counter()
            context = build_weekly_summary_context_from_qa_range(
                user_id=int(selected_user_id),
                start_date=selected_start_date,
                end_date=selected_end_date,
            )
            provider_result = generate_weekly_summary_provider_preview(
                context=context,
                deterministic_summary=cached_preview["summary"],
                config=provider_config,
            )
            provider_preview_cache[range_key] = provider_result.to_dict()
            _store_weekly_coach_summary_timing(
                range_key,
                "provider_preview",
                {
                    "provider_preview_ms": _weekly_coach_summary_elapsed_ms(
                        provider_start
                    )
                },
            )

        provider_preview = provider_preview_cache.get(range_key)
        if provider_preview:
            st.markdown("**Provider Preview Result:**")
            st.dataframe(
                pd.DataFrame(
                    weekly_provider_preview_result_to_display_rows(provider_preview)
                ),
                width="stretch",
                hide_index=True,
            )
            if provider_preview.get("validation_status") == "approved":
                st.success(
                    "Provider candidate parsed and validated for Developer Mode preview."
                )
                provider_sections = provider_preview["approved_sections"]
                _render_weekly_coach_summary_sections(provider_sections)
            else:
                st.warning(
                    provider_preview.get(
                        "safe_message",
                        "Provider preview fell back to deterministic summary.",
                    )
                )
                errors = provider_preview.get("validation_errors") or []
                if errors:
                    st.markdown("**Provider Preview Validation Notes:**")
                    st.write(", ".join(errors))

    persisted = persisted_cache.get(range_key)
    if persisted:
        st.markdown("**Persisted Weekly Coach Summary Metadata:**")
        persisted_rows = [
            {"Field": "Record ID", "Value": persisted.record_id},
            {"Field": "User ID", "Value": persisted.user_id},
            {"Field": "Week Start", "Value": persisted.week_start},
            {"Field": "Week End", "Value": persisted.week_end},
            {"Field": "Source", "Value": persisted.source},
            {"Field": "Confidence", "Value": persisted.confidence},
            {"Field": "Public Safe", "Value": str(persisted.public_safe).lower()},
            {"Field": "Displayable", "Value": str(persisted.displayable).lower()},
            {"Field": "Stale", "Value": str(persisted.stale).lower()},
            {"Field": "Expired", "Value": str(persisted.expired).lower()},
            {"Field": "Created At", "Value": persisted.created_at},
        ]
        st.dataframe(pd.DataFrame(persisted_rows), width="stretch", hide_index=True)
        st.markdown("**Persisted Reason Codes:**")
        st.write(", ".join(persisted.reason_codes) or "None")
        st.markdown("**Persisted Limitations:**")
        st.write(", ".join(persisted.limitations) or "None")
        with st.expander("Loaded approved summary sections", expanded=False):
            _render_weekly_coach_summary_sections(
                approved_weekly_summary_to_public_sections(persisted.approved_summary)
            )

    _store_weekly_coach_summary_timing(
        range_key,
        "panel_render",
        {
            **st.session_state.weekly_coach_summary_timing_by_user.get(range_key, {}),
            "panel_render_ms": _weekly_coach_summary_elapsed_ms(panel_start),
        },
    )
    _render_weekly_coach_summary_timing(range_key)


def _developer_mode_latency_elapsed_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 2)


def _record_developer_mode_latency(label: str, start: float) -> None:
    timings = st.session_state.setdefault("developer_mode_latency_timing", {})
    timings[label] = _developer_mode_latency_elapsed_ms(start)


def _developer_mode_latency_log(label: str, start: float | None = None) -> float:
    now = perf_counter()
    if start is None:
        print(f"[developer-latency] {label}: start", flush=True)
        return now

    elapsed_ms = round((now - start) * 1000, 2)
    print(f"[developer-latency] {label}: {elapsed_ms} ms", flush=True)
    return now


def _render_developer_mode_latency_timing() -> None:
    timings = st.session_state.get("developer_mode_latency_timing") or {}
    if not timings:
        return

    rows = [
        {"Step": key.replace("_", " ").title(), "Milliseconds": value}
        for key, value in timings.items()
    ]
    with st.expander("Developer Mode Timing", expanded=False):
        st.caption(
            "Safe aggregate timing only. Developer tools are lazy-loaded; "
            "diagnostics and debug outputs run only after explicit actions."
        )
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def _runtime_diagnostic_table(mapping: dict) -> None:
    rows = [
        {"Field": key, "Value": "" if value is None else str(value)}
        for key, value in mapping.items()
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def _runtime_qa_seed_rows(diagnostics: list[dict]) -> list[dict]:
    rows = []
    for user in diagnostics:
        recovery = user.get("recovery") or {}
        nutrition = user.get("nutrition") or {}
        workouts = user.get("workouts") or {}
        actual_sets = user.get("actual_sets") or {}
        rows.append(
            {
                "User ID": user.get("user_id"),
                "Exists": user.get("user_exists"),
                "Scenario": user.get("scenario"),
                "Recovery Count": recovery.get("row_count"),
                "Recovery Min": recovery.get("min_date"),
                "Recovery Max": recovery.get("max_date"),
                "Nutrition Count": nutrition.get("row_count"),
                "Nutrition Min": nutrition.get("min_date"),
                "Nutrition Max": nutrition.get("max_date"),
                "Workout Count": workouts.get("row_count"),
                "Workout Min": workouts.get("min_date"),
                "Workout Max": workouts.get("max_date"),
                "Actual Set Count": actual_sets.get("row_count"),
                "Actual Set Min": actual_sets.get("min_date"),
                "Actual Set Max": actual_sets.get("max_date"),
            }
        )
    return rows


def render_runtime_db_source_verification() -> None:
    if not st.session_state.get("developer_mode", False):
        return

    st.subheader("Runtime / DB Source Verification")
    st.caption(
        "Developer Mode-only diagnostic. Shows sanitized runtime identity, "
        "database source, and QA seed aggregate counts/date bounds. No raw rows, "
        "secrets, provider output, prompts, or stack traces are displayed."
    )
    st.info(
        "Developer diagnostics are lazy-loaded. Click refresh to query the active "
        "runtime/database; opening the Developer tab alone does not run this query."
    )

    if "runtime_db_diagnostics" not in st.session_state:
        st.session_state.runtime_db_diagnostics = None

    refresh = st.button(
        "Refresh runtime / DB diagnostics",
        key="runtime_db_diagnostics_refresh_button",
    )
    if refresh:
        refresh_start = perf_counter()
        st.session_state.runtime_db_diagnostics = build_runtime_db_diagnostics(
            api_base_url=API_BASE_URL
        )
        _record_developer_mode_latency(
            "runtime_db_diagnostics_refresh_ms", refresh_start
        )

    diagnostics = st.session_state.get("runtime_db_diagnostics")
    if not diagnostics:
        st.info(
            "No runtime diagnostics loaded yet. Click refresh to inspect runtime/DB source."
        )
        return

    warnings = diagnostics.get("warnings") or []
    for warning in warnings:
        st.warning(warning)

    st.markdown("**Runtime Identity**")
    runtime_identity = diagnostics.get("runtime_identity") or {}
    _runtime_diagnostic_table(
        {
            "git_commit_short": runtime_identity.get("git_commit_short"),
            "git_commit_full": runtime_identity.get("git_commit_full"),
            "git_branch": runtime_identity.get("git_branch"),
            "dirty_working_tree": runtime_identity.get("dirty_working_tree"),
            "repository_root": runtime_identity.get("repository_root"),
            "current_working_directory": runtime_identity.get(
                "current_working_directory"
            ),
            "python_executable": runtime_identity.get("python_executable"),
            "python_version": runtime_identity.get("python_version"),
            "platform": runtime_identity.get("platform"),
        }
    )

    st.markdown("**Database Source**")
    database_source = diagnostics.get("database_source") or {}
    _runtime_diagnostic_table(
        {
            "resolved_database_path": database_source.get("resolved_database_path"),
            "database_exists": database_source.get("database_exists"),
            "database_file_size_bytes": database_source.get("database_file_size_bytes"),
            "database_modified_at": database_source.get("database_modified_at"),
            "sqlite_connectable": database_source.get("sqlite_connectable"),
            "available_table_count": database_source.get("available_table_count"),
            "relevant_tables_found": ", ".join(
                database_source.get("relevant_tables_found") or []
            ),
            "error_category": database_source.get("error_category"),
        }
    )

    st.markdown("**Streamlit / FastAPI Context**")
    streamlit_fastapi = diagnostics.get("streamlit_fastapi") or {}
    _runtime_diagnostic_table(
        {
            "configured_api_base_url": streamlit_fastapi.get("configured_api_base_url"),
            "diagnostic_path": streamlit_fastapi.get("diagnostic_path"),
        }
    )

    st.markdown("**QA Seed Presence**")
    qa_rows = _runtime_qa_seed_rows(diagnostics.get("qa_seed_diagnostics") or [])
    if qa_rows:
        st.dataframe(pd.DataFrame(qa_rows), width="stretch", hide_index=True)
    else:
        st.info("No QA seed diagnostics were returned.")

    with st.expander(
        "Developer details: sanitized runtime diagnostics", expanded=False
    ):
        st.json(diagnostics)


def render_developer_section(user_id: int) -> None:
    developer_terminal_start = _developer_mode_latency_log("developer_section_enter")
    developer_render_start = perf_counter()
    st.header("Developer")
    st.caption(
        "Developer details are hidden from the main UI unless Developer Mode is on."
    )

    if not st.session_state.get("developer_mode", False):
        st.info("Turn on Developer Mode in the sidebar to show raw backend responses.")
        return

    st.caption(
        "Developer tools are lazy-loaded. Opening this tab renders controls only; "
        "diagnostics, QA inspection, and summary generation require explicit buttons."
    )

    session_state_terminal_start = _developer_mode_latency_log(
        "session_state_snapshot_start"
    )
    session_state_start = perf_counter()
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
            "workout_daily_state": (
                st.session_state.workout_daily_state_response or {}
            ).get("workout_daily_state"),
            "has_runtime_db_diagnostics": st.session_state.get("runtime_db_diagnostics")
            is not None,
        }
    )
    _record_developer_mode_latency(
        "session_state_snapshot_render_ms", session_state_start
    )
    _developer_mode_latency_log(
        "session_state_snapshot_done", session_state_terminal_start
    )

    runtime_panel_start = perf_counter()
    runtime_terminal_start = _developer_mode_latency_log(
        "runtime_db_source_panel_start"
    )
    render_runtime_db_source_verification()
    _developer_mode_latency_log("runtime_db_source_panel_done", runtime_terminal_start)
    _record_developer_mode_latency(
        "runtime_db_source_panel_render_ms", runtime_panel_start
    )

    weekly_panel_start = perf_counter()
    weekly_terminal_start = _developer_mode_latency_log(
        "weekly_coach_summary_panel_start"
    )
    render_weekly_coach_summary_developer_inspection(user_id)
    _developer_mode_latency_log(
        "weekly_coach_summary_panel_done", weekly_terminal_start
    )
    _record_developer_mode_latency(
        "weekly_coach_summary_panel_render_ms", weekly_panel_start
    )

    quick_endpoint_start = perf_counter()
    quick_terminal_start = _developer_mode_latency_log("quick_endpoint_panel_start")
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
    _record_developer_mode_latency(
        "quick_endpoint_panel_render_ms", quick_endpoint_start
    )
    _developer_mode_latency_log("quick_endpoint_panel_done", quick_terminal_start)

    _record_developer_mode_latency("developer_tab_render_ms", developer_render_start)
    _developer_mode_latency_log("developer_section_done", developer_terminal_start)
    _render_developer_mode_latency_timing()


# =====================================
# Main Navigation
# =====================================

MAIN_NAVIGATION_PAGES = [
    "Today",
    "Workout",
    "Nutrition",
    "History",
    "Reports",
    "Developer",
]


def render_main_navigation(user_id: int) -> None:
    """Render only the selected top-level page body.

    Streamlit tabs eagerly execute every tab body on each rerun. On the Linux
    runtime this made opening Developer Mode wait for Workout and History to
    finish expensive cold renders first. This radio-based navigation keeps the
    same top-level sections but executes exactly one selected page per rerun.
    """

    navigation_override = st.session_state.get("main_navigation_page_override")
    if navigation_override in MAIN_NAVIGATION_PAGES:
        st.session_state.main_navigation_page = navigation_override
        st.session_state.main_navigation_page_override = None

    selected_page = st.radio(
        "Main navigation",
        options=MAIN_NAVIGATION_PAGES,
        horizontal=True,
        key="main_navigation_page",
    )

    if selected_page == "Today":
        today_tab_start = _developer_mode_latency_log("today_tab_render_start")
        render_today_section(user_id)
        _developer_mode_latency_log("today_tab_render_done", today_tab_start)
    elif selected_page == "Workout":
        workout_tab_start = _developer_mode_latency_log("workout_tab_render_start")
        render_workout_plan_section(user_id)
        _developer_mode_latency_log("workout_tab_render_done", workout_tab_start)
    elif selected_page == "Nutrition":
        nutrition_tab_start = _developer_mode_latency_log("nutrition_tab_render_start")
        render_nutrition_section(user_id)
        _developer_mode_latency_log("nutrition_tab_render_done", nutrition_tab_start)
    elif selected_page == "History":
        history_tab_start = _developer_mode_latency_log("history_tab_render_start")
        render_history_section(user_id)
        _developer_mode_latency_log("history_tab_render_done", history_tab_start)
    elif selected_page == "Reports":
        reports_tab_start = _developer_mode_latency_log("reports_tab_render_start")
        render_reports_section(user_id)
        _developer_mode_latency_log("reports_tab_render_done", reports_tab_start)
    elif selected_page == "Developer":
        developer_tab_start = _developer_mode_latency_log(
            "developer_tab_container_render_start"
        )
        render_developer_section(user_id)
        _developer_mode_latency_log(
            "developer_tab_container_render_done", developer_tab_start
        )
    else:
        st.error("Unknown navigation page selected.")


render_main_navigation(user_id)

# Portfolio visual tightening v4 — garnet/gold portfolio palette
st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(206, 184, 136, 0.15);
        border-radius: 0.7rem;
        padding: 0.55rem 0.65rem;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.78rem;
        color: #cdbf9f;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.15rem;
    }
    .portfolio-card {
        border: 1px solid rgba(206, 184, 136, 0.20);
        border-radius: 0.85rem;
        padding: 0.72rem 0.82rem;
        background: linear-gradient(180deg, rgba(39, 24, 32, 0.82), rgba(15, 23, 42, 0.46));
        margin-bottom: 0.55rem;
    }
    .portfolio-card-accent { border-left: 4px solid #CEB888; }
    .portfolio-card-green { border-left: 4px solid #CEB888; }
    .portfolio-card-amber { border-left: 4px solid #F2C75C; }
    .portfolio-card-purple { border-left: 4px solid #782F40; }
    .portfolio-eyebrow {
        color: #CEB888;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 750;
        margin-bottom: 0.25rem;
    }
    .portfolio-title {
        font-size: 1.02rem;
        font-weight: 750;
        line-height: 1.2;
        margin-bottom: 0.28rem;
        color: #fff8e6;
    }
    .portfolio-body {
        font-size: 0.86rem;
        line-height: 1.35;
        color: #e5dcc6;
        margin-bottom: 0.26rem;
    }
    .portfolio-chip {
        display: inline-block;
        border-radius: 999px;
        padding: 0.12rem 0.45rem;
        margin: 0.08rem 0.15rem 0.08rem 0;
        font-size: 0.72rem;
        font-weight: 650;
        color: #fff8e6;
        background: rgba(120, 47, 64, 0.22);
        border: 1px solid rgba(206, 184, 136, 0.30);
    }
    .portfolio-chip-green {
        color: #fff8e6;
        background: rgba(206, 184, 136, 0.16);
        border-color: rgba(206, 184, 136, 0.42);
    }
    .portfolio-chip-amber {
        color: #fff3c4;
        background: rgba(242, 199, 92, 0.14);
        border-color: rgba(242, 199, 92, 0.34);
    }
    .portfolio-chip-purple {
        color: #ffe9ef;
        background: rgba(120, 47, 64, 0.28);
        border-color: rgba(206, 184, 136, 0.24);
    }
    .portfolio-muted {
        color: #b9ad92;
        font-size: 0.78rem;
        margin-top: 0.2rem;
    }
    .quick-log-panel {
        border: 1px solid rgba(206, 184, 136, 0.24);
        border-radius: 0.95rem;
        padding: 0.9rem 1rem;
        background: linear-gradient(135deg, rgba(120, 47, 64, 0.22), rgba(15, 23, 42, 0.50));
        margin: 0.5rem 0 0.85rem 0;
    }
    .quick-log-title {
        color: #fff8e6;
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 0.15rem;
    }
    .quick-log-copy {
        color: #e5dcc6;
        font-size: 0.86rem;
        line-height: 1.35;
        margin-bottom: 0.35rem;
    }
    .quick-log-step {
        display: inline-block;
        color: #fff8e6;
        background: rgba(206, 184, 136, 0.14);
        border: 1px solid rgba(206, 184, 136, 0.30);
        border-radius: 999px;
        padding: 0.12rem 0.48rem;
        font-size: 0.72rem;
        font-weight: 700;
        margin-right: 0.18rem;
        margin-top: 0.12rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
