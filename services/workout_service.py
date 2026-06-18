# =====================================
# Imports
# =====================================

from datetime import datetime

from database import get_connection

# =====================================
# Get All Exercises
# =====================================


def get_exercises():
    from services.exercise_catalog_service import seed_exercise_catalog

    seed_exercise_catalog()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM exercises
    ORDER BY name
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


# =====================================
# Search Exercises
# =====================================


def search_exercises(search_term, limit=10):
    from services.exercise_catalog_service import seed_exercise_catalog

    seed_exercise_catalog()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT *
    FROM exercises
    WHERE name LIKE ?
    ORDER BY name
    LIMIT ?
    """,
        (f"%{search_term}%", limit),
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


# =====================================
# Create Workout Session
# =====================================


def create_workout_session(user_id, workout_name, duration_minutes=None, notes=None):
    conn = get_connection()
    cursor = conn.cursor()

    workout_date = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        """
    INSERT INTO workout_sessions (

        user_id,
        workout_date,
        workout_name,
        duration_minutes,
        notes

    )
    VALUES (?, ?, ?, ?, ?)
    """,
        (user_id, workout_date, workout_name, duration_minutes, notes),
    )

    session_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return session_id


# =====================================
# Add Workout Set
# =====================================


def add_workout_set(
    workout_session_id, exercise_id, set_number, reps, weight, rir=None
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    INSERT INTO workout_sets (

        workout_session_id,
        exercise_id,
        set_number,
        reps,
        weight,
        rir

    )
    VALUES (?, ?, ?, ?, ?, ?)
    """,
        (workout_session_id, exercise_id, set_number, reps, weight, rir),
    )

    conn.commit()
    conn.close()


# =====================================
# Get Recent Workouts
# =====================================


def get_recent_workouts(user_id, limit=5):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT *
    FROM workout_sessions
    WHERE user_id = ?
    ORDER BY workout_date DESC, id DESC
    LIMIT ?
    """,
        (user_id, limit),
    )

    sessions = cursor.fetchall()

    workouts = []

    for session in sessions:
        cursor.execute(
            """
        SELECT

            workout_sets.id,
            workout_sets.workout_session_id,
            workout_sets.exercise_id,
            workout_sets.set_number,
            workout_sets.reps,
            workout_sets.weight,
            workout_sets.rir,

            exercises.name

        FROM workout_sets

        JOIN exercises
            ON workout_sets.exercise_id = exercises.id

        WHERE workout_sets.workout_session_id = ?

        ORDER BY workout_sets.set_number
        """,
            (session["id"],),
        )

        sets = cursor.fetchall()

        workouts.append(
            {"session": dict(session), "sets": [dict(set_row) for set_row in sets]}
        )

    conn.close()

    return workouts


# =====================================
# Get Exercises
# =====================================


def get_all_exercises():
    from services.exercise_catalog_service import seed_exercise_catalog

    seed_exercise_catalog()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            muscle_group,
            equipment
        FROM exercises
        ORDER BY name
        """)

    exercises = cursor.fetchall()

    conn.close()

    return [dict(row) for row in exercises]
