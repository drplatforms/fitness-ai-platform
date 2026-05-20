# =====================================
# Imports
# =====================================

from datetime import datetime
from time import time

from dotenv import load_dotenv

from crewai import Agent, Task, Crew, LLM

from services.recovery_service import get_recent_recovery_metrics

from services.nutrition_service import get_nutrition_analysis

from services.workout_service import get_recent_workouts

from services.user_service import get_user_profile

from services.report_service import save_health_report

# =====================================
# Environment Initialization
# =====================================

load_dotenv()

# =====================================
# Generate Health Report
# =====================================


def generate_health_report(user_id):
    # -----------------------------
    # Load Data
    # -----------------------------

    user_profile = get_user_profile(user_id)

    recovery_data = get_recent_recovery_metrics()

    nutrition_data = get_nutrition_analysis(user_id)

    workouts = get_recent_workouts(user_id, limit=2)

    # -----------------------------
    # Required User Validation
    # -----------------------------

    if not user_profile:
        return "No user profile found."

    # -----------------------------
    # Recovery Fallback
    # -----------------------------

    if not recovery_data:
        recovery_data = {
            "avg_sleep": "N/A",
            "avg_energy": "N/A",
            "avg_soreness": "N/A",
            "weight_change": "N/A",
        }

    # -----------------------------
    # Nutrition Fallback
    # -----------------------------

    if not nutrition_data:
        nutrition_data = {}

    # -----------------------------
    # Workout Fallback
    # -----------------------------

    if not workouts:
        workouts = []

    # -----------------------------
    # Nutrition Summary
    # -----------------------------

    nutrition_summary = ""

    if not nutrition_data:
        nutrition_summary = "No nutrition data logged."

    else:
        for nutrient_name, nutrient_data in nutrition_data.items():
            nutrition_summary += (
                f"{nutrient_name}: {nutrient_data['amount']} {nutrient_data['unit']}\n"
            )

    # -----------------------------
    # Workout Summary
    # -----------------------------

    workout_summary = ""

    if not workouts:
        workout_summary = "No workout data available."

    else:
        for workout in workouts:
            session = workout["session"]

            workout_summary += (
                f"\nWorkout: "
                f"{session['workout_name']}\n"
                f"Date: "
                f"{session['workout_date']}\n"
                f"Duration: "
                f"{session['duration_minutes']} "
                f"minutes\n"
            )

            for set_data in workout["sets"]:
                workout_summary += (
                    f"- "
                    f"{set_data['name']} | "
                    f"{set_data['reps']} reps x "
                    f"{set_data['weight']} lbs"
                )

                if set_data["rir"] is not None:
                    workout_summary += f" | RIR {set_data['rir']}"

                workout_summary += "\n"

    # -----------------------------
    # LLMs
    # -----------------------------

    fast_llm = LLM(model="ollama/qwen3:8b", base_url="http://localhost:11434")

    smart_llm = LLM(model="ollama/qwen3:8b", base_url="http://localhost:11434")

    # -----------------------------
    # Recovery Agent
    # -----------------------------

    recovery_agent = Agent(
        role="Recovery Coach",
        goal="""
        Analyze recovery trends
        and training readiness.
        """,
        backstory="""
        You specialize in recovery
        management,
        fatigue analysis,
        and training readiness.
        """,
        llm=fast_llm,
        verbose=False,
    )

    recovery_task = Task(
        description=f"""
        Analyze the following
        recovery data.

        Recovery Metrics:

        Average sleep:
        {recovery_data["avg_sleep"]}

        Average energy:
        {recovery_data["avg_energy"]}

        Average soreness:
        {recovery_data["avg_soreness"]}

        Weight change:
        {recovery_data["weight_change"]}

        Provide:
        1. Recovery assessment
        2. Training readiness
        3. Recovery recommendations

        Keep response concise.
        """,
        expected_output="""
        Concise recovery assessment.
        """,
        agent=recovery_agent,
    )

    # -----------------------------
    # Nutrition Agent
    # -----------------------------

    nutrition_agent = Agent(
        role="Nutrition Coach",
        goal="""
        Analyze nutrition intake
        and recovery support.
        """,
        backstory="""
        You specialize in
        performance nutrition,
        body composition,
        and recovery nutrition.
        """,
        llm=smart_llm,
        verbose=False,
    )

    nutrition_task = Task(
        description=f"""
        Analyze the following
        nutrition data.

        Nutrition Data:

        {nutrition_summary}

        Provide:
        1. Nutrition assessment
        2. Recovery implications
        3. Nutrition recommendations

        Keep response concise.
        """,
        expected_output="""
        Concise nutrition assessment.
        """,
        agent=nutrition_agent,
    )

    # -----------------------------
    # Workout Agent
    # -----------------------------

    workout_agent = Agent(
        role="Strength Coach",
        goal="""
        Analyze workout quality
        and training balance.
        """,
        backstory="""
        You specialize in
        resistance training,
        recovery management,
        and performance progression.
        """,
        llm=fast_llm,
        verbose=False,
    )

    workout_task = Task(
        description=f"""
        Analyze the following
        workout history.

        Workout Data:

        {workout_summary}

        Provide:
        1. Workout quality assessment
        2. Recovery implications
        3. Training recommendations

        Keep response concise.
        """,
        expected_output="""
        Concise workout assessment.
        """,
        agent=workout_agent,
    )

    # -----------------------------
    # Coordinator Agent
    # -----------------------------

    coordinator_agent = Agent(
        role="Health Performance Coordinator",
        goal="""
        Combine recovery,
        nutrition,
        and workout insights
        into unified coaching
        recommendations.
        """,
        backstory="""
        You synthesize recovery,
        nutrition,
        and workout analyses
        into practical,
        actionable health guidance.
        """,
        llm=smart_llm,
        verbose=False,
    )

    coordinator_task = Task(
        description="""
        Combine the recovery,
        nutrition,
        and workout analyses
        into a unified health
        recommendation.

        Identify:
        1. Biggest issue
        2. Likely cause
        3. Highest priority action
        4. Best recommendation

        Keep response concise
        and actionable.
        """,
        expected_output="""
        Unified health report.
        """,
        agent=coordinator_agent,
        context=[recovery_task, nutrition_task, workout_task],
    )

    # -----------------------------
    # Build Crew
    # -----------------------------

    crew = Crew(
        agents=[recovery_agent, nutrition_agent, workout_agent, coordinator_agent],
        tasks=[recovery_task, nutrition_task, workout_task, coordinator_task],
        verbose=False,
    )

    # -----------------------------
    # Run Workflow
    # -----------------------------

    start_timestamp = datetime.now()

    print("\nStarting health coordinator...")

    print(f"Start Time: {start_timestamp.strftime('%Y-%m-%d %I:%M:%S %p')}")

    start_time = time()

    try:
        result = crew.kickoff()

        end_time = time()

        end_timestamp = datetime.now()

        runtime_seconds = round(end_time - start_time, 2)

        runtime_minutes = round(runtime_seconds / 60, 2)

        print("\nWorkflow complete.")

        print(f"End Time: {end_timestamp.strftime('%Y-%m-%d %I:%M:%S %p')}")

        print(f"Runtime: {runtime_seconds} seconds ({runtime_minutes} minutes)")

        print("\n=== HEALTH REPORT ===\n")

        save_health_report(
            user_id=user_id, report_text=result.raw, model_summary="All 8B Benchmark"
        )

        print(result.raw)

        return result.raw

    except Exception as e:
        print("\nCrewAI Error:")
        print(e)

        return str(e)


# =====================================
# Run Script
# =====================================

if __name__ == "__main__":
    user_id = 1

    report = generate_health_report(user_id)

    print("\n=== FINAL REPORT ===\n")

    print(report)
