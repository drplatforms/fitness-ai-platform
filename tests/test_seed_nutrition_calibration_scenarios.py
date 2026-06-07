from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from models.nutrition_trend_models import (
    CALIBRATION_READINESS_EARLY_SIGNAL,
    CALIBRATION_READINESS_NOT_READY,
    CALIBRATION_READINESS_STRONG,
    CALIBRATION_READINESS_USABLE,
)
from scripts.seed_nutrition_calibration_scenarios import (
    SEED_END_DATE,
    seed_nutrition_calibration_scenarios,
)
from services.nutrition_target_calibration_service import (
    RECOMMENDED_ACTION_INSUFFICIENT_DATA,
    RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE,
    build_nutrition_target_calibration_result,
)
from services.nutrition_target_formula_service import (
    build_nutrition_target_formula_inputs,
    calculate_nutrition_target_formula,
)
from services.nutrition_target_formula_validation_service import (
    approve_validated_macro_targets,
)
from services.nutrition_trend_service import build_nutrition_trend_window
from services.user_service import get_user_profile
from services.user_state_service import build_user_health_state


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_nutrition_calibration_scenarios()


def _count_seeded_rows() -> tuple[int, int, int]:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM food_entries
        WHERE user_id IN (102, 103, 104, 105)
          AND entry_date BETWEEN '2026-05-10' AND '2026-06-06'
          AND food_id IN (
              SELECT id
              FROM foods
              WHERE name LIKE 'Canonical:%'
          )
        """)
    food_entry_count = int(cursor.fetchone()["count"])
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM daily_checkins
        WHERE user_id IN (102, 103, 104, 105)
          AND notes LIKE 'seed_nutrition_calibration_scenarios_v1:%'
        """)
    checkin_count = int(cursor.fetchone()["count"])
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM workout_sessions
        WHERE user_id IN (102, 103, 104, 105)
          AND notes LIKE 'seed_nutrition_calibration_scenarios_v1:%'
        """)
    workout_count = int(cursor.fetchone()["count"])
    conn.close()
    return food_entry_count, checkin_count, workout_count


def _approved_target_snapshot(user_id: int) -> dict:
    profile = get_user_profile(user_id)
    health_state = build_user_health_state(user_id)
    formula_inputs = build_nutrition_target_formula_inputs(
        health_state,
        calculation_date=SEED_END_DATE.isoformat(),
        sex=profile["gender"] if profile else None,
    )
    formula_result = calculate_nutrition_target_formula(formula_inputs)
    return approve_validated_macro_targets(formula_result).to_dict()


def test_seed_script_creates_calibration_scenarios_idempotently(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    first_counts = _count_seeded_rows()

    seed_nutrition_calibration_scenarios()
    second_counts = _count_seeded_rows()

    assert first_counts == second_counts
    assert first_counts[0] > 0
    assert first_counts[1] > 0
    assert first_counts[2] > 0


def test_seeded_28_day_strong_scenario_is_available(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    window = build_nutrition_trend_window(
        102,
        end_date=SEED_END_DATE.isoformat(),
        window_days=28,
    )
    calibration = build_nutrition_target_calibration_result(
        102,
        calibration_date=SEED_END_DATE.isoformat(),
        window_days=28,
    )

    assert window.logged_day_count == 25
    assert window.complete_logging_day_count == 23
    assert window.no_log_day_count == 3
    assert window.calibration_readiness.readiness_level in {
        CALIBRATION_READINESS_USABLE,
        CALIBRATION_READINESS_STRONG,
    }
    assert calibration.readiness_level in {
        CALIBRATION_READINESS_USABLE,
        CALIBRATION_READINESS_STRONG,
    }
    assert calibration.calibrated_targets is None


def test_seeded_14_day_early_signal_scenario_is_available(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    window = build_nutrition_trend_window(
        103,
        end_date=SEED_END_DATE.isoformat(),
        window_days=14,
    )
    calibration = build_nutrition_target_calibration_result(
        103,
        calibration_date=SEED_END_DATE.isoformat(),
        window_days=14,
    )

    assert (
        window.calibration_readiness.readiness_level
        == CALIBRATION_READINESS_EARLY_SIGNAL
    )
    assert window.calibration_readiness.calibration_allowed is False
    assert calibration.readiness_level == CALIBRATION_READINESS_EARLY_SIGNAL
    assert calibration.recommended_action == RECOMMENDED_ACTION_MAINTAIN_BROAD_RANGE
    assert calibration.calibrated_targets is None


def test_seeded_not_ready_scenario_is_available(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    calibration = build_nutrition_target_calibration_result(
        104,
        calibration_date=SEED_END_DATE.isoformat(),
        window_days=28,
    )

    assert calibration.readiness_level == CALIBRATION_READINESS_NOT_READY
    assert calibration.recommended_action == RECOMMENDED_ACTION_INSUFFICIENT_DATA
    assert "bodyweight_trend_unavailable" in calibration.reason_codes
    assert calibration.calibrated_targets is None


def test_seeded_data_quality_limited_scenario_is_available(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    window = build_nutrition_trend_window(
        105,
        end_date=SEED_END_DATE.isoformat(),
        window_days=28,
    )
    calibration = build_nutrition_target_calibration_result(
        105,
        calibration_date=SEED_END_DATE.isoformat(),
        window_days=28,
    )

    assert window.logged_day_count == 6
    assert window.complete_logging_day_count == 2
    assert window.no_log_day_count == 22
    assert calibration.readiness_level == CALIBRATION_READINESS_NOT_READY
    assert "logging_quality_insufficient" in calibration.reason_codes
    assert calibration.limitations


def test_trend_and_calibration_apis_reflect_seeded_scenarios(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    trend_response = client.get(
        "/nutrition/102/trend-window?end_date=2026-06-06&window_days=28"
    )
    calibration_response = client.get(
        "/nutrition/102/target-calibration?end_date=2026-06-06&window_days=28"
    )

    assert trend_response.status_code == 200
    trend_payload = trend_response.json()
    assert trend_payload["user_id"] == 102
    assert trend_payload["window_days"] == 28
    assert trend_payload["logged_day_count"] == 25
    assert trend_payload["calibration_readiness"]["readiness_level"] in {
        CALIBRATION_READINESS_USABLE,
        CALIBRATION_READINESS_STRONG,
    }

    assert calibration_response.status_code == 200
    calibration_payload = calibration_response.json()
    assert calibration_payload["user_id"] == 102
    assert calibration_payload["calibrated_targets"] is None
    assert calibration_payload["readiness_level"] in {
        CALIBRATION_READINESS_USABLE,
        CALIBRATION_READINESS_STRONG,
    }
    assert "target_mutation_not_performed" in calibration_payload["reason_codes"]


def test_seed_does_not_mutate_formula_targets(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    before = _approved_target_snapshot(102)

    seed_nutrition_calibration_scenarios()
    after = _approved_target_snapshot(102)

    ignored_dynamic_keys = {"formula_metadata"}
    comparable_before = {
        key: value for key, value in before.items() if key not in ignored_dynamic_keys
    }
    comparable_after = {
        key: value for key, value in after.items() if key not in ignored_dynamic_keys
    }
    assert comparable_before == comparable_after


def test_seed_does_not_break_existing_nutrition_logs(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM food_entries
        WHERE user_id IN (102, 103, 104, 105)
        """)
    food_entry_count = int(cursor.fetchone()["count"])
    conn.close()

    assert food_entry_count > 0
