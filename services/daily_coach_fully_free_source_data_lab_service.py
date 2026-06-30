from __future__ import annotations

import csv
import json
import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from services.daily_coach_full_user_day_free_range_service import (
    BASELINE_DRIFT,
    DEFAULT_FULL_USER_DAY_MODEL,
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
    DailyCoachFullUserDayFreeRangeError,
    _call_direct_ollama_full_user_day_note,
    _call_openai_full_user_day_note,
    _timeout_seconds,
    build_daily_coach_full_user_day_packet,
    list_daily_coach_full_user_day_scenarios,
    scan_full_user_day_claim_risk,
)
from services.daily_coach_natural_draft_audit_service import (
    get_daily_coach_natural_draft_scenario,
)

DEFAULT_FULLY_FREE_OUTPUT_DIR = (
    "docs/provider_trials/daily_coach_fully_free_source_data_lab_v1"
)
DEFAULT_FULLY_FREE_PROVIDER = PROVIDER_DETERMINISTIC
DEFAULT_FULLY_FREE_MODEL = DEFAULT_FULL_USER_DAY_MODEL
FULLY_FREE_PROVIDER_ENV = "DAILY_COACH_FULLY_FREE_PROVIDER"
FULLY_FREE_MODEL_ENV = "DAILY_COACH_FULLY_FREE_MODEL"
FULLY_FREE_MAX_OUTPUT_TOKENS_ENV = "DAILY_COACH_FULLY_FREE_MAX_OUTPUT_TOKENS"
SUPPORTED_FULLY_FREE_PROVIDERS = (
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
)

BACKEND_PROSE_PATTERNS: tuple[str, ...] = (
    "approved option",
    "approved protein option",
    "approved food option",
    "main lever",
    "limiter",
    "anchor",
    "confidence",
    "protein gap",
    "macro gap",
    "volume load",
    "volume_load",
    "weight_change",
    "set_level_data_available",
    "Rapid Increase",
    "Progressing",
    "High adherence",
    "training load",
    "green-light day skeleton",
    "planned workout as written",
    "fix the day",
    "real protein feeding",
    "logging uncertainty",
)

DEBUG_ONLY_KEYS: tuple[str, ...] = (
    "confidence",
    "gap",
    "macro_gap",
    "value_precision",
    "quote_style",
    "volume_load",
    "weight_change",
    "internal_workout_model",
    "set_level_data_available",
    "training_load",
    "limiter",
    "anchor",
    "main_lever",
)

SAFETY_BOUNDARIES: tuple[str, ...] = (
    "Use only the source data provided.",
    "Do not invent workouts, foods, macros, targets, injuries, diagnoses, or user facts.",
    "Do not diagnose medical conditions.",
    "Do not recommend unsafe training or ignoring pain.",
    "If source data is incomplete, handle that naturally.",
)

FullyFreeProviderCallable = Callable[
    [str, str, float, Mapping[str, str]], dict[str, Any]
]


@dataclass(frozen=True)
class FullyFreePromptVariant:
    variant_id: str
    label: str
    description: str
    extra_instruction: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FullyFreeDraftResult:
    scenario_id: str
    user_id: int
    date: str
    provider: str
    model: str | None
    variant_id: str
    repeat_index: int
    skipped: bool
    skip_reason: str | None
    first_pass_draft: str
    provider_input_prompt: str | None
    source_data_packet: dict[str, Any] | None
    runtime_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FullyFreeRunResult:
    run_id: str
    scenario_id: str
    user_id: int
    date: str
    provider: str
    model: str | None
    variants: tuple[FullyFreeDraftResult, ...]
    baseline_drift: dict[str, Any]
    runtime_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def list_daily_coach_fully_free_source_data_scenarios() -> list[dict[str, Any]]:
    return list_daily_coach_full_user_day_scenarios()


def list_daily_coach_fully_free_prompt_variants() -> list[dict[str, Any]]:
    return [variant.to_dict() for variant in _fully_free_prompt_variants().values()]


def run_daily_coach_fully_free_source_data_lab_scenario(
    *,
    scenario_id: str,
    provider: str = DEFAULT_FULLY_FREE_PROVIDER,
    model: str | None = None,
    variants: Sequence[str] | None = None,
    repeat: int = 1,
    allow_live_provider: bool = False,
    output_dir: Path | None = None,
    write_provider_payload_debug: bool = False,
    write_source_data_packet: bool = False,
    write_source_data_completeness_summary: bool = False,
    write_model_freedom_summary: bool = False,
    write_backend_prose_contamination_summary: bool = False,
    write_completion_diagnostics: bool = False,
    write_pasteback_report: bool = False,
    environ: Mapping[str, str] | None = None,
    provider_generate: FullyFreeProviderCallable | None = None,
) -> FullyFreeRunResult:
    env = dict(os.environ if environ is None else environ)
    scenario = get_daily_coach_natural_draft_scenario(scenario_id)
    resolved_provider = _configured_fully_free_provider(provider, env)
    if resolved_provider not in SUPPORTED_FULLY_FREE_PROVIDERS:
        resolved_provider = PROVIDER_DETERMINISTIC
    resolved_model = model or env.get(FULLY_FREE_MODEL_ENV) or DEFAULT_FULLY_FREE_MODEL
    selected_variants = tuple(variants or _default_fully_free_variant_order())
    resolved_repeat = max(1, min(int(repeat or 1), 10))
    user_id = int(scenario["user_id"])
    target_date = str(scenario["target_date"])
    run_id = _build_run_id(resolved_provider, scenario_id)

    try:
        source_packet = build_fully_free_source_data_packet(
            user_id=user_id,
            target_date=target_date,
            scenario_id=scenario_id,
        )
    except Exception as exc:  # noqa: BLE001 - dev diagnostic path captures setup failure
        result = _skipped_setup_run(
            run_id=run_id,
            scenario_id=scenario_id,
            user_id=user_id,
            target_date=target_date,
            provider=resolved_provider,
            model=resolved_model,
            variants=selected_variants,
            repeat=resolved_repeat,
            reason=f"fully_free_source_data_packet_build_failed:{_safe_error(exc)}",
        )
        if output_dir:
            write_daily_coach_fully_free_source_data_lab_artifacts(
                output_dir,
                [result],
                write_provider_payload_debug=write_provider_payload_debug,
                write_source_data_packet=write_source_data_packet,
                write_source_data_completeness_summary=write_source_data_completeness_summary,
                write_model_freedom_summary=write_model_freedom_summary,
                write_backend_prose_contamination_summary=write_backend_prose_contamination_summary,
                write_completion_diagnostics=write_completion_diagnostics,
                write_pasteback_report=write_pasteback_report,
            )
        return result

    draft_results: list[FullyFreeDraftResult] = []
    for variant_id in selected_variants:
        for repeat_index in range(1, resolved_repeat + 1):
            draft_results.append(
                _run_fully_free_variant(
                    source_packet=source_packet,
                    variant_id=variant_id,
                    repeat_index=repeat_index,
                    provider=resolved_provider,
                    model=resolved_model,
                    allow_live_provider=allow_live_provider,
                    environ=env,
                    provider_generate=provider_generate,
                )
            )

    result = FullyFreeRunResult(
        run_id=run_id,
        scenario_id=scenario_id,
        user_id=user_id,
        date=target_date,
        provider=resolved_provider,
        model=resolved_model,
        variants=tuple(draft_results),
        baseline_drift=dict(BASELINE_DRIFT),
        runtime_metadata={
            "milestone": "daily_coach_fully_free_source_data_lab_v1",
            "developer_only": True,
            "normal_today_unchanged": True,
            "provider_promotion": False,
            "source_data_packet_version": source_packet.get("packet_version"),
            "model_freedom_summary": build_model_freedom_summary(
                build_fully_free_source_data_prompt(source_packet, selected_variants[0])
            ),
        },
    )
    if output_dir:
        write_daily_coach_fully_free_source_data_lab_artifacts(
            output_dir,
            [result],
            write_provider_payload_debug=write_provider_payload_debug,
            write_source_data_packet=write_source_data_packet,
            write_source_data_completeness_summary=write_source_data_completeness_summary,
            write_model_freedom_summary=write_model_freedom_summary,
            write_backend_prose_contamination_summary=write_backend_prose_contamination_summary,
            write_completion_diagnostics=write_completion_diagnostics,
            write_pasteback_report=write_pasteback_report,
        )
    return result


def run_daily_coach_fully_free_source_data_lab_matrix(
    *,
    scenarios: Sequence[str] | None = None,
    provider: str = DEFAULT_FULLY_FREE_PROVIDER,
    model: str | None = None,
    variants: Sequence[str] | None = None,
    repeat: int = 1,
    allow_live_provider: bool = False,
    output_dir: Path | None = None,
    write_provider_payload_debug: bool = False,
    write_source_data_packet: bool = False,
    write_source_data_completeness_summary: bool = False,
    write_model_freedom_summary: bool = False,
    write_backend_prose_contamination_summary: bool = False,
    write_completion_diagnostics: bool = False,
    write_pasteback_report: bool = False,
    environ: Mapping[str, str] | None = None,
    provider_generate: FullyFreeProviderCallable | None = None,
) -> list[FullyFreeRunResult]:
    scenario_ids = tuple(scenarios or ("rich_nutrition_training_recovery",))
    results = [
        run_daily_coach_fully_free_source_data_lab_scenario(
            scenario_id=scenario_id,
            provider=provider,
            model=model,
            variants=variants,
            repeat=repeat,
            allow_live_provider=allow_live_provider,
            output_dir=None,
            write_provider_payload_debug=write_provider_payload_debug,
            write_source_data_packet=write_source_data_packet,
            write_source_data_completeness_summary=write_source_data_completeness_summary,
            write_model_freedom_summary=write_model_freedom_summary,
            write_backend_prose_contamination_summary=write_backend_prose_contamination_summary,
            write_completion_diagnostics=write_completion_diagnostics,
            write_pasteback_report=write_pasteback_report,
            environ=environ,
            provider_generate=provider_generate,
        )
        for scenario_id in scenario_ids
    ]
    if output_dir:
        write_daily_coach_fully_free_source_data_lab_artifacts(
            output_dir,
            results,
            write_provider_payload_debug=write_provider_payload_debug,
            write_source_data_packet=write_source_data_packet,
            write_source_data_completeness_summary=write_source_data_completeness_summary,
            write_model_freedom_summary=write_model_freedom_summary,
            write_backend_prose_contamination_summary=write_backend_prose_contamination_summary,
            write_completion_diagnostics=write_completion_diagnostics,
            write_pasteback_report=write_pasteback_report,
        )
    return results


def build_fully_free_source_data_packet(
    *, user_id: int, target_date: str, scenario_id: str
) -> dict[str, Any]:
    full_packet = build_daily_coach_full_user_day_packet(
        user_id=user_id, target_date=target_date, scenario_id=scenario_id
    )
    payload = full_packet.to_dict()
    nutrition = payload.get("nutrition") or {}
    training = payload.get("training") or {}
    recovery = payload.get("recovery") or {}
    food_candidates = tuple(payload.get("food_candidates") or ())
    snack_candidates = tuple(payload.get("ai_snack_candidates") or ())
    source_packet = {
        "packet_version": "fully_free_source_data_lab_v1",
        "user_context": _clean_mapping(payload.get("user_profile") or {}),
        "today_context": {
            "date": target_date,
            "scenario_id": scenario_id,
            "note": "This is a developer-only source-data lab packet for a Daily Coach note.",
        },
        "recovery_source_data": _plain_recovery_source(recovery),
        "training_source_data": _plain_training_source(training),
        "nutrition_source_data": _plain_nutrition_source(nutrition, payload),
        "food_and_snack_source_data": _plain_food_and_snack_source(
            food_candidates, snack_candidates, payload
        ),
        "body_metrics_source_data": _plain_body_metrics_source(payload),
        "recent_history_source_data": _plain_recent_history_source(training, recovery),
        "available_unknowns": _available_unknowns(payload),
        "safety_boundaries": list(SAFETY_BOUNDARIES),
        "debug_reference": {
            "source_full_user_day_packet_available": True,
            "debug_artifacts_may_include_internal_labels": True,
            "model_facing_packet_avoids_backend_prose": True,
        },
    }
    return _drop_empty(_strip_backend_labels(source_packet))


def build_fully_free_source_data_prompt(
    source_packet: Mapping[str, Any], variant_id: str
) -> str:
    variant = _resolve_fully_free_variant(variant_id)
    packet_text = json.dumps(source_packet, indent=2, sort_keys=True, default=str)
    return "\n".join(
        [
            "You are writing a Daily Coach note for a fitness app user.",
            "",
            "Use only the source data provided.",
            "Do not invent facts.",
            "Do not diagnose medical conditions.",
            "Do not recommend unsafe training.",
            "Write naturally, like a real coach.",
            "Choose what matters most.",
            "You do not need to mention every fact.",
            "If the data is incomplete, handle that naturally.",
            "If numbers are useful, use the display-ready values.",
            "If a metric would confuse a normal user, explain it simply or leave it out.",
            "",
            variant.extra_instruction,
            "",
            "Write the best coach note you can.",
            "",
            "SOURCE_DATA_JSON:",
            packet_text,
        ]
    )


def build_model_freedom_summary(prompt: str) -> dict[str, Any]:
    return {
        "prompt_length": len(prompt),
        "explicit_style_constraints": 3,
        "safety_constraints": 4,
        "examples_included": False,
        "deterministic_coach_prose_included": False,
        "renderer_structure_included": False,
        "phrase_bans_included": False,
        "output_structure_forced": False,
        "model_can_choose_what_matters": "Choose what matters most" in prompt,
        "minimal_prompt_lab": True,
    }


def write_daily_coach_fully_free_source_data_lab_artifacts(
    output_dir: Path,
    results: Sequence[FullyFreeRunResult],
    *,
    write_provider_payload_debug: bool = False,
    write_source_data_packet: bool = False,
    write_source_data_completeness_summary: bool = False,
    write_model_freedom_summary: bool = False,
    write_backend_prose_contamination_summary: bool = False,
    write_completion_diagnostics: bool = False,
    write_pasteback_report: bool = False,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    flags = {
        "write_provider_payload_debug": write_provider_payload_debug,
        "write_source_data_packet": write_source_data_packet,
        "write_source_data_completeness_summary": write_source_data_completeness_summary,
        "write_model_freedom_summary": write_model_freedom_summary,
        "write_backend_prose_contamination_summary": write_backend_prose_contamination_summary,
        "write_completion_diagnostics": write_completion_diagnostics,
        "write_pasteback_report": write_pasteback_report,
    }
    _write_json(
        output_dir / "run_config.json",
        {
            "milestone": "daily_coach_fully_free_source_data_lab_v1",
            "developer_only": True,
            "normal_today_unchanged": True,
            "provider_promotion": False,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "run_count": len(results),
            "flags": flags,
            "baseline_drift": dict(BASELINE_DRIFT),
        },
    )
    _write_text(
        output_dir / "provider_input_prompt.md", _render_provider_input(results)
    )
    _write_json(
        output_dir / "provider_payload_debug.json", _provider_payload_debug(results)
    )
    _write_json(
        output_dir / "fully_free_source_data_packet.json", _source_packets(results)
    )
    _write_text(
        output_dir / "fully_free_source_data_packet.md", _render_source_packets(results)
    )
    _write_text(output_dir / "first_pass_drafts.md", _render_first_pass_drafts(results))
    _write_text(
        output_dir / "first_pass_drafts_compact.md", _render_first_pass_drafts(results)
    )
    _write_text(
        output_dir / "side_by_side_comparison.md", _render_side_by_side(results)
    )
    _write_text(output_dir / "best_variant_summary.md", _render_best_variant(results))
    _write_text(output_dir / "claim_risk_summary.md", _render_claim_risk(results))
    _write_text(output_dir / "consistency_summary.md", _render_consistency(results))
    _write_text(output_dir / "token_cost_telemetry.md", _render_token_cost(results))
    _write_token_cost_csv(output_dir / "token_cost_telemetry.csv", results)
    _write_text(output_dir / "artifact_safety_summary.md", _render_artifact_safety())
    _write_text(
        output_dir / "source_data_completeness_summary.md",
        _render_source_data_completeness(results),
    )
    _write_json(
        output_dir / "source_data_completeness_summary.json",
        build_source_data_completeness_summary(results),
    )
    _write_text(output_dir / "model_freedom_summary.md", _render_model_freedom(results))
    _write_json(
        output_dir / "model_freedom_summary.json",
        build_model_freedom_summaries(results),
    )
    _write_text(
        output_dir / "backend_prose_contamination_summary.md",
        _render_backend_prose_contamination(results),
    )
    _write_json(
        output_dir / "backend_prose_contamination_summary.json",
        build_backend_prose_contamination_summary(results),
    )
    _write_text(
        output_dir / "completion_diagnostics.md",
        _render_completion_diagnostics(results),
    )
    _write_json(
        output_dir / "completion_diagnostics.json",
        build_completion_diagnostics(results),
    )
    _write_text(output_dir / "v4_vs_fully_free_comparison.md", _render_v4_comparison())
    _write_text(
        output_dir / "variant_quality_notes.md", _render_variant_quality_notes(results)
    )
    _write_text(
        output_dir / "source_data_missing_for_future_agents.md",
        _render_source_data_missing_for_future_agents(results),
    )
    _write_text(output_dir / "pasteback_report.md", _render_pasteback_report(results))


def build_source_data_completeness_summary(
    results: Sequence[FullyFreeRunResult],
) -> dict[str, Any]:
    rows = []
    for packet in _unique_source_packets(results):
        rows.append(
            {
                "scenario_id": packet.get("today_context", {}).get("scenario_id"),
                "user_context_received": bool(packet.get("user_context")),
                "recovery_details_received": bool(packet.get("recovery_source_data")),
                "training_details_received": bool(packet.get("training_source_data")),
                "set_level_workout_data_received": bool(
                    packet.get("training_source_data", {}).get("set_level_workout_data")
                ),
                "nutrition_logs_received": bool(packet.get("nutrition_source_data")),
                "macro_targets_received": bool(
                    packet.get("nutrition_source_data", {}).get("macro_display")
                ),
                "food_options_received": bool(
                    packet.get("food_and_snack_source_data", {}).get("food_options")
                ),
                "snack_options_received": bool(
                    packet.get("food_and_snack_source_data", {}).get("snack_options")
                ),
                "recent_history_received": bool(
                    packet.get("recent_history_source_data")
                ),
                "trend_data_received": bool(packet.get("recent_history_source_data")),
                "available_unknowns": packet.get("available_unknowns") or [],
                "future_data_needs": _future_data_needs(packet),
            }
        )
    return {"records": rows}


def build_model_freedom_summaries(
    results: Sequence[FullyFreeRunResult],
) -> dict[str, Any]:
    records = []
    for variant in _iter_variants(results):
        prompt = variant.provider_input_prompt or ""
        records.append(
            {
                "scenario_id": variant.scenario_id,
                "variant_id": variant.variant_id,
                "repeat_index": variant.repeat_index,
                **build_model_freedom_summary(prompt),
            }
        )
    return {"records": records}


def build_backend_prose_contamination_summary(
    results: Sequence[FullyFreeRunResult],
) -> dict[str, Any]:
    records = []
    for variant in _iter_variants(results):
        packet_md = _render_single_source_packet(variant.source_data_packet or {})
        prompt = variant.provider_input_prompt or ""
        draft = variant.first_pass_draft or ""
        records.append(
            {
                "scenario_id": variant.scenario_id,
                "variant_id": variant.variant_id,
                "repeat_index": variant.repeat_index,
                "provider_prompt_findings": _contamination_findings(prompt),
                "source_packet_findings": _contamination_findings(packet_md),
                "first_pass_findings": _contamination_findings(draft),
                "mutated_first_pass": False,
            }
        )
    return {"patterns": list(BACKEND_PROSE_PATTERNS), "records": records}


def build_completion_diagnostics(
    results: Sequence[FullyFreeRunResult],
) -> dict[str, Any]:
    records = []
    for variant in _iter_variants(results):
        metadata = variant.runtime_metadata
        truncated = bool(metadata.get("truncated"))
        skipped = bool(variant.skipped)
        captured = bool(variant.first_pass_draft and not skipped)
        records.append(
            {
                "scenario_id": variant.scenario_id,
                "variant_id": variant.variant_id,
                "repeat_index": variant.repeat_index,
                "skipped": skipped,
                "captured": captured,
                "completion_status": metadata.get("completion_status"),
                "finish_reason": metadata.get("finish_reason"),
                "output_tokens": metadata.get("output_tokens"),
                "max_output_tokens": metadata.get("max_output_tokens"),
                "truncated": truncated,
                "truncation_heuristics": metadata.get("truncation_heuristics") or [],
            }
        )
    expected = len(records)
    return {
        "summary": {
            "expected_drafts": expected,
            "captured_drafts": sum(1 for row in records if row["captured"]),
            "complete_drafts": sum(
                1 for row in records if row["captured"] and not row["truncated"]
            ),
            "truncated_drafts": sum(1 for row in records if row["truncated"]),
            "skipped_drafts": sum(1 for row in records if row["skipped"]),
        },
        "records": records,
    }


def _run_fully_free_variant(
    *,
    source_packet: Mapping[str, Any],
    variant_id: str,
    repeat_index: int,
    provider: str,
    model: str,
    allow_live_provider: bool,
    environ: Mapping[str, str],
    provider_generate: FullyFreeProviderCallable | None,
) -> FullyFreeDraftResult:
    prompt = build_fully_free_source_data_prompt(source_packet, variant_id)
    user_id = int(source_packet.get("user_context", {}).get("user_id") or 0)
    today = source_packet.get("today_context") or {}
    scenario_id = str(today.get("scenario_id") or "unknown")
    date = str(today.get("date") or "unknown")
    if provider != PROVIDER_DETERMINISTIC and not allow_live_provider:
        return FullyFreeDraftResult(
            scenario_id=scenario_id,
            user_id=user_id,
            date=date,
            provider=provider,
            model=model,
            variant_id=variant_id,
            repeat_index=repeat_index,
            skipped=True,
            skip_reason="live_provider_not_allowed",
            first_pass_draft="",
            provider_input_prompt=prompt,
            source_data_packet=dict(source_packet),
            runtime_metadata=_runtime_metadata(
                prompt=prompt,
                provider_attempted=False,
                max_output_tokens=_fully_free_max_output_tokens(environ),
            ),
        )
    if provider == PROVIDER_DETERMINISTIC:
        raw_text = _deterministic_fully_free_draft(source_packet, variant_id)
        call_payload = {
            "raw_text": raw_text,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "cached_input_tokens": None,
            "estimated_cost_usd": None,
            "cost_estimate_basis": "deterministic_no_provider_cost",
            "finish_reason": "complete",
            "completion_status": "completed",
            "max_output_tokens": _fully_free_max_output_tokens(environ),
        }
        provider_attempted = False
    else:
        try:
            call_payload = _call_fully_free_provider(
                provider=provider,
                model=model,
                prompt=prompt,
                environ=environ,
                provider_generate=provider_generate,
            )
        except Exception as exc:  # noqa: BLE001
            return FullyFreeDraftResult(
                scenario_id=scenario_id,
                user_id=user_id,
                date=date,
                provider=provider,
                model=model,
                variant_id=variant_id,
                repeat_index=repeat_index,
                skipped=True,
                skip_reason=_safe_error(exc),
                first_pass_draft="",
                provider_input_prompt=prompt,
                source_data_packet=dict(source_packet),
                runtime_metadata=_runtime_metadata(
                    prompt=prompt,
                    provider_attempted=True,
                    provider_error=_safe_error(exc),
                    max_output_tokens=_fully_free_max_output_tokens(environ),
                ),
            )
        provider_attempted = True
    raw_text = str(call_payload.get("raw_text") or "").strip()
    reasons = _completion_truncation_reasons(
        raw_text,
        output_tokens=_optional_int(call_payload.get("output_tokens")),
        max_output_tokens=_optional_int(call_payload.get("max_output_tokens")),
        finish_reason=call_payload.get("finish_reason"),
    )
    return FullyFreeDraftResult(
        scenario_id=scenario_id,
        user_id=user_id,
        date=date,
        provider=provider,
        model=model,
        variant_id=variant_id,
        repeat_index=repeat_index,
        skipped=False,
        skip_reason=None,
        first_pass_draft=raw_text,
        provider_input_prompt=prompt,
        source_data_packet=dict(source_packet),
        runtime_metadata=_runtime_metadata(
            prompt=prompt,
            provider_attempted=provider_attempted,
            input_tokens=call_payload.get("input_tokens"),
            output_tokens=call_payload.get("output_tokens"),
            total_tokens=call_payload.get("total_tokens"),
            cached_input_tokens=call_payload.get("cached_input_tokens"),
            estimated_cost_usd=call_payload.get("estimated_cost_usd"),
            cost_estimate_basis=call_payload.get("cost_estimate_basis"),
            finish_reason=call_payload.get("finish_reason"),
            completion_status=call_payload.get("completion_status"),
            max_output_tokens=call_payload.get("max_output_tokens"),
            truncated=bool(reasons),
            truncation_heuristics=reasons,
        ),
    )


def _call_fully_free_provider(
    *,
    provider: str,
    model: str,
    prompt: str,
    environ: Mapping[str, str],
    provider_generate: FullyFreeProviderCallable | None,
) -> dict[str, Any]:
    env = dict(environ)
    env.setdefault(
        FULLY_FREE_MAX_OUTPUT_TOKENS_ENV, str(_fully_free_max_output_tokens(env))
    )
    env.setdefault(
        "DAILY_COACH_FULL_USER_DAY_MAX_OUTPUT_TOKENS",
        env[FULLY_FREE_MAX_OUTPUT_TOKENS_ENV],
    )
    timeout = _timeout_seconds(provider, env)
    generate = provider_generate
    if generate:
        result = generate(model, prompt, timeout, env)
        return dict(result)
    if provider == PROVIDER_OPENAI:
        result = _call_openai_full_user_day_note(model, prompt, timeout, env)
    elif provider == PROVIDER_DIRECT_OLLAMA:
        result = _call_direct_ollama_full_user_day_note(model, prompt, timeout, env)
    else:
        raise DailyCoachFullUserDayFreeRangeError(f"unsupported_provider:{provider}")
    return result.to_dict()


def _fully_free_prompt_variants() -> dict[str, FullyFreePromptVariant]:
    return {
        "fully_free_minimal": FullyFreePromptVariant(
            "fully_free_minimal",
            "Fully free minimal",
            "Source data plus minimal safety instructions only.",
            "Use the source data and minimal safety instructions only.",
        ),
        "fully_free_human_coach": FullyFreePromptVariant(
            "fully_free_human_coach",
            "Fully free human coach",
            "Natural human coach note with no imposed structure.",
            "Write like a natural human coach. Do not force a template.",
        ),
        "fully_free_direct": FullyFreePromptVariant(
            "fully_free_direct",
            "Fully free direct",
            "Clear direct coaching with plain language.",
            "Be clear and direct. Use plain language and useful specifics.",
        ),
        "fully_free_energy": FullyFreePromptVariant(
            "fully_free_energy",
            "Fully free energy",
            "High-energy coaching without unsafe advice.",
            "Bring energy and motivation, but keep the advice safe and grounded.",
        ),
        "fully_free_story_style": FullyFreePromptVariant(
            "fully_free_story_style",
            "Fully free story style",
            "Flowing note that connects the user's day into a coherent message.",
            "Make the day feel connected: recovery, training, food, and next move.",
        ),
        "fully_free_no_structure": FullyFreePromptVariant(
            "fully_free_no_structure",
            "Fully free no structure",
            "The model can choose the structure completely.",
            "Choose the structure completely. Use no imposed sections unless they help.",
        ),
    }


def _default_fully_free_variant_order() -> tuple[str, ...]:
    return tuple(_fully_free_prompt_variants().keys())


def _resolve_fully_free_variant(variant_id: str) -> FullyFreePromptVariant:
    variants = _fully_free_prompt_variants()
    if variant_id not in variants:
        raise DailyCoachFullUserDayFreeRangeError(
            f"unknown_fully_free_variant:{variant_id}; valid={', '.join(variants)}"
        )
    return variants[variant_id]


def _configured_fully_free_provider(provider: str, env: Mapping[str, str]) -> str:
    explicit_provider = (provider or "").strip().lower()
    if explicit_provider:
        return explicit_provider
    return (
        (env.get(FULLY_FREE_PROVIDER_ENV) or DEFAULT_FULLY_FREE_PROVIDER)
        .strip()
        .lower()
    )


def _plain_recovery_source(recovery: Mapping[str, Any]) -> dict[str, Any]:
    return _drop_empty(
        {
            "readiness_note": recovery.get("readiness_interpretation"),
            "recovery_score": recovery.get("recovery_score_display")
            or recovery.get("recovery_score"),
            "sleep": recovery.get("avg_sleep_display") or recovery.get("avg_sleep"),
            "energy": recovery.get("avg_energy_display") or recovery.get("avg_energy"),
            "soreness": recovery.get("avg_soreness_display")
            or recovery.get("avg_soreness"),
            "trend_notes": _clean_list(
                [
                    recovery.get("sleep_trend"),
                    recovery.get("weight_trend_display"),
                    recovery.get("fatigue_risk_display"),
                ]
            ),
            "what_not_to_infer": recovery.get("what_not_to_infer"),
        }
    )


def _plain_training_source(training: Mapping[str, Any]) -> dict[str, Any]:
    set_rows = training.get("exercise_rows") or training.get("set_level_rows") or []
    return _drop_empty(
        {
            "session_name": training.get("user_facing_session_name")
            or training.get("scheduled_session_name"),
            "session_type": training.get("session_type")
            or training.get("training_type"),
            "session_intensity": _plain_label(training.get("session_intensity")),
            "session_name_source": training.get("session_name_source"),
            "training_note": training.get("training_summary_for_coach")
            or _training_note_from_fields(training),
            "set_level_workout_data": _clean_set_rows(set_rows),
            "set_level_workout_data_note": training.get("set_level_data_reason")
            or training.get("set_level_data_unavailable_reason"),
            "recent_training_note": training.get("recent_training_note"),
        }
    )


def _plain_nutrition_source(
    nutrition: Mapping[str, Any], payload: Mapping[str, Any]
) -> dict[str, Any]:
    macro_card = payload.get("macro_display_card") or nutrition.get(
        "macro_display_card"
    )
    macros = nutrition.get("macro_targets_actuals_deltas") or {}
    macro_lines = []
    for macro, row in macros.items():
        if not isinstance(row, Mapping):
            continue
        display = row.get("display") or row.get("display_phrase")
        if display:
            macro_lines.append(str(display))
        elif row.get("logged_display") and row.get("target_display"):
            macro_lines.append(
                f"{str(macro).title()}: {row['logged_display']} / {row['target_display']}"
            )
    return _drop_empty(
        {
            "logged_intake_note": nutrition.get("logged_intake_note")
            or "Nutrition details are based on what is logged so far.",
            "macro_display": macro_card or macro_lines,
            "food_log_note": nutrition.get("today_food_log_summary")
            or nutrition.get("last_usable_food_log_summary"),
            "plain_guidance_context": "Logged intake so far may be incomplete; if anything is missing, it should be logged before judging the full day.",
        }
    )


def _plain_food_and_snack_source(
    food_candidates: Sequence[Mapping[str, Any]],
    snack_candidates: Sequence[Mapping[str, Any]],
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    food_rows = []
    for food in food_candidates[:20]:
        row = _drop_empty(
            {
                "option": food.get("plain_name_for_user") or food.get("display_name"),
                "serving": food.get("serving_size"),
                "display": food.get("display_phrase"),
                "helps_with": _plain_label(food.get("helps_with")),
                "why_it_may_help": food.get("why_useful_today"),
            }
        )
        if row:
            food_rows.append(row)
    snack_rows = []
    for snack in snack_candidates[:12]:
        row = _drop_empty(
            {
                "option": snack.get("snack_name"),
                "foods": snack.get("foods_included"),
                "serving_notes": snack.get("serving_notes"),
                "display": _clean_snack_display(snack),
                "helps_with": snack.get("helps_with"),
            }
        )
        if row:
            snack_rows.append(row)
    return _drop_empty(
        {
            "food_options": food_rows,
            "snack_or_mini_meal_options": snack_rows,
            "food_option_card": payload.get("food_option_card"),
            "note": "Meal-option numbers are estimates; introduce that once if useful rather than hedging every number.",
        }
    )


def _plain_body_metrics_source(payload: Mapping[str, Any]) -> dict[str, Any]:
    recovery = payload.get("recovery") or {}
    body = payload.get("user_profile") or {}
    weight_note = recovery.get("weight_trend_handling") or recovery.get(
        "weight_trend_display"
    )
    return _drop_empty(
        {
            "latest_body_weight": body.get("latest_body_weight_display")
            or body.get("latest_body_weight"),
            "goal_weight": body.get("goal_weight_display") or body.get("goal_weight"),
            "weight_trend_note": weight_note,
            "weight_trend_surface_to_coach": recovery.get(
                "weight_trend_surface_to_coach"
            ),
        }
    )


def _plain_recent_history_source(
    training: Mapping[str, Any], recovery: Mapping[str, Any]
) -> dict[str, Any]:
    return _drop_empty(
        {
            "training_recent_history": training.get("recent_workouts_summary")
            or training.get("recent_training_note"),
            "recovery_recent_history": recovery.get("recent_recovery_summary")
            or recovery.get("readiness_interpretation"),
        }
    )


def _available_unknowns(payload: Mapping[str, Any]) -> list[str]:
    unknowns = list(payload.get("do_not_infer") or [])
    training = payload.get("training") or {}
    if not training.get("set_level_data_available"):
        reason = (
            training.get("set_level_data_unavailable_reason")
            or "not available in this path"
        )
        unknowns.append(f"Actual set-level workout data: {reason}.")
    if not (payload.get("food_candidates") or []):
        unknowns.append("Food options were not available in this scenario.")
    return _clean_list(unknowns)


def _strip_backend_labels(value: Any) -> Any:
    if isinstance(value, Mapping):
        clean = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_debug_only_key(key_text):
                continue
            clean[key_text] = _strip_backend_labels(item)
        return clean
    if isinstance(value, list | tuple):
        return [_strip_backend_labels(item) for item in value]
    if isinstance(value, str):
        return _clean_backend_phrase(value)
    return value


def _clean_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    clean = {}
    for key, item in value.items():
        if _is_debug_only_key(str(key)):
            continue
        if isinstance(item, Mapping):
            item = _clean_mapping(item)
        elif isinstance(item, list | tuple):
            item = [
                _clean_mapping(row) if isinstance(row, Mapping) else row for row in item
            ]
        clean[str(key)] = item
    return _drop_empty(clean)


def _is_debug_only_key(key: str) -> bool:
    lowered = key.lower()
    return any(pattern in lowered for pattern in DEBUG_ONLY_KEYS)


def _clean_backend_phrase(value: str) -> str:
    replacements = {
        "protein gap": "protein still needed",
        "macro gap": "macros still below the target range",
        "confidence": "data quality",
        "volume_load": "recent training workload",
        "volume load": "recent training workload",
        "Progressing": "moving forward",
        "Rapid Increase": "large recent change",
        "training load": "training workload",
    }
    output = value
    for old, new in replacements.items():
        output = re.sub(re.escape(old), new, output, flags=re.IGNORECASE)
    return output


def _clean_snack_display(snack: Mapping[str, Any]) -> str | None:
    display = snack.get("display_phrase")
    if display:
        return str(display).replace("roughly 0g", "0g")
    name = snack.get("snack_name")
    if not name:
        return None
    calories = _display_number(snack.get("estimated_calories"), suffix=" calories")
    protein = _display_number(snack.get("estimated_protein_g"), suffix="g protein")
    pieces = [piece for piece in (protein, calories) if piece]
    return f"{name} — {', '.join(pieces)}" if pieces else str(name)


def _display_number(value: Any, *, suffix: str) -> str | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number.is_integer():
        return f"{int(number):,}{suffix}"
    return f"{round(number):,}{suffix}"


def _plain_label(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).replace("_", " ").strip().lower()
    return _clean_backend_phrase(text)


def _training_note_from_fields(training: Mapping[str, Any]) -> str | None:
    if training.get("scheduled_session_name"):
        return f"A training session is available: {training['scheduled_session_name']}."
    return None


def _clean_set_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list | tuple):
        return []
    clean_rows = []
    for row in rows[:20]:
        if not isinstance(row, Mapping):
            continue
        clean = _drop_empty(
            {
                "exercise": row.get("exercise_name") or row.get("exercise"),
                "target": row.get("target_display"),
                "actual": row.get("actual_display"),
                "result": _plain_label(row.get("set_result")),
                "progression_note": row.get("progression_signal_display")
                or row.get("progression_note"),
            }
        )
        if clean:
            clean_rows.append(clean)
    return clean_rows


def _drop_empty(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if value not in (None, "", [], {}, ())
    }


def _clean_list(values: Sequence[Any]) -> list[str]:
    return [
        _clean_backend_phrase(str(value))
        for value in values
        if value not in (None, "", [], {})
    ]


def _future_data_needs(packet: Mapping[str, Any]) -> list[str]:
    needs = []
    if not packet.get("training_source_data", {}).get("set_level_workout_data"):
        needs.append("richer actual set-level workout data")
    if not packet.get("recent_history_source_data"):
        needs.append("longer recent-history trend context")
    if not packet.get("food_and_snack_source_data", {}).get("food_options"):
        needs.append("broader curated food candidate coverage")
    return needs


def _call_provider_to_dict(result: Any) -> dict[str, Any]:
    if isinstance(result, Mapping):
        return dict(result)
    if hasattr(result, "to_dict"):
        return result.to_dict()
    return dict(asdict(result))


def _deterministic_fully_free_draft(
    source_packet: Mapping[str, Any], variant_id: str
) -> str:
    training = source_packet.get("training_source_data") or {}
    recovery = source_packet.get("recovery_source_data") or {}
    nutrition = source_packet.get("nutrition_source_data") or {}
    food = source_packet.get("food_and_snack_source_data") or {}
    session = training.get("session_name") or "today’s training"
    readiness = recovery.get("readiness_note") or "recovery data is available"
    food_options = (
        food.get("snack_or_mini_meal_options") or food.get("food_options") or []
    )
    food_line = ""
    if food_options:
        option = food_options[0]
        food_line = f" For food, start with {option.get('option') or option.get('display')} if that fits what you still need."
    if variant_id == "fully_free_energy":
        closer = " Bring the work, keep it clean, and make the next meal count."
    else:
        closer = " Keep it simple and log what actually happens."
    return (
        f"Today, use the strong signal in front of you: {readiness}. "
        f"Treat {session} as controlled work, not a max test. "
        f"{nutrition.get('logged_intake_note', 'Use the food data that is logged so far.')}"
        f"{food_line}{closer}"
    ).strip()


def _runtime_metadata(
    prompt: str, provider_attempted: bool, **extra: Any
) -> dict[str, Any]:
    metadata = {
        "developer_only": True,
        "normal_today_unchanged": True,
        "provider_promotion": False,
        "prompt_character_count": len(prompt),
        "provider_attempted": provider_attempted,
        "raw_provider_envelope_persisted": False,
        "repair_or_fallback_before_first_pass": False,
    }
    metadata.update(extra)
    return metadata


def _completion_truncation_reasons(
    text: str,
    *,
    output_tokens: int | None,
    max_output_tokens: int | None,
    finish_reason: Any,
) -> list[str]:
    stripped = text.strip()
    reasons = []
    if not stripped:
        return ["empty_output"]
    if str(finish_reason or "").lower() in {
        "length",
        "max_tokens",
        "max_output_tokens",
    }:
        reasons.append("provider_finish_reason_length")
    if (
        output_tokens
        and max_output_tokens
        and output_tokens >= int(max_output_tokens * 0.95)
    ):
        reasons.append("output_tokens_near_cap")
    if stripped.endswith((",", ":", "-", "and", "or", "but")):
        reasons.append("ends_mid_thought")
    if stripped[-1] not in ".!?)]}\"'":
        reasons.append("no_terminal_punctuation")
    return reasons


def _fully_free_max_output_tokens(env: Mapping[str, str]) -> int:
    value = env.get(FULLY_FREE_MAX_OUTPUT_TOKENS_ENV)
    if value:
        try:
            return max(256, min(int(value), 4000))
        except ValueError:
            pass
    return 1800


def _optional_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _iter_variants(results: Sequence[FullyFreeRunResult]) -> list[FullyFreeDraftResult]:
    return [variant for result in results for variant in result.variants]


def _unique_source_packets(
    results: Sequence[FullyFreeRunResult],
) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    seen: set[str] = set()
    for variant in _iter_variants(results):
        packet = variant.source_data_packet
        if not packet:
            continue
        key = json.dumps(packet.get("today_context", {}), sort_keys=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        packets.append(dict(packet))
    return packets


def _source_packets(results: Sequence[FullyFreeRunResult]) -> dict[str, Any]:
    return {"records": _unique_source_packets(results)}


def _provider_payload_debug(results: Sequence[FullyFreeRunResult]) -> dict[str, Any]:
    records = []
    for variant in _iter_variants(results):
        records.append(
            {
                "scenario_id": variant.scenario_id,
                "variant_id": variant.variant_id,
                "repeat_index": variant.repeat_index,
                "provider": variant.provider,
                "model": variant.model,
                "prompt_character_count": len(variant.provider_input_prompt or ""),
                "source_packet_available": variant.source_data_packet is not None,
                "raw_provider_envelope_persisted": False,
                "secrets_persisted": False,
                "raw_db_rows_persisted": False,
            }
        )
    return {"records": records}


def _render_provider_input(results: Sequence[FullyFreeRunResult]) -> str:
    lines = ["# Provider Input Prompt", ""]
    for variant in _iter_variants(results):
        lines.extend(
            [
                f"## {variant.variant_id} / repeat {variant.repeat_index}",
                f"Provider/model: {variant.provider} / {variant.model}",
                "",
                variant.provider_input_prompt or "(missing prompt)",
                "",
            ]
        )
    return "\n".join(lines)


def _render_source_packets(results: Sequence[FullyFreeRunResult]) -> str:
    lines = ["# Fully Free Source Data Packet", ""]
    for packet in _unique_source_packets(results):
        lines.append(_render_single_source_packet(packet))
    return "\n".join(lines)


def _render_single_source_packet(packet: Mapping[str, Any]) -> str:
    lines = []
    for section, value in packet.items():
        lines.extend(
            [
                f"## {section}",
                "",
                "```json",
                json.dumps(value, indent=2, sort_keys=True, default=str),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def _render_first_pass_drafts(results: Sequence[FullyFreeRunResult]) -> str:
    lines = [
        "# First-Pass Draft Capture",
        "",
        "Exact returned coach-note text. No repair, fallback, reviewer, renderer, or mutation is applied before capture.",
        "",
    ]
    for result in results:
        lines.append(f"## {result.scenario_id}")
        for variant in result.variants:
            lines.extend(
                [
                    f"### {variant.variant_id} / repeat {variant.repeat_index}",
                    f"Skipped: {variant.skipped}",
                    f"Skip reason: {variant.skip_reason or 'none'}",
                    "",
                    variant.first_pass_draft or "(no draft)",
                    "",
                ]
            )
    return "\n".join(lines)


def _render_side_by_side(results: Sequence[FullyFreeRunResult]) -> str:
    lines = ["# Side-by-Side Comparison", ""]
    for variant in _iter_variants(results):
        preview = (variant.first_pass_draft or "(no draft)").replace("\n", " ")[:300]
        lines.append(f"- {variant.variant_id} repeat {variant.repeat_index}: {preview}")
    return "\n".join(lines)


def _render_best_variant(results: Sequence[FullyFreeRunResult]) -> str:
    candidates = [variant for variant in _iter_variants(results) if not variant.skipped]
    best = max(candidates, key=lambda item: len(item.first_pass_draft), default=None)
    if not best:
        return "# Best Variant Summary\n\nNo captured draft."
    return "\n".join(
        [
            "# Best Variant Summary",
            "",
            f"Best heuristic variant: {best.variant_id}",
            f"Repeat: {best.repeat_index}",
            "Reason: longest captured deterministic/provider draft; QA should review content quality manually.",
            "",
            best.first_pass_draft,
        ]
    )


def _render_claim_risk(results: Sequence[FullyFreeRunResult]) -> str:
    lines = ["# Claim Risk Summary", ""]
    for variant in _iter_variants(results):
        findings = scan_full_user_day_claim_risk(variant.first_pass_draft or "")
        lines.append(
            f"- {variant.variant_id} repeat {variant.repeat_index}: {findings or 'none'}"
        )
    return "\n".join(lines)


def _render_consistency(results: Sequence[FullyFreeRunResult]) -> str:
    diagnostics = build_completion_diagnostics(results)["summary"]
    return "\n".join(
        [
            "# Consistency Summary",
            "",
            f"Expected drafts: {diagnostics['expected_drafts']}",
            f"Captured drafts: {diagnostics['captured_drafts']}",
            f"Skipped drafts: {diagnostics['skipped_drafts']}",
            "Manual QA should compare voice, usefulness, and source-data use across repeats.",
        ]
    )


def _render_token_cost(results: Sequence[FullyFreeRunResult]) -> str:
    lines = ["# Token/Cost Telemetry", ""]
    for variant in _iter_variants(results):
        metadata = variant.runtime_metadata
        lines.append(
            f"- {variant.variant_id} repeat {variant.repeat_index}: input={metadata.get('input_tokens')}; output={metadata.get('output_tokens')}; total={metadata.get('total_tokens')}; cost={metadata.get('estimated_cost_usd')}; basis={metadata.get('cost_estimate_basis')}"
        )
    return "\n".join(lines)


def _write_token_cost_csv(path: Path, results: Sequence[FullyFreeRunResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_id",
                "variant_id",
                "repeat_index",
                "provider",
                "model",
                "input_tokens",
                "output_tokens",
                "total_tokens",
                "estimated_cost_usd",
                "cost_estimate_basis",
            ],
        )
        writer.writeheader()
        for variant in _iter_variants(results):
            metadata = variant.runtime_metadata
            writer.writerow(
                {
                    "scenario_id": variant.scenario_id,
                    "variant_id": variant.variant_id,
                    "repeat_index": variant.repeat_index,
                    "provider": variant.provider,
                    "model": variant.model,
                    "input_tokens": metadata.get("input_tokens"),
                    "output_tokens": metadata.get("output_tokens"),
                    "total_tokens": metadata.get("total_tokens"),
                    "estimated_cost_usd": metadata.get("estimated_cost_usd"),
                    "cost_estimate_basis": metadata.get("cost_estimate_basis"),
                }
            )


def _render_artifact_safety() -> str:
    return "\n".join(
        [
            "# Artifact Safety Summary",
            "",
            "- Developer-only lab artifacts.",
            "- No API keys or secrets are intentionally persisted.",
            "- Raw provider envelopes are not persisted.",
            "- Raw DB rows are not persisted in provider artifacts.",
            "- First-pass drafts are captured exactly before diagnostics.",
            "- Normal Today behavior is unchanged.",
        ]
    )


def _render_source_data_completeness(results: Sequence[FullyFreeRunResult]) -> str:
    summary = build_source_data_completeness_summary(results)
    lines = ["# Source Data Completeness Summary", ""]
    for record in summary["records"]:
        lines.extend(
            [
                f"## {record.get('scenario_id')}",
                f"User context received: {record['user_context_received']}",
                f"Recovery details received: {record['recovery_details_received']}",
                f"Training details received: {record['training_details_received']}",
                f"Set-level workout data received: {record['set_level_workout_data_received']}",
                f"Nutrition logs received: {record['nutrition_logs_received']}",
                f"Macro targets received: {record['macro_targets_received']}",
                f"Food options received: {record['food_options_received']}",
                f"Snack options received: {record['snack_options_received']}",
                f"Recent history received: {record['recent_history_received']}",
                f"Future data needs: {record['future_data_needs'] or 'none'}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_model_freedom(results: Sequence[FullyFreeRunResult]) -> str:
    lines = ["# Model Freedom Summary", ""]
    for record in build_model_freedom_summaries(results)["records"]:
        lines.extend(
            [
                f"## {record['variant_id']} / repeat {record['repeat_index']}",
                f"Prompt length: {record['prompt_length']}",
                f"Explicit style constraints: {record['explicit_style_constraints']}",
                f"Safety constraints: {record['safety_constraints']}",
                f"Examples included: {record['examples_included']}",
                f"Deterministic coach prose included: {record['deterministic_coach_prose_included']}",
                f"Renderer structure included: {record['renderer_structure_included']}",
                f"Phrase bans included: {record['phrase_bans_included']}",
                f"Output structure forced: {record['output_structure_forced']}",
                f"Model can choose what matters: {record['model_can_choose_what_matters']}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_backend_prose_contamination(results: Sequence[FullyFreeRunResult]) -> str:
    summary = build_backend_prose_contamination_summary(results)
    lines = ["# Backend Prose Contamination Summary", ""]
    lines.append("Audit only. Findings do not mutate first-pass drafts.")
    lines.append("")
    for record in summary["records"]:
        lines.extend(
            [
                f"## {record['variant_id']} / repeat {record['repeat_index']}",
                f"Provider prompt findings: {record['provider_prompt_findings'] or 'none'}",
                f"Source packet findings: {record['source_packet_findings'] or 'none'}",
                f"First-pass findings: {record['first_pass_findings'] or 'none'}",
                f"Mutated first pass: {record['mutated_first_pass']}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_completion_diagnostics(results: Sequence[FullyFreeRunResult]) -> str:
    diagnostics = build_completion_diagnostics(results)
    summary = diagnostics["summary"]
    lines = [
        "# Completion Diagnostics",
        "",
        f"Expected drafts: {summary['expected_drafts']}",
        f"Captured drafts: {summary['captured_drafts']}",
        f"Complete drafts: {summary['complete_drafts']}",
        f"Truncated drafts: {summary['truncated_drafts']}",
        f"Skipped drafts: {summary['skipped_drafts']}",
        "",
    ]
    for record in diagnostics["records"]:
        lines.append(
            f"- {record['variant_id']} repeat {record['repeat_index']}: skipped={record['skipped']}; captured={record['captured']}; truncated={record['truncated']}; finish_reason={record['finish_reason']}; status={record['completion_status']}; reasons={record['truncation_heuristics']}"
        )
    return "\n".join(lines)


def _render_v4_comparison() -> str:
    return "\n".join(
        [
            "# v4 vs Fully Free Comparison",
            "",
            "This lab does not rerun v4. It compares design intent against the v4 diagnostic baseline.",
            "",
            "- v4: decaged but still model-facing coach facts.",
            "- Fully free lab: clean source data plus minimal prompt.",
            "- v4: direct/hypeman emphasis available.",
            "- Fully free lab: broader source-data ceiling variants.",
            "- Both: first-pass capture before diagnostics; OpenAI opt-in only; normal Today unchanged.",
        ]
    )


def _render_variant_quality_notes(results: Sequence[FullyFreeRunResult]) -> str:
    lines = ["# Variant Quality Notes", ""]
    for variant in _fully_free_prompt_variants().values():
        lines.append(f"- {variant.variant_id}: {variant.description}")
    lines.append("")
    lines.append(
        "Manual QA should judge naturalness, specificity, food usefulness, training usefulness, recovery use, and claim risk."
    )
    return "\n".join(lines)


def _render_source_data_missing_for_future_agents(
    results: Sequence[FullyFreeRunResult],
) -> str:
    lines = ["# Source Data Missing for Future Agents", ""]
    for record in build_source_data_completeness_summary(results)["records"]:
        lines.append(f"## {record.get('scenario_id')}")
        for need in record.get("future_data_needs") or []:
            lines.append(f"- {need}")
        if not record.get("future_data_needs"):
            lines.append("- none flagged by this lab")
        lines.append("")
    return "\n".join(lines)


def _render_pasteback_report(results: Sequence[FullyFreeRunResult]) -> str:
    completion = build_completion_diagnostics(results)["summary"]
    freedom_records = build_model_freedom_summaries(results)["records"]
    contamination = build_backend_prose_contamination_summary(results)["records"]
    best = _render_best_variant(results)
    return "\n".join(
        [
            "# Fully Free Source-Data Lab Pasteback Report",
            "",
            "## Status",
            "Developer-only fully free source-data lab artifacts generated.",
            "",
            "## Completion",
            f"Expected/captured/complete/truncated/skipped: {completion['expected_drafts']} / {completion['captured_drafts']} / {completion['complete_drafts']} / {completion['truncated_drafts']} / {completion['skipped_drafts']}",
            "",
            "## Model Freedom",
            f"Phrase bans included: {all(not row['phrase_bans_included'] for row in freedom_records)}",
            f"Renderer structure omitted: {all(not row['renderer_structure_included'] for row in freedom_records)}",
            f"Model can choose what matters: {all(row['model_can_choose_what_matters'] for row in freedom_records)}",
            "",
            "## Backend Prose Contamination",
            f"Records audited: {len(contamination)}",
            "Audit is post-hoc and does not mutate first-pass drafts.",
            "",
            "## Best Variant Snapshot",
            best,
            "",
            "## Known Baseline Drift",
            BASELINE_DRIFT["test_file"],
        ]
    )


def _contamination_findings(text: str) -> list[str]:
    lowered = text.lower()
    return [pattern for pattern in BACKEND_PROSE_PATTERNS if pattern.lower() in lowered]


def _build_run_id(provider: str, scenario_id: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"fully-free-{provider}-{scenario_id}-{stamp}"


def _skipped_setup_run(
    *,
    run_id: str,
    scenario_id: str,
    user_id: int,
    target_date: str,
    provider: str,
    model: str,
    variants: Sequence[str],
    repeat: int,
    reason: str,
) -> FullyFreeRunResult:
    draft_results = []
    for variant_id in variants:
        for repeat_index in range(1, repeat + 1):
            draft_results.append(
                FullyFreeDraftResult(
                    scenario_id=scenario_id,
                    user_id=user_id,
                    date=target_date,
                    provider=provider,
                    model=model,
                    variant_id=variant_id,
                    repeat_index=repeat_index,
                    skipped=True,
                    skip_reason=reason,
                    first_pass_draft="",
                    provider_input_prompt=None,
                    source_data_packet=None,
                    runtime_metadata={
                        "developer_only": True,
                        "normal_today_unchanged": True,
                        "provider_promotion": False,
                        "setup_failed": True,
                        "repair_or_fallback_before_first_pass": False,
                    },
                )
            )
    return FullyFreeRunResult(
        run_id=run_id,
        scenario_id=scenario_id,
        user_id=user_id,
        date=target_date,
        provider=provider,
        model=model,
        variants=tuple(draft_results),
        baseline_drift=dict(BASELINE_DRIFT),
        runtime_metadata={
            "milestone": "daily_coach_fully_free_source_data_lab_v1",
            "developer_only": True,
            "normal_today_unchanged": True,
            "provider_promotion": False,
            "setup_failure": reason,
        },
    )


def _safe_error(exc: Exception) -> str:
    return str(exc).replace("\n", " ")[:300]


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )


def _write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
