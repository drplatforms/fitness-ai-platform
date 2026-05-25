import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fitness_ai.db"


def get_connection():
    print(f"Using database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    # -----------------------------
    # Users
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE,

        gender TEXT,
        age INTEGER,
        height_cm REAL,

        starting_weight REAL,
        goal_weight REAL,

        primary_goal TEXT,
        activity_level TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # -----------------------------
    # Daily Check-ins
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        checkin_date TEXT NOT NULL,

        body_weight REAL,
        sleep_hours REAL,
        energy_level INTEGER,
        soreness_level INTEGER,

        mood TEXT,
        notes TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # -----------------------------
    # Recovery Reports
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recovery_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        report_date TEXT NOT NULL,

        entries_analyzed INTEGER,
        avg_sleep REAL,
        avg_energy REAL,
        avg_soreness REAL,
        weight_change REAL,

        recommendation TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # -----------------------------
    # Foods
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # -----------------------------
    # Nutrients
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nutrients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE,
        unit TEXT NOT NULL,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # -----------------------------
    # Food Nutrients
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_nutrients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        food_id INTEGER NOT NULL,
        nutrient_id INTEGER NOT NULL,

        amount_per_100g REAL NOT NULL,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (food_id) REFERENCES foods(id),
        FOREIGN KEY (nutrient_id) REFERENCES nutrients(id)
    )
    """)

    # -----------------------------
    # Food Entries
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,
        food_id INTEGER NOT NULL,

        grams REAL NOT NULL,

        entry_date TEXT NOT NULL,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (food_id) REFERENCES foods(id)
    )
    """)

    # -----------------------------
    # Seed Users
    # -----------------------------

    cursor.execute("""
    INSERT OR IGNORE INTO users (
        name,
        gender,
        age,
        height_cm,
        starting_weight,
        goal_weight,
        primary_goal,
        activity_level
    )
    VALUES

    (
        'Dustin',
        'Male',
        37,
        176.5,
        187.6,
        165,
        'fat_loss',
        'moderate'
    ),

    (
        'Danielle',
        'Female',
        37,
        162.6,
        170,
        130,
        'fat_loss',
        'moderate'
    )
    """)

    # -----------------------------
    # Seed Nutrients
    # -----------------------------

    cursor.execute("""
    INSERT OR IGNORE INTO nutrients (
        name,
        unit
    )
    VALUES
        ('Calories', 'kcal'),
        ('Protein', 'g'),
        ('Carbohydrates', 'g'),
        ('Fat', 'g'),
        ('Fiber', 'g'),
        ('Sugar', 'g'),
        ('Sodium', 'mg'),
        ('Potassium', 'mg'),
        ('Magnesium', 'mg'),
        ('Calcium', 'mg'),
        ('Iron', 'mg'),
        ('Vitamin C', 'mg'),
        ('Vitamin D', 'mcg'),
        ('Vitamin B12', 'mcg'),
        ('Zinc', 'mg')
    """)

    # -----------------------------
    # Exercises
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE,

        muscle_group TEXT,
        movement_type TEXT,
        equipment TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # -----------------------------
    # Workout Sessions
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        workout_date TEXT NOT NULL,

        workout_name TEXT,

        duration_minutes INTEGER,

        notes TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # -----------------------------
    # Workout Sets
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        workout_session_id INTEGER NOT NULL,

        exercise_id INTEGER NOT NULL,

        set_number INTEGER,

        reps INTEGER,
        weight REAL,

        rir INTEGER,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (workout_session_id)
            REFERENCES workout_sessions(id),

        FOREIGN KEY (exercise_id)
            REFERENCES exercises(id)
    )
    """)

    # -----------------------------
    # User Equipment Profiles
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_equipment_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL UNIQUE,

        training_environment TEXT NOT NULL,
        available_equipment_json TEXT NOT NULL,
        unavailable_equipment_json TEXT NOT NULL,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # -----------------------------
    # Workout Plan Instances
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_plan_instances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        status TEXT NOT NULL,
        scenario TEXT NOT NULL,
        confidence TEXT NOT NULL,
        title TEXT NOT NULL,
        approved_workout_plan_json TEXT NOT NULL,

        selected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # -----------------------------
    # Planned Workout Exercises
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planned_workout_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        workout_plan_instance_id INTEGER NOT NULL,

        exercise_order INTEGER NOT NULL,
        name TEXT NOT NULL,
        sets INTEGER NOT NULL,
        reps_min INTEGER NOT NULL,
        reps_max INTEGER NOT NULL,
        rir_min INTEGER NOT NULL,
        rir_max INTEGER NOT NULL,
        notes TEXT NOT NULL,
        equipment_required_json TEXT NOT NULL,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (workout_plan_instance_id)
            REFERENCES workout_plan_instances(id)
    )
    """)

    # -----------------------------
    # Workout Execution Sessions
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_execution_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        workout_plan_instance_id INTEGER NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,

        status TEXT NOT NULL,
        workout_session_id INTEGER,

        started_at TEXT,
        completed_at TEXT,
        abandoned_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (workout_plan_instance_id)
            REFERENCES workout_plan_instances(id),

        FOREIGN KEY (user_id) REFERENCES users(id),

        FOREIGN KEY (workout_session_id)
            REFERENCES workout_sessions(id)
    )
    """)

    # -----------------------------
    # Workout Execution Set Actuals
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_execution_set_actuals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        workout_execution_session_id INTEGER NOT NULL,
        planned_workout_exercise_id INTEGER,
        workout_session_id INTEGER,
        workout_set_id INTEGER,

        exercise_name TEXT NOT NULL,
        set_number INTEGER NOT NULL,

        planned_reps_min INTEGER,
        planned_reps_max INTEGER,
        planned_rir_min INTEGER,
        planned_rir_max INTEGER,

        actual_reps INTEGER,
        actual_weight REAL,
        actual_rir INTEGER,

        completed INTEGER NOT NULL DEFAULT 0,
        skipped INTEGER NOT NULL DEFAULT 0,
        substitution_for_planned_exercise_id INTEGER,
        notes TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (workout_execution_session_id)
            REFERENCES workout_execution_sessions(id),

        FOREIGN KEY (planned_workout_exercise_id)
            REFERENCES planned_workout_exercises(id),

        FOREIGN KEY (workout_session_id)
            REFERENCES workout_sessions(id),

        FOREIGN KEY (workout_set_id)
            REFERENCES workout_sets(id),

        FOREIGN KEY (substitution_for_planned_exercise_id)
            REFERENCES planned_workout_exercises(id)
    )
    """)

    # -----------------------------
    # Seed Exercises
    # -----------------------------

    cursor.execute("""
    INSERT OR IGNORE INTO exercises (
        name,
        muscle_group,
        movement_type,
        equipment
    )
    VALUES

    -- Chest
    ('Barbell Bench Press', 'Chest', 'Compound', 'Barbell'),
    ('Incline Bench Press', 'Chest', 'Compound', 'Barbell'),
    ('Dumbbell Bench Press', 'Chest', 'Compound', 'Dumbbell'),
    ('Incline Dumbbell Press', 'Chest', 'Compound', 'Dumbbell'),
    ('Chest Fly', 'Chest', 'Isolation', 'Machine'),
    ('Cable Fly', 'Chest', 'Isolation', 'Cable'),
    ('Push-Up', 'Chest', 'Compound', 'Bodyweight'),
    ('Dips', 'Chest', 'Compound', 'Bodyweight'),

    -- Back
    ('Deadlift', 'Posterior Chain', 'Compound', 'Barbell'),
    ('Barbell Row', 'Back', 'Compound', 'Barbell'),
    ('Dumbbell Row', 'Back', 'Compound', 'Dumbbell'),
    ('Pull-Up', 'Back', 'Compound', 'Bodyweight'),
    ('Chin-Up', 'Back', 'Compound', 'Bodyweight'),
    ('Lat Pulldown', 'Back', 'Compound', 'Machine'),
    ('Seated Cable Row', 'Back', 'Compound', 'Cable'),
    ('T-Bar Row', 'Back', 'Compound', 'Machine'),
    ('Face Pull', 'Back', 'Isolation', 'Cable'),
    ('Shrug', 'Traps', 'Isolation', 'Dumbbell'),

    -- Shoulders
    ('Overhead Press', 'Shoulders', 'Compound', 'Barbell'),
    ('Seated Dumbbell Press', 'Shoulders', 'Compound', 'Dumbbell'),
    ('Arnold Press', 'Shoulders', 'Compound', 'Dumbbell'),
    ('Lateral Raise', 'Shoulders', 'Isolation', 'Dumbbell'),
    ('Front Raise', 'Shoulders', 'Isolation', 'Dumbbell'),
    ('Rear Delt Fly', 'Shoulders', 'Isolation', 'Machine'),
    ('Upright Row', 'Shoulders', 'Compound', 'Barbell'),

    -- Legs
    ('Barbell Squat', 'Legs', 'Compound', 'Barbell'),
    ('Front Squat', 'Legs', 'Compound', 'Barbell'),
    ('Leg Press', 'Legs', 'Compound', 'Machine'),
    ('Walking Lunge', 'Legs', 'Compound', 'Dumbbell'),
    ('Romanian Deadlift', 'Hamstrings', 'Compound', 'Barbell'),
    ('Bulgarian Split Squat', 'Legs', 'Compound', 'Dumbbell'),
    ('Hack Squat', 'Legs', 'Compound', 'Machine'),
    ('Leg Extension', 'Quadriceps', 'Isolation', 'Machine'),
    ('Leg Curl', 'Hamstrings', 'Isolation', 'Machine'),
    ('Calf Raise', 'Calves', 'Isolation', 'Machine'),
    ('Hip Thrust', 'Glutes', 'Compound', 'Barbell'),

    -- Arms
    ('Barbell Curl', 'Biceps', 'Isolation', 'Barbell'),
    ('Dumbbell Curl', 'Biceps', 'Isolation', 'Dumbbell'),
    ('Hammer Curl', 'Biceps', 'Isolation', 'Dumbbell'),
    ('Preacher Curl', 'Biceps', 'Isolation', 'Machine'),
    ('Cable Curl', 'Biceps', 'Isolation', 'Cable'),
    ('Tricep Pushdown', 'Triceps', 'Isolation', 'Cable'),
    ('Overhead Tricep Extension', 'Triceps', 'Isolation', 'Dumbbell'),
    ('Skullcrusher', 'Triceps', 'Isolation', 'Barbell'),
    ('Close-Grip Bench Press', 'Triceps', 'Compound', 'Barbell'),
    ('Bench Dip', 'Triceps', 'Compound', 'Bodyweight'),

    -- Core
    ('Crunch', 'Core', 'Isolation', 'Bodyweight'),
    ('Sit-Up', 'Core', 'Isolation', 'Bodyweight'),
    ('Plank', 'Core', 'Isometric', 'Bodyweight'),
    ('Hanging Leg Raise', 'Core', 'Compound', 'Bodyweight'),
    ('Cable Crunch', 'Core', 'Isolation', 'Cable'),
    ('Russian Twist', 'Core', 'Isolation', 'Bodyweight'),
    ('Ab Wheel Rollout', 'Core', 'Compound', 'Bodyweight'),

    -- Conditioning
    ('Rowing Machine', 'Conditioning', 'Cardio', 'Machine'),
    ('Treadmill Run', 'Conditioning', 'Cardio', 'Machine'),
    ('Stationary Bike', 'Conditioning', 'Cardio', 'Machine'),
    ('Jump Rope', 'Conditioning', 'Cardio', 'Bodyweight'),
    ('Farmer Carry', 'Conditioning', 'Compound', 'Dumbbell'),
    ('Sled Push', 'Conditioning', 'Compound', 'Machine'),

    -- Olympic / Athletic
    ('Power Clean', 'Full Body', 'Explosive', 'Barbell'),
    ('Hang Clean', 'Full Body', 'Explosive', 'Barbell'),
    ('Push Press', 'Full Body', 'Explosive', 'Barbell'),
    ('Snatch', 'Full Body', 'Explosive', 'Barbell'),
    ('Clean and Jerk', 'Full Body', 'Explosive', 'Barbell'),

    -- Machines
    ('Chest Press Machine', 'Chest', 'Compound', 'Machine'),
    ('Smith Machine Squat', 'Legs', 'Compound', 'Machine'),
    ('Machine Shoulder Press', 'Shoulders', 'Compound', 'Machine'),
    ('Machine Row', 'Back', 'Compound', 'Machine'),

    -- Glutes
    ('Cable Kickback', 'Glutes', 'Isolation', 'Cable'),
    ('Glute Bridge', 'Glutes', 'Compound', 'Bodyweight'),
    ('Step-Up', 'Legs', 'Compound', 'Dumbbell'),

    -- Additional Variations
    ('Incline Push-Up', 'Chest', 'Compound', 'Bodyweight'),
    ('Decline Push-Up', 'Chest', 'Compound', 'Bodyweight'),
    ('Single Arm Row', 'Back', 'Compound', 'Dumbbell'),
    ('Goblet Squat', 'Legs', 'Compound', 'Dumbbell'),
    ('Kettlebell Swing', 'Posterior Chain', 'Explosive', 'Kettlebell'),
    ('Reverse Lunge', 'Legs', 'Compound', 'Dumbbell'),
    ('Sumo Deadlift', 'Posterior Chain', 'Compound', 'Barbell'),
    ('Trap Bar Deadlift', 'Posterior Chain', 'Compound', 'Barbell'),
    ('Cable Lateral Raise', 'Shoulders', 'Isolation', 'Cable'),
    ('EZ Bar Curl', 'Biceps', 'Isolation', 'Barbell'),
    ('Rope Pushdown', 'Triceps', 'Isolation', 'Cable'),
    ('Machine Fly', 'Chest', 'Isolation', 'Machine'),
    ('Reverse Pec Deck', 'Rear Delts', 'Isolation', 'Machine'),
    ('Good Morning', 'Posterior Chain', 'Compound', 'Barbell'),
    ('Walking Farmer Carry', 'Conditioning', 'Compound', 'Dumbbell')
    """)

    # -----------------------------
    # Health Reports
    # -----------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS health_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        report_text TEXT NOT NULL,
        model_summary TEXT,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized.")
