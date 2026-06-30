from __future__ import annotations

from dataclasses import dataclass

import database
from models.nutrition_trend_models import (
    BodyweightTrendSummary,
    NutritionCalibrationReadiness,
    NutritionIntakeTrendSummary,
    NutritionTrendWindow,
)
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
        (1, "Snapshot Test User", 190.0),
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


def test_snapshot_builds_for_user_with_data(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    monkeypatch.setattr(
        service,
        "build_training_execution_summary",
        lambda user_id: FakeTrainingSummary(),
    )
    monkeypatch.setattr(
        "services.nutrition_trend_service.build_nutrition_trend_window",
        lambda user_id, end_date, window_days: _fake_nutrition_window(),
    )

    snapshot = build_daily_coach_intelligence_snapshot(
        user_id=1, target_date="2026-06-14"
    )

    assert snapshot.user_id == 1
    assert snapshot.recovery_intelligence.target_date == "2026-06-14"
    assert snapshot.training_execution_summary is not None
    assert snapshot.nutrition_trend_window is not None
    assert snapshot.snapshot_version == "daily_coach_intelligence_snapshot_v1"


def test_foundation_layer_status_is_explicit_and_honest(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    monkeypatch.setattr(
        service,
        "build_training_execution_summary",
        lambda user_id: FakeTrainingSummary(),
    )
    monkeypatch.setattr(
        "services.nutrition_trend_service.build_nutrition_trend_window",
        lambda user_id, end_date, window_days: _fake_nutrition_window(),
    )

    snapshot = build_daily_coach_intelligence_snapshot(
        user_id=1, target_date="2026-06-14"
    )

    assert snapshot.foundation_layer_status["recovery_intelligence"] == "implemented_v1"
    assert (
        snapshot.foundation_layer_status["workout_set_intelligence"]
        == "existing_training_execution_summary_only"
    )
    assert snapshot.data_completeness["food_knowledge_expansion"] == "pending"
    assert snapshot.source_data_gaps


def test_nutrition_trend_limitations_are_controlled(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    monkeypatch.setattr(
        service,
        "build_training_execution_summary",
        lambda user_id: FakeTrainingSummary(),
    )

    def _raise_value_error(user_id, end_date, window_days):
        raise ValueError("local db nutrition tables unavailable")

    monkeypatch.setattr(
        "services.nutrition_trend_service.build_nutrition_trend_window",
        _raise_value_error,
    )

    snapshot = build_daily_coach_intelligence_snapshot(
        user_id=1, target_date="2026-06-14"
    )

    assert snapshot.nutrition_trend_window is None
    assert "nutrition_trend_window_unavailable" in snapshot.reason_codes
    assert any(
        "Nutrition trend window unavailable" in item for item in snapshot.limitations
    )


def test_snapshot_does_not_mutate_database_or_call_provider(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    monkeypatch.setattr(
        service,
        "build_training_execution_summary",
        lambda user_id: FakeTrainingSummary(),
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
    assert "provider" not in " ".join(snapshot.source_services).lower()
    assert snapshot.training_execution_summary is not None


def test_normal_today_behavior_remains_unchanged_by_import() -> None:
    import services.daily_coach_today_card_service as today_service

    assert hasattr(today_service, "build_daily_coach_today_card")
