from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

_ALLOWED_FEEDBACK_LABELS = {"bad", "better", "approved"}
_ALLOWED_SCENARIO_SOURCES = {
    "synthetic",
    "seeded_qa",
    "current_day",
    "provider_preview",
}
_ALLOWED_CANDIDATE_SOURCES = {"deterministic", "provider"}
_FORBIDDEN_STORAGE_FRAGMENTS = (
    "raw_food",
    "raw food",
    "raw_workout",
    "raw workout",
    "raw_set",
    "raw set",
    "raw_check",
    "raw check",
    "secret",
    "api_key",
    "password",
    "chain-of-thought",
    "scratchpad",
    "prompt:",
)


@dataclass(frozen=True)
class DailyNarrativeFeedbackInput:
    scenario_id: str
    scenario_label: str
    scenario_source: str
    candidate_id: str
    candidate_source: str
    candidate_text: str
    feedback_label: str
    rejected_phrase: str = ""
    preferred_rewrite: str = ""
    user_notes: str = ""
    reason_codes: tuple[str, ...] = ()
    data_quality: str = ""
    confidence: str = ""
    domains_present: tuple[str, ...] = ()
    domains_missing: tuple[str, ...] = ()
    coaching_angle: str = ""
    copy_quality_warnings: tuple[str, ...] = ()
    provider_model: str = ""
    provider_name: str = ""
    app_version_or_git_commit: str = ""


@dataclass(frozen=True)
class DailyNarrativeFeedbackRecord:
    feedback_id: str
    created_at: str
    scenario_id: str
    scenario_label: str
    scenario_source: str
    candidate_id: str
    candidate_source: str
    candidate_text: str
    feedback_label: str
    rejected_phrase: str = ""
    preferred_rewrite: str = ""
    user_notes: str = ""
    reason_codes: tuple[str, ...] = ()
    data_quality: str = ""
    confidence: str = ""
    domains_present: tuple[str, ...] = ()
    domains_missing: tuple[str, ...] = ()
    coaching_angle: str = ""
    copy_quality_warnings: tuple[str, ...] = ()
    provider_model: str = ""
    provider_name: str = ""
    app_version_or_git_commit: str = ""
    raw_data_included: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_daily_narrative_feedback_path() -> Path:
    configured = os.getenv("DAILY_NARRATIVE_FEEDBACK_PATH")
    if configured:
        return Path(configured)
    return Path("artifacts") / "daily_narrative_feedback.jsonl"


def save_daily_narrative_feedback(
    feedback: DailyNarrativeFeedbackInput,
    *,
    path: str | Path | None = None,
) -> DailyNarrativeFeedbackRecord:
    record = build_daily_narrative_feedback_record(feedback)
    target_path = (
        Path(path) if path is not None else default_daily_narrative_feedback_path()
    )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
    return record


def build_daily_narrative_feedback_record(
    feedback: DailyNarrativeFeedbackInput,
) -> DailyNarrativeFeedbackRecord:
    _validate_feedback_input(feedback)
    record = DailyNarrativeFeedbackRecord(
        feedback_id=str(uuid.uuid4()),
        created_at=datetime.now(UTC).isoformat(),
        scenario_id=feedback.scenario_id.strip(),
        scenario_label=feedback.scenario_label.strip(),
        scenario_source=feedback.scenario_source.strip(),
        candidate_id=feedback.candidate_id.strip(),
        candidate_source=feedback.candidate_source.strip(),
        candidate_text=feedback.candidate_text.strip(),
        feedback_label=feedback.feedback_label.strip().lower(),
        rejected_phrase=feedback.rejected_phrase.strip(),
        preferred_rewrite=feedback.preferred_rewrite.strip(),
        user_notes=feedback.user_notes.strip(),
        reason_codes=tuple(feedback.reason_codes),
        data_quality=feedback.data_quality.strip(),
        confidence=feedback.confidence.strip(),
        domains_present=tuple(feedback.domains_present),
        domains_missing=tuple(feedback.domains_missing),
        coaching_angle=feedback.coaching_angle.strip(),
        copy_quality_warnings=tuple(feedback.copy_quality_warnings),
        provider_model=feedback.provider_model.strip(),
        provider_name=feedback.provider_name.strip(),
        app_version_or_git_commit=feedback.app_version_or_git_commit.strip(),
        raw_data_included=False,
    )
    _assert_feedback_record_public_safe(record)
    return record


def list_daily_narrative_feedback(
    *,
    path: str | Path | None = None,
    scenario_id: str | None = None,
    limit: int | None = None,
) -> list[DailyNarrativeFeedbackRecord]:
    target_path = (
        Path(path) if path is not None else default_daily_narrative_feedback_path()
    )
    if not target_path.exists():
        return []
    records: list[DailyNarrativeFeedbackRecord] = []
    with target_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            record = _record_from_payload(payload)
            if scenario_id and record.scenario_id != scenario_id:
                continue
            records.append(record)
    if limit is not None and limit >= 0:
        return records[-limit:]
    return records


def export_daily_narrative_feedback(
    *,
    path: str | Path | None = None,
    scenario_id: str | None = None,
) -> list[dict[str, object]]:
    return [
        record.to_dict()
        for record in list_daily_narrative_feedback(path=path, scenario_id=scenario_id)
    ]


def summarize_daily_narrative_feedback(
    *,
    path: str | Path | None = None,
) -> dict[str, object]:
    records = list_daily_narrative_feedback(path=path)
    by_label: dict[str, int] = {"bad": 0, "better": 0, "approved": 0}
    by_scenario: dict[str, int] = {}
    rejected_phrases: list[str] = []
    preferred_rewrites: list[str] = []
    for record in records:
        by_label[record.feedback_label] = by_label.get(record.feedback_label, 0) + 1
        by_scenario[record.scenario_id] = by_scenario.get(record.scenario_id, 0) + 1
        if record.rejected_phrase:
            rejected_phrases.append(record.rejected_phrase)
        if record.preferred_rewrite:
            preferred_rewrites.append(record.preferred_rewrite)
    return {
        "count": len(records),
        "by_label": by_label,
        "by_scenario": by_scenario,
        "recent_rejected_phrases": rejected_phrases[-10:],
        "recent_preferred_rewrites": preferred_rewrites[-10:],
    }


def feedback_record_contains_forbidden_private_data(
    record: DailyNarrativeFeedbackRecord,
) -> bool:
    serialized = json.dumps(record.to_dict(), sort_keys=True).lower()
    return any(fragment in serialized for fragment in _FORBIDDEN_STORAGE_FRAGMENTS)


def _validate_feedback_input(feedback: DailyNarrativeFeedbackInput) -> None:
    if not feedback.scenario_id.strip():
        raise ValueError("scenario_id is required")
    if not feedback.scenario_label.strip():
        raise ValueError("scenario_label is required")
    if feedback.scenario_source not in _ALLOWED_SCENARIO_SOURCES:
        raise ValueError(f"Unsupported scenario_source: {feedback.scenario_source}")
    if not feedback.candidate_id.strip():
        raise ValueError("candidate_id is required")
    if feedback.candidate_source not in _ALLOWED_CANDIDATE_SOURCES:
        raise ValueError(f"Unsupported candidate_source: {feedback.candidate_source}")
    if not feedback.candidate_text.strip():
        raise ValueError("candidate_text is required")
    if feedback.feedback_label.lower() not in _ALLOWED_FEEDBACK_LABELS:
        raise ValueError(f"Unsupported feedback_label: {feedback.feedback_label}")


def _assert_feedback_record_public_safe(record: DailyNarrativeFeedbackRecord) -> None:
    if record.raw_data_included:
        raise ValueError("feedback records must not include raw data")
    if feedback_record_contains_forbidden_private_data(record):
        raise ValueError("feedback record contains forbidden private/debug data")


def _record_from_payload(payload: dict[str, object]) -> DailyNarrativeFeedbackRecord:
    tuple_fields = {
        "reason_codes",
        "domains_present",
        "domains_missing",
        "copy_quality_warnings",
    }
    clean = dict(payload)
    for field_name in tuple_fields:
        value = clean.get(field_name, ())
        clean[field_name] = tuple(str(item) for item in _as_iterable(value))
    return DailyNarrativeFeedbackRecord(**clean)


def _as_iterable(value: object) -> Iterable[object]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return value
    return ()
