from __future__ import annotations

import json

import database
from tools import dev_daily_coach_intelligence_snapshot as tool


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    conn = database.get_connection()
    cursor = conn.cursor()
    for user_id in [101, 102]:
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (id, name, starting_weight)
            VALUES (?, ?, ?)
            """,
            (user_id, f"Tool Test User {user_id}", 190.0),
        )
        cursor.execute(
            """
            INSERT INTO daily_checkins (
                user_id, checkin_date, body_weight, sleep_hours, energy_level, soreness_level
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, "2026-06-14", 190.0, 7.0, 6, 3),
        )
    conn.commit()
    conn.close()


def test_single_user_mode_writes_terminal_friendly_artifacts(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    output_dir = tmp_path / "single"

    exit_code = tool.main(
        [
            "--user-id",
            "101",
            "--target-date",
            "2026-06-14",
            "--output-dir",
            str(output_dir),
            "--write-json",
            "--write-markdown",
            "--write-pasteback-report",
        ]
    )

    assert exit_code == 0
    expected = {
        "daily_coach_intelligence_snapshot.json",
        "daily_coach_intelligence_snapshot.md",
        "backend_intelligence_gap_report.md",
        "data_completeness_summary.md",
        "pasteback_report.md",
        "workout_set_intelligence_summary.md",
    }
    assert expected.issubset({path.name for path in output_dir.iterdir()})
    pasteback = (output_dir / "pasteback_report.md").read_text(encoding="utf-8")
    assert "Provider called: false" in pasteback
    assert "Database mutated: false" in pasteback
    assert "Workout completion indicator:" in pasteback


def test_users_matrix_mode_writes_combined_and_per_user_json(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    output_dir = tmp_path / "matrix"

    exit_code = tool.main(
        [
            "--users",
            "101,102",
            "--target-date",
            "2026-06-14",
            "--output-dir",
            str(output_dir),
            "--write-json",
            "--write-markdown",
            "--write-pasteback-report",
        ]
    )

    assert exit_code == 0
    payload = json.loads(
        (output_dir / "daily_coach_intelligence_snapshot.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(payload["snapshots"]) == 2
    assert (output_dir / "user_101_daily_coach_intelligence_snapshot.json").exists()
    assert (output_dir / "user_102_daily_coach_intelligence_snapshot.json").exists()


def test_tool_artifacts_do_not_include_secrets_or_raw_provider_payloads(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    output_dir = tmp_path / "safe"

    tool.main(
        [
            "--user-id",
            "101",
            "--target-date",
            "2026-06-14",
            "--output-dir",
            str(output_dir),
            "--write-json",
            "--write-markdown",
            "--write-pasteback-report",
        ]
    )

    serialized = "\n".join(
        path.read_text(encoding="utf-8")
        for path in output_dir.iterdir()
        if path.is_file()
    ).lower()
    assert "api_key" not in serialized
    assert "authorization" not in serialized
    assert "raw_provider_envelope" not in serialized
    assert "provider_payload" not in serialized
    assert "select *" not in serialized
