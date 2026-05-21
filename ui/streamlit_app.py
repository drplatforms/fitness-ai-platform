# =====================================
# Imports
# =====================================

from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

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

user_id = st.selectbox(
    "Select User",
    options=[1, 2],
    index=0,
)


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
        health_state["system_stress_level"],
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
        f"http://127.0.0.1:8000/reports/status/{st.session_state.report_job_id}"
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


# =====================================
# Display Health Report
# =====================================

if st.session_state.health_report:
    st.write(st.session_state.health_report)

elif st.session_state.report_job_id is None:
    st.info("Click the button to generate a new AI health report.")

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
