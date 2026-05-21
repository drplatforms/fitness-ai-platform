from dataclasses import dataclass


@dataclass
class UserRecoveryState:
    avg_sleep: float | str
    avg_energy: float | str
    avg_soreness: float | str
    weight_change: float | str
    recovery_score: int
    fatigue_risk: str
    readiness_level: str
    sleep_trend: str
    weight_trend: str


@dataclass
class UserNutritionState:
    nutrition_summary: str
    has_nutrition_data: bool


@dataclass
class UserTrainingState:
    workout_summary: str
    has_workout_data: bool
    workout_count: int
    adherence_level: str
    training_trend: str


@dataclass
class UserHealthState:
    user_id: int
    user_name: str
    primary_goal: str
    recovery_state: UserRecoveryState
    nutrition_state: UserNutritionState
    training_state: UserTrainingState
    system_stress_level: str
