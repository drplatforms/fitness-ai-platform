from __future__ import annotations

from dataclasses import dataclass

from services import training_execution_summary_service as service


@dataclass
class FakePlannedVsActualSummary:
    completion_percentage: float
    average_planned_rir: float | None = 2.5
    average_actual_rir: float | None = 2.5
    rir_deviation: float | None = 0
    skipped_exercise_count: int = 0
    substituted_exercise_count: int = 0
    sets_below_planned_reps: int = 0
    sets_inside_planned_reps: int = 0
    sets_above_planned_reps: int = 0
    missing_actual_rir_count: int = 0
    missing_actual_reps_count: int = 0
    deviation_flags: list[str] | None = None

    def __post_init__(self) -> None:
        if self.deviation_flags is None:
            self.deviation_flags = []


def _patch_execution_summaries(monkeypatch, summaries_by_plan_id):
    plan_ids = list(summaries_by_plan_id.keys())

    monkeypatch.setattr(
        service,
        "_get_recent_completed_plan_instance_ids",
        lambda user_id, limit: plan_ids,
    )
    monkeypatch.setattr(
        service,
        "_load_planned_vs_actual_summary",
        lambda plan_instance_id: summaries_by_plan_id[plan_instance_id],
    )


def test_no_completed_executions_returns_limited_no_data_summary(monkeypatch):
    monkeypatch.setattr(
        service,
        "_get_recent_completed_plan_instance_ids",
        lambda user_id, limit: [],
    )

    summary = service.build_training_execution_summary(user_id=42)

    assert summary.completed_execution_count == 0
    assert summary.recent_plan_instance_ids == []
    assert summary.execution_quality == "no_planned_execution_data"
    assert summary.execution_effort_trend == "no_planned_execution_data"
    assert summary.execution_completion_trend == "no_planned_execution_data"
    assert summary.confidence == "Limited"
    assert "no_completed_planned_executions" in summary.reason_codes


def test_one_completed_execution_produces_limited_execution_data(monkeypatch):
    _patch_execution_summaries(
        monkeypatch,
        {
            10: FakePlannedVsActualSummary(
                completion_percentage=100,
                average_planned_rir=2.5,
                average_actual_rir=2,
                rir_deviation=-0.5,
            )
        },
    )

    summary = service.build_training_execution_summary(user_id=42)

    assert summary.completed_execution_count == 1
    assert summary.recent_plan_instance_ids == [10]
    assert summary.execution_quality == "limited_execution_data"
    assert summary.confidence == "Low"
    assert "single_completed_execution_limited_confidence" in summary.reason_codes


def test_multiple_completed_executions_aggregate_completion_and_rir(monkeypatch):
    _patch_execution_summaries(
        monkeypatch,
        {
            12: FakePlannedVsActualSummary(
                completion_percentage=100,
                average_planned_rir=3,
                average_actual_rir=2,
                rir_deviation=-1,
            ),
            11: FakePlannedVsActualSummary(
                completion_percentage=90,
                average_planned_rir=3,
                average_actual_rir=2,
                rir_deviation=-1,
            ),
            10: FakePlannedVsActualSummary(
                completion_percentage=95,
                average_planned_rir=2,
                average_actual_rir=2,
                rir_deviation=0,
            ),
        },
    )

    summary = service.build_training_execution_summary(user_id=42)

    assert summary.completed_execution_count == 3
    assert summary.average_completion_percentage == 95
    assert summary.average_planned_rir == 2.67
    assert summary.average_actual_rir == 2
    assert summary.average_rir_deviation == -0.67
    assert summary.execution_quality == "consistently_completed"
    assert summary.confidence == "Moderate"


def test_incomplete_logging_lowers_confidence(monkeypatch):
    _patch_execution_summaries(
        monkeypatch,
        {
            11: FakePlannedVsActualSummary(
                completion_percentage=75,
                deviation_flags=["incomplete_logging"],
            ),
            10: FakePlannedVsActualSummary(completion_percentage=100),
        },
    )

    summary = service.build_training_execution_summary(user_id=42)

    assert summary.incomplete_logging_count == 1
    assert summary.confidence == "Low"
    assert "incomplete_logging_lowers_confidence" in summary.reason_codes


def test_skipped_exercises_are_plan_fit_signal_not_adherence_failure(monkeypatch):
    _patch_execution_summaries(
        monkeypatch,
        {
            11: FakePlannedVsActualSummary(
                completion_percentage=85,
                skipped_exercise_count=2,
                deviation_flags=["skipped_exercises_present"],
            ),
            10: FakePlannedVsActualSummary(completion_percentage=95),
        },
    )

    summary = service.build_training_execution_summary(user_id=42)

    assert summary.skipped_exercise_count == 2
    assert summary.execution_quality == "plan_fit_review_signal"
    assert "skipped_exercises_plan_fit_review_signal" in summary.reason_codes
    assert "poor_adherence" not in summary.reason_codes
    assert "failure" not in " ".join(summary.reason_codes)


def test_substitutions_are_plan_fit_signal_not_failure(monkeypatch):
    _patch_execution_summaries(
        monkeypatch,
        {
            11: FakePlannedVsActualSummary(
                completion_percentage=90,
                substituted_exercise_count=1,
                deviation_flags=["substitutions_present"],
            ),
            10: FakePlannedVsActualSummary(completion_percentage=95),
        },
    )

    summary = service.build_training_execution_summary(user_id=42)

    assert summary.substituted_exercise_count == 1
    assert summary.execution_quality == "plan_fit_review_signal"
    assert "substitutions_plan_fit_review_signal" in summary.reason_codes
    assert "failed_programming" not in summary.reason_codes


def test_harder_than_planned_rir_trend_is_detected_conservatively(monkeypatch):
    _patch_execution_summaries(
        monkeypatch,
        {
            11: FakePlannedVsActualSummary(
                completion_percentage=100,
                average_planned_rir=3,
                average_actual_rir=1.5,
                rir_deviation=-1.5,
            ),
            10: FakePlannedVsActualSummary(
                completion_percentage=100,
                average_planned_rir=3,
                average_actual_rir=2,
                rir_deviation=-1,
            ),
        },
    )

    summary = service.build_training_execution_summary(user_id=42)

    assert summary.execution_effort_trend == "harder_than_planned"
    assert "actual_effort_harder_than_planned" in summary.reason_codes
    assert "overtraining" not in " ".join(summary.reason_codes)
    assert "deload" not in " ".join(summary.reason_codes)


def test_easier_than_planned_rir_trend_is_detected_conservatively(monkeypatch):
    _patch_execution_summaries(
        monkeypatch,
        {
            11: FakePlannedVsActualSummary(
                completion_percentage=100,
                average_planned_rir=2,
                average_actual_rir=3.5,
                rir_deviation=1.5,
            ),
            10: FakePlannedVsActualSummary(
                completion_percentage=100,
                average_planned_rir=2,
                average_actual_rir=3,
                rir_deviation=1,
            ),
        },
    )

    summary = service.build_training_execution_summary(user_id=42)

    assert summary.execution_effort_trend == "easier_than_planned"
    assert "actual_effort_easier_than_planned" in summary.reason_codes
    assert "automatic_progression" not in summary.reason_codes


def test_reps_below_inside_and_above_planned_ranges_are_aggregated(monkeypatch):
    _patch_execution_summaries(
        monkeypatch,
        {
            11: FakePlannedVsActualSummary(
                completion_percentage=90,
                sets_below_planned_reps=2,
                sets_inside_planned_reps=5,
                sets_above_planned_reps=1,
            ),
            10: FakePlannedVsActualSummary(
                completion_percentage=90,
                sets_below_planned_reps=1,
                sets_inside_planned_reps=4,
                sets_above_planned_reps=2,
            ),
        },
    )

    summary = service.build_training_execution_summary(user_id=42)

    assert summary.sets_below_planned_reps == 3
    assert summary.sets_inside_planned_reps == 9
    assert summary.sets_above_planned_reps == 3
    assert "sets_below_planned_reps" in summary.reason_codes
    assert "sets_above_planned_reps" in summary.reason_codes


def test_missing_actual_rir_and_reps_lower_confidence(monkeypatch):
    _patch_execution_summaries(
        monkeypatch,
        {
            11: FakePlannedVsActualSummary(
                completion_percentage=100,
                missing_actual_rir_count=2,
                missing_actual_reps_count=1,
                deviation_flags=["missing_actual_rir", "missing_actual_reps"],
            ),
            10: FakePlannedVsActualSummary(completion_percentage=100),
        },
    )

    summary = service.build_training_execution_summary(user_id=42)

    assert summary.missing_actual_rir_count == 2
    assert summary.missing_actual_reps_count == 1
    assert summary.confidence == "Low"
    assert "missing_actual_rir_lowers_confidence" in summary.reason_codes
    assert "missing_actual_reps_lowers_confidence" in summary.reason_codes


def test_completed_workout_corrections_are_reflected_dynamically(monkeypatch):
    monkeypatch.setattr(
        service,
        "_get_recent_completed_plan_instance_ids",
        lambda user_id, limit: [10],
    )

    corrected_summary = {"value": FakePlannedVsActualSummary(completion_percentage=60)}

    def fake_load_summary(plan_instance_id):
        return corrected_summary["value"]

    monkeypatch.setattr(service, "_load_planned_vs_actual_summary", fake_load_summary)

    first_summary = service.build_training_execution_summary(user_id=42)

    corrected_summary["value"] = FakePlannedVsActualSummary(completion_percentage=100)

    second_summary = service.build_training_execution_summary(user_id=42)

    assert first_summary.average_completion_percentage == 60
    assert second_summary.average_completion_percentage == 100


def test_manual_workout_logs_are_not_used_for_planned_vs_actual(monkeypatch):
    _patch_execution_summaries(
        monkeypatch,
        {
            10: FakePlannedVsActualSummary(completion_percentage=100),
        },
    )

    summary = service.build_training_execution_summary(user_id=42)

    assert "manual_workout_logs_not_used_for_planned_vs_actual" in summary.reason_codes
