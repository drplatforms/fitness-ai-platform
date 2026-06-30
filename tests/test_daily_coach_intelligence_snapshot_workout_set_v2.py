from __future__ import annotations

from dataclasses import dataclass

import database
from models.nutrition_trend_models import (
    BodyweightTrendSummary,
    NutritionCalibrationReadiness,
    NutritionIntakeTrendSummary,
    NutritionTrendWindow,
)
from models.workout_set_intelligence_models import WorkoutSetIntelligenceSummary
from services import daily_coach_intelligence_snapshot_service as service
from services.daily_coach_intelligence_snapshot_service import (
    build_daily_coach_intelligence_snapshot,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (id, name, starting_weight)
        VALUES (?, ?, ?)
        """,
        (1, "Snapshot V2 Test User", 190.0),
    )
    cursor.execute(
        """
        INSERT INTO daily_checkins (
            user_id, checkin_date, body_weight, sleep_hours, energy_level, soreness_level
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (1, "2026-06-14", 190.0, 7.0, 6, 3),
    )
    conn.commit()
    conn.close()


@dataclass(frozen=True)
class FakeTrainingSummary:
    user_id: int = 1
    completed_execution_count: int = 2
    confidence: str = "Moderate"

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "completed_execution_count": self.completed_execution_count,
            "confidence": self.confidence,
        }


def _fake_workout_set_summary(
    *,
    completed_execution_count: int = 2,
    confidence: str = "Moderate",
) -> WorkoutSetIntelligenceSummary:
    return WorkoutSetIntelligenceSummary(
        user_id=1,
        target_date="2026-06-14",
        generated_at="2026-06-14T12:00:00+00:00",
        source_tables=["workout_plan_instances", "workout_execution_set_actuals"],
        model_version="workout_set_intelligence_v1",
        completed_execution_count=completed_execution_count,
        recent_plan_instance_ids=[10, 9] if completed_execution_count else [],
        session_summaries=[],
        exercise_indicators=[],
        overall_completion_indicator=(
            "mostly_completed"
            if completed_execution_count
            else "no_planned_execution_data"
        ),
        overall_effort_indicator=(
            "as_planned" if completed_execution_count else "unknown"
        ),
        overall_rep_range_indicator=(
            "mostly_inside_range" if completed_execution_count else "unknown"
        ),
        overall_logging_quality="complete" if completed_execution_count else "unknown",
        confidence=confidence,
        source_facts=["Completion indicator: mostly_completed."],
        coach_safe_summary="Recent logged sets mostly matched the written plan.",
        reason_codes=([] if confidence == "Moderate" else ["limited_workout_set_data"]),
        limitations=(
            [] if confidence == "Moderate" else ["Workout set data is limited."]
        ),
    )


def _fake_nutrition_window() -> NutritionTrendWindow:
    return NutritionTrendWindow(
        user_id=1,
        start_date="2026-06-01",
        end_date="2026-06-14",
        window_days=14,
        logged_day_count=3,
        complete_logging_day_count=1,
        partial_logging_day_count=2,
        no_log_day_count=11,
        intake_trend_summary=NutritionIntakeTrendSummary(
            average_calories=1800,
            logging_consistency_status="inconsistent",
            confidence="Low",
            reason_codes=["partial_logging"],
        ),
        bodyweight_trend_summary=BodyweightTrendSummary(
            trend_direction="unavailable",
            confidence="Limited",
            reason_codes=["bodyweight_unavailable"],
        ),
        calibration_readiness=NutritionCalibrationReadiness(
            calibration_allowed=False,
            readiness_level="not_ready",
            minimum_window_met=True,
            preferred_window_met=False,
            logging_quality_met=False,
            bodyweight_trend_available=False,
            goal_context_available=False,
            training_context_available=True,
            reason_codes=["calibration_not_ready"],
        ),
        confidence="Low",
        reason_codes=["partial_logging"],
    )


def test_snapshot_v2_includes_workout_set_intelligence(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    monkeypatch.setattr(
        service,
        "build_training_execution_summary",
        lambda user_id: FakeTrainingSummary(),
    )
    monkeypatch.setattr(
        service,
        "build_workout_set_intelligence",
        lambda user_id, target_date: _fake_workout_set_summary(),
    )
    monkeypatch.setattr(
        "services.nutrition_trend_service.build_nutrition_trend_window",
        lambda user_id, end_date, window_days: _fake_nutrition_window(),
    )

    snapshot = build_daily_coach_intelligence_snapshot(
        user_id=1, target_date="2026-06-14"
    )

    assert snapshot.snapshot_version == "daily_coach_intelligence_snapshot_v2"
    assert snapshot.workout_set_intelligence is not None
    assert "workout_set_intelligence_service" in snapshot.source_services
    assert (
        snapshot.foundation_layer_status["workout_set_intelligence"] == "implemented_v1"
    )
    assert snapshot.data_completeness["workout_set_intelligence"] == "usable"
    assert not any(
        gap.startswith("workout_set_intelligence: not_implemented")
        for gap in snapshot.source_data_gaps
    )


def test_snapshot_v2_reports_workout_set_missing_when_no_planned_data(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    monkeypatch.setattr(
        service,
        "build_training_execution_summary",
        lambda user_id: FakeTrainingSummary(completed_execution_count=0),
    )
    monkeypatch.setattr(
        service,
        "build_workout_set_intelligence",
        lambda user_id, target_date: _fake_workout_set_summary(
            completed_execution_count=0,
            confidence="Limited",
        ),
    )
    monkeypatch.setattr(
        "services.nutrition_trend_service.build_nutrition_trend_window",
        lambda user_id, end_date, window_days: _fake_nutrition_window(),
    )

    snapshot = build_daily_coach_intelligence_snapshot(
        user_id=1, target_date="2026-06-14"
    )

    assert snapshot.data_completeness["workout_set_intelligence"] == "missing"
    assert "workout_set_intelligence: missing" in snapshot.source_data_gaps


def test_snapshot_v2_preserves_existing_layers_and_boundaries(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    monkeypatch.setattr(
        service,
        "build_training_execution_summary",
        lambda user_id: FakeTrainingSummary(),
    )
    monkeypatch.setattr(
        service,
        "build_workout_set_intelligence",
        lambda user_id, target_date: _fake_workout_set_summary(),
    )
    monkeypatch.setattr(
        "services.nutrition_trend_service.build_nutrition_trend_window",
        lambda user_id, end_date, window_days: _fake_nutrition_window(),
    )
    conn = database.get_connection()
    before = conn.execute("SELECT COUNT(*) AS count FROM daily_checkins").fetchone()[
        "count"
    ]
    conn.close()

    snapshot = build_daily_coach_intelligence_snapshot(
        user_id=1, target_date="2026-06-14"
    )

    conn = database.get_connection()
    after = conn.execute("SELECT COUNT(*) AS count FROM daily_checkins").fetchone()[
        "count"
    ]
    conn.close()
    assert before == after
    assert snapshot.recovery_intelligence is not None
    assert snapshot.training_execution_summary is not None
    assert snapshot.nutrition_trend_window is not None
    assert "provider" not in " ".join(snapshot.source_services).lower()


def test_normal_today_behavior_remains_unchanged_by_snapshot_v2_import() -> None:
    import services.daily_coach_today_card_service as today_service

    assert hasattr(today_service, "build_daily_coach_today_card")
