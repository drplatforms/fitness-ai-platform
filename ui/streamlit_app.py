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
        timeout=30,
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
