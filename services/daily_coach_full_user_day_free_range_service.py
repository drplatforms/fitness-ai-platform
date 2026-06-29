from __future__ import annotations

import csv
import json
import os
import re
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from models.daily_coach_full_user_day_models import (
    DailyCoachFullUserDayDraftResult,
    DailyCoachFullUserDayPacket,
    DailyCoachFullUserDayPromptVariant,
    DailyCoachFullUserDayProviderCallResult,
    DailyCoachFullUserDayTrialRunResult,
)
from models.daily_coach_natural_draft_audit_models import (
    AddressingPolicy,
    ApprovedCoachBrief,
)
from services.daily_coach_approved_brief_service import build_approved_coach_brief
from services.daily_coach_natural_draft_audit_service import (
    get_daily_coach_natural_draft_scenario,
    list_daily_coach_natural_draft_scenarios,
)
from services.daily_coach_synthesis_service import build_daily_coach_synthesis
from services.daily_coach_value_narrative_service import (
    DEFAULT_OLLAMA_BASE_URL,
    OLLAMA_BASE_URL_ENV,
    OPENAI_API_KEY_ENV,
    OPENAI_BASE_URL_ENV,
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
    build_daily_coach_value_aware_provider_context,
)
from services.user_state_service import build_user_health_state

DEFAULT_FULL_USER_DAY_OUTPUT_DIR = (
    "docs/provider_trials/daily_coach_full_user_day_free_range_payload_baseline_v1"
)
DEFAULT_FULL_USER_DAY_MODEL = "gpt-5.5"
DEFAULT_FULL_USER_DAY_PROVIDER = PROVIDER_DETERMINISTIC
FULL_USER_DAY_PROVIDER_ENV = "DAILY_COACH_FULL_USER_DAY_PROVIDER"
FULL_USER_DAY_MODEL_ENV = "DAILY_COACH_FULL_USER_DAY_MODEL"
FULL_USER_DAY_OPENAI_TIMEOUT_ENV = "DAILY_COACH_FULL_USER_DAY_OPENAI_TIMEOUT_SECONDS"
FULL_USER_DAY_DIRECT_OLLAMA_TIMEOUT_ENV = (
    "DAILY_COACH_FULL_USER_DAY_DIRECT_OLLAMA_TIMEOUT_SECONDS"
)
FULL_USER_DAY_INPUT_COST_PER_MILLION_ENV = (
    "DAILY_COACH_FULL_USER_DAY_INPUT_COST_PER_MILLION"
)
FULL_USER_DAY_OUTPUT_COST_PER_MILLION_ENV = (
    "DAILY_COACH_FULL_USER_DAY_OUTPUT_COST_PER_MILLION"
)
SUPPORTED_FULL_USER_DAY_PROVIDERS = (
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
)
SECRET_PATTERNS = ("bearer ", "openai_api_key", "api key", "sk-")
BASELINE_DRIFT = {
    "documented": True,
    "test_file": "tests/test_daily_narrative_rich_day_service.py",
    "example_test": "test_rich_day_summary_selects_fact_based_action",
    "example_expected": "Read the day before adding more",
    "example_actual": "Consider the full day",
    "architecture_decision": "document_do_not_block_free_range_trial",
    "patched_in_this_milestone": False,
}
APP_COPY_SCAN_PATTERNS: tuple[dict[str, str], ...] = (
    {"pattern": "approved option", "category": "backend_approval_language"},
    {"pattern": "approved protein option", "category": "backend_approval_language"},
    {"pattern": "approved food option", "category": "backend_approval_language"},
    {
        "pattern": "approved protein-focused food options",
        "category": "backend_approval_language",
    },
    {"pattern": "approved food suggestions", "category": "backend_approval_language"},
    {"pattern": "remaining protein gap", "category": "macro_gap_wording"},
    {"pattern": "protein gap", "category": "macro_gap_wording"},
    {"pattern": "green-light day", "category": "recovery_status_label"},
    {"pattern": "planned workout", "category": "training_app_prose"},
    {"pattern": "planned session", "category": "training_app_prose"},
    {"pattern": "current_narrow_path", "category": "old_path_reference"},
    {"pattern": "fallback", "category": "old_path_reference"},
)
CLAIM_RISK_PATTERNS: tuple[dict[str, str], ...] = (
    {"pattern": "diagnosed", "category": "medical_claim_risk"},
    {"pattern": "injury", "category": "medical_claim_risk"},
    {"pattern": "overtraining", "category": "unsupported_training_claim"},
    {"pattern": "fat loss stalled", "category": "unsupported_body_composition_claim"},
    {"pattern": "you ate", "category": "unsupported_food_completion_claim"},
    {"pattern": "you completed", "category": "unsupported_workout_completion_claim"},
)

FullUserDayProviderCallable = Callable[
    [str, str, float, Mapping[str, str]], DailyCoachFullUserDayProviderCallResult
]


class DailyCoachFullUserDayFreeRangeError(ValueError):
    """Raised when the full-user-day free-range trial cannot proceed safely."""


def list_daily_coach_full_user_day_scenarios() -> list[dict[str, Any]]:
    return list_daily_coach_natural_draft_scenarios()


def list_daily_coach_full_user_day_prompt_variants() -> list[dict[str, Any]]:
    return [variant.to_dict() for variant in _prompt_variants().values()]


def scan_full_user_day_app_copy(text: str) -> list[dict[str, str]]:
    lowered = text.lower()
    return [
        rule for rule in APP_COPY_SCAN_PATTERNS if rule["pattern"].lower() in lowered
    ]


def scan_full_user_day_claim_risk(text: str) -> list[dict[str, str]]:
    lowered = text.lower()
    return [rule for rule in CLAIM_RISK_PATTERNS if rule["pattern"].lower() in lowered]


def build_daily_coach_full_user_day_packet(
    *,
    user_id: int,
    target_date: str,
    scenario_id: str,
    synthesis: Any | None = None,
    health_state: Any | None = None,
    value_context: Mapping[str, Any] | None = None,
    brief: ApprovedCoachBrief | None = None,
    food_candidate_limit: int = 15,
) -> DailyCoachFullUserDayPacket:
    """Build a neutral structured user-day packet for free-range provider trials.

    This packet intentionally avoids app-written Daily Coach prose and deterministic
    coach copy. It gives the provider facts, calculations, uncertainty, and food
    choices as data so Architecture can see the true GPT-5.5 first-pass ceiling.
    """

    resolved_synthesis = synthesis or build_daily_coach_synthesis(user_id)
    resolved_health_state = health_state or build_user_health_state(user_id)
    resolved_value_context = dict(
        value_context
        or build_daily_coach_value_aware_provider_context(
            user_id=user_id,
            narrative_date=target_date,
            synthesis=resolved_synthesis,
            health_state=resolved_health_state,
        )
    )
    resolved_brief = brief or build_approved_coach_brief(
        user_id=user_id,
        target_date=target_date,
        scenario_id=scenario_id,
        synthesis=resolved_synthesis,
        value_context=resolved_value_context,
        addressing_policy=AddressingPolicy(),
    )
    nutrition = _nutrition_payload(resolved_value_context, resolved_health_state)
    training = _training_payload(resolved_health_state, resolved_synthesis)
    recovery = _recovery_payload(resolved_health_state)
    health_projection, health_coverage = _user_health_state_projection(
        resolved_health_state
    )
    packet = DailyCoachFullUserDayPacket(
        packet_version="daily_coach_full_user_day_free_range_payload_baseline_v1",
        user_id=user_id,
        date=target_date,
        scenario_id=scenario_id,
        user_profile=_user_profile(resolved_health_state),
        today_context={
            "date": target_date,
            "scenario_id": scenario_id,
            "available_data": _available_data(nutrition, training, recovery),
            "missing_data": _missing_data(nutrition, training, recovery),
            "logging_completeness": nutrition.get("logging_completeness"),
            "uncertainty_flags": _uncertainty_flags(nutrition, training, recovery),
        },
        user_health_state_projection=health_projection,
        user_health_state_field_coverage=health_coverage,
        nutrition=nutrition,
        food_candidates=tuple(
            _food_candidates(
                resolved_brief,
                resolved_value_context,
                limit=max(1, min(food_candidate_limit, 15)),
            )
        ),
        training=training,
        recovery=recovery,
        deterministic_calculations={
            "macro_targets_actuals_deltas": nutrition.get(
                "macro_targets_actuals_deltas", {}
            ),
            "nutrition_priority": nutrition.get("priority"),
            "training_suitability": training.get("training_suitability"),
            "readiness_interpretation": recovery.get("readiness_interpretation"),
            "logging_limitation": nutrition.get("limitations"),
        },
        do_not_infer=(
            "Do not assume food was eaten unless it is logged.",
            "Do not assume the workout was completed unless it is logged.",
            "Do not invent foods, amounts, targets, exercise details, causes, diagnoses, injuries, medical advice, or body-composition claims.",
            "Do not turn app labels or system workflow language into user-facing language.",
        ),
        context_sources=(
            "DailyCoachSynthesis identifiers and non-prose reason/limitation fields",
            "UserHealthState structured projection",
            "DailyCoachValueAwareProviderContext nutrition calculations",
            "ApprovedCoachBrief food/training/recovery facts projected as neutral data",
        ),
    )
    _assert_packet_sanitized(packet)
    return packet


def build_full_user_day_free_range_prompt(
    packet: DailyCoachFullUserDayPacket,
    variant_id: str,
) -> str:
    variant = _resolve_variant(variant_id)
    packet_json = json.dumps(packet.to_dict(), indent=2, sort_keys=True, default=str)
    prompt = (
        f"{variant.writer_instruction}\n\n"
        "Use the data packet below.\n"
        "Sound like a practical human coach.\n"
        "Use specific training, nutrition, recovery, and food details when they help.\n"
        "If data is missing or uncertain, say that naturally.\n"
        "Do not invent facts.\n"
        "Return only the coach note.\n\n"
        "DATA_PACKET_JSON:\n"
        f"{packet_json}\n"
    )
    _assert_text_sanitized(prompt, label="full user-day provider input prompt")
    return prompt


def run_daily_coach_full_user_day_free_range_scenario(
    *,
    scenario_id: str,
    provider: str = DEFAULT_FULL_USER_DAY_PROVIDER,
    model: str | None = None,
    variants: Sequence[str] | None = None,
    repeat: int = 1,
    allow_live_provider: bool = False,
    output_dir: Path | None = None,
    write_provider_payload_debug: bool = False,
    environ: Mapping[str, str] | None = None,
    provider_generate: FullUserDayProviderCallable | None = None,
) -> DailyCoachFullUserDayTrialRunResult:
    scenario = get_daily_coach_natural_draft_scenario(scenario_id)
    env = dict(os.environ if environ is None else environ)
    resolved_provider = _configured_provider(provider, env)
    if resolved_provider not in SUPPORTED_FULL_USER_DAY_PROVIDERS:
        resolved_provider = PROVIDER_DETERMINISTIC
    resolved_model = (
        model or env.get(FULL_USER_DAY_MODEL_ENV) or DEFAULT_FULL_USER_DAY_MODEL
    )
    selected_variants = tuple(variants or _default_variant_order())
    resolved_repeat = max(1, min(int(repeat or 1), 10))
    run_id = _build_run_id(resolved_provider, scenario_id)
    user_id = int(scenario["user_id"])
    target_date = str(scenario["target_date"])
    try:
        packet = build_daily_coach_full_user_day_packet(
            user_id=user_id,
            target_date=target_date,
            scenario_id=scenario_id,
        )
    except Exception as exc:  # noqa: BLE001 - developer diagnostic captures setup failures safely
        result = _skipped_setup_run(
            run_id=run_id,
            scenario_id=scenario_id,
            user_id=user_id,
            target_date=target_date,
            provider=resolved_provider,
            model=resolved_model,
            variants=selected_variants,
            repeat=resolved_repeat,
            reason=f"full_user_day_packet_build_failed:{_safe_error(exc)}",
        )
        if output_dir:
            write_daily_coach_full_user_day_artifacts(
                output_dir,
                [result],
                write_provider_payload_debug=write_provider_payload_debug,
            )
        return result
    draft_results: list[DailyCoachFullUserDayDraftResult] = []
    for repeat_index in range(1, resolved_repeat + 1):
        for variant_id in selected_variants:
            draft_results.append(
                _run_variant(
                    packet=packet,
                    variant_id=variant_id,
                    repeat_index=repeat_index,
                    provider=resolved_provider,
                    model=resolved_model,
                    allow_live_provider=allow_live_provider,
                    environ=env,
                    provider_generate=provider_generate,
                )
            )
    result = DailyCoachFullUserDayTrialRunResult(
        run_id=run_id,
        scenario_id=scenario_id,
        user_id=user_id,
        date=target_date,
        provider=resolved_provider,  # type: ignore[arg-type]
        model=resolved_model,
        variants=tuple(draft_results),
        baseline_drift=dict(BASELINE_DRIFT),
        runtime_metadata={
            "developer_only": True,
            "normal_today_unchanged": True,
            "free_range_payload_baseline_only": True,
            "provider_promotion": False,
            "raw_provider_envelope_persisted": False,
            "repair_or_fallback_before_first_pass": False,
            "repeat": resolved_repeat,
            "provider_payload_debug_available": write_provider_payload_debug,
        },
    )
    _assert_run_sanitized(result)
    if output_dir:
        write_daily_coach_full_user_day_artifacts(
            output_dir,
            [result],
            write_provider_payload_debug=write_provider_payload_debug,
        )
    return result


def run_daily_coach_full_user_day_free_range_matrix(
    *,
    scenarios: Sequence[str],
    provider: str = DEFAULT_FULL_USER_DAY_PROVIDER,
    model: str | None = None,
    variants: Sequence[str] | None = None,
    repeat: int = 1,
    allow_live_provider: bool = False,
    output_dir: Path,
    write_provider_payload_debug: bool = False,
    environ: Mapping[str, str] | None = None,
    provider_generate: FullUserDayProviderCallable | None = None,
) -> list[DailyCoachFullUserDayTrialRunResult]:
    selected_scenarios = list(scenarios) or ["rich_nutrition_training_recovery"]
    results = [
        run_daily_coach_full_user_day_free_range_scenario(
            scenario_id=scenario_id,
            provider=provider,
            model=model,
            variants=variants,
            repeat=repeat,
            allow_live_provider=allow_live_provider,
            environ=environ,
            provider_generate=provider_generate,
            write_provider_payload_debug=write_provider_payload_debug,
        )
        for scenario_id in selected_scenarios
    ]
    write_daily_coach_full_user_day_artifacts(
        output_dir,
        results,
        write_provider_payload_debug=write_provider_payload_debug,
    )
    return results


def write_daily_coach_full_user_day_artifacts(
    output_dir: Path,
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
    *,
    write_provider_payload_debug: bool = False,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_config = {
        "milestone": "daily_coach_full_user_day_free_range_payload_baseline_v1",
        "developer_only": True,
        "normal_today_unchanged": True,
        "run_count": len(results),
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "write_provider_payload_debug": write_provider_payload_debug,
        "baseline_drift": dict(BASELINE_DRIFT),
    }
    _write_json(output_dir / "run_config.json", run_config)
    _write_json(output_dir / "full_user_day_packet.json", _packet_summaries(results))
    (output_dir / "full_user_day_packet_summary.md").write_text(
        _render_packet_summary(results), encoding="utf-8"
    )
    (output_dir / "prompt_variants.md").write_text(
        _render_prompt_variants(), encoding="utf-8"
    )
    (output_dir / "first_pass_drafts.md").write_text(
        _render_first_pass_drafts(results), encoding="utf-8"
    )
    (output_dir / "first_pass_drafts_compact.md").write_text(
        _render_first_pass_drafts_compact(results), encoding="utf-8"
    )
    (output_dir / "side_by_side_comparison.md").write_text(
        _render_side_by_side_comparison(results), encoding="utf-8"
    )
    (output_dir / "best_variant_summary.md").write_text(
        _render_best_variant_summary(results), encoding="utf-8"
    )
    (output_dir / "product_language_findings.md").write_text(
        _render_product_language_findings(results), encoding="utf-8"
    )
    (output_dir / "claim_risk_summary.md").write_text(
        _render_claim_risk_summary(results), encoding="utf-8"
    )
    (output_dir / "consistency_summary.md").write_text(
        _render_consistency_summary(results), encoding="utf-8"
    )
    (output_dir / "token_cost_telemetry.md").write_text(
        _render_token_cost_telemetry(results), encoding="utf-8"
    )
    _write_telemetry_csv(output_dir / "token_cost_telemetry.csv", results)
    (output_dir / "artifact_safety_summary.md").write_text(
        _render_artifact_safety_summary(results, write_provider_payload_debug),
        encoding="utf-8",
    )
    (output_dir / "pasteback_report.md").write_text(
        _render_pasteback_report(results, write_provider_payload_debug),
        encoding="utf-8",
    )
    if write_provider_payload_debug:
        (output_dir / "provider_input_prompt.md").write_text(
            _render_provider_input_prompt_debug(results), encoding="utf-8"
        )
        _write_json(output_dir / "provider_payload_debug.json", _payload_debug(results))
    serialized = "\n".join(
        path.read_text(encoding="utf-8")
        for path in output_dir.iterdir()
        if path.is_file()
    )
    _assert_text_sanitized(serialized, label="full user-day artifacts")


def _run_variant(
    *,
    packet: DailyCoachFullUserDayPacket,
    variant_id: str,
    repeat_index: int,
    provider: str,
    model: str,
    allow_live_provider: bool,
    environ: Mapping[str, str],
    provider_generate: FullUserDayProviderCallable | None,
) -> DailyCoachFullUserDayDraftResult:
    variant = _resolve_variant(variant_id)
    prompt = build_full_user_day_free_range_prompt(packet, variant.variant_id)
    if provider != PROVIDER_DETERMINISTIC and not allow_live_provider:
        return DailyCoachFullUserDayDraftResult(
            scenario_id=packet.scenario_id,
            user_id=packet.user_id,
            date=packet.date,
            provider=provider,  # type: ignore[arg-type]
            model=model,
            variant_id=variant.variant_id,
            repeat_index=repeat_index,
            skipped=True,
            skip_reason="live_provider_not_allowed",
            first_pass_draft="",
            provider_input_prompt=prompt,
            full_user_day_packet=packet,
            runtime_metadata={
                "developer_only": True,
                "normal_today_unchanged": True,
                "prompt_character_count": len(prompt),
                "provider_attempted": False,
                "repair_or_fallback_before_first_pass": False,
            },
        )
    if provider == PROVIDER_DETERMINISTIC:
        call_result = DailyCoachFullUserDayProviderCallResult(
            raw_text=_deterministic_free_range_draft(packet, variant.variant_id),
            cost_estimate_basis="deterministic_no_provider_cost",
        )
    else:
        generate = provider_generate or _provider_generate(provider)
        try:
            call_result = generate(
                model, prompt, _timeout_seconds(provider, environ), environ
            )
        except Exception as exc:  # noqa: BLE001 - developer trial captures provider failure safely
            return DailyCoachFullUserDayDraftResult(
                scenario_id=packet.scenario_id,
                user_id=packet.user_id,
                date=packet.date,
                provider=provider,  # type: ignore[arg-type]
                model=model,
                variant_id=variant.variant_id,
                repeat_index=repeat_index,
                skipped=True,
                skip_reason=_safe_error(exc),
                first_pass_draft="",
                provider_input_prompt=prompt,
                full_user_day_packet=packet,
                runtime_metadata={
                    "developer_only": True,
                    "normal_today_unchanged": True,
                    "prompt_character_count": len(prompt),
                    "provider_attempted": True,
                    "provider_error": _safe_error(exc),
                    "repair_or_fallback_before_first_pass": False,
                },
            )
    return DailyCoachFullUserDayDraftResult(
        scenario_id=packet.scenario_id,
        user_id=packet.user_id,
        date=packet.date,
        provider=provider,  # type: ignore[arg-type]
        model=model,
        variant_id=variant.variant_id,
        repeat_index=repeat_index,
        skipped=False,
        skip_reason=None,
        first_pass_draft=call_result.raw_text.strip(),
        provider_input_prompt=prompt,
        full_user_day_packet=packet,
        runtime_metadata={
            "developer_only": True,
            "normal_today_unchanged": True,
            "prompt_character_count": len(prompt),
            "provider_attempted": provider != PROVIDER_DETERMINISTIC,
            "input_tokens": call_result.input_tokens,
            "output_tokens": call_result.output_tokens,
            "total_tokens": call_result.total_tokens,
            "cached_input_tokens": call_result.cached_input_tokens,
            "estimated_cost_usd": call_result.estimated_cost_usd,
            "cost_estimate_basis": call_result.cost_estimate_basis,
            "raw_output_length": len(call_result.raw_text),
            "raw_provider_envelope_persisted": False,
            "repair_or_fallback_before_first_pass": False,
        },
    )


def _skipped_setup_run(
    *,
    run_id: str,
    scenario_id: str,
    user_id: int,
    target_date: str,
    provider: str,
    model: str | None,
    variants: Sequence[str],
    repeat: int,
    reason: str,
) -> DailyCoachFullUserDayTrialRunResult:
    skipped = []
    for repeat_index in range(1, repeat + 1):
        for variant_id in variants:
            variant = _resolve_variant(variant_id)
            skipped.append(
                DailyCoachFullUserDayDraftResult(
                    scenario_id=scenario_id,
                    user_id=user_id,
                    date=target_date,
                    provider=provider,  # type: ignore[arg-type]
                    model=model,
                    variant_id=variant.variant_id,
                    repeat_index=repeat_index,
                    skipped=True,
                    skip_reason=reason,
                    first_pass_draft="",
                    provider_input_prompt=None,
                    full_user_day_packet=None,
                    runtime_metadata={
                        "developer_only": True,
                        "normal_today_unchanged": True,
                        "setup_failed": True,
                        "skip_reason": reason,
                    },
                )
            )
    return DailyCoachFullUserDayTrialRunResult(
        run_id=run_id,
        scenario_id=scenario_id,
        user_id=user_id,
        date=target_date,
        provider=provider,  # type: ignore[arg-type]
        model=model,
        variants=tuple(skipped),
        baseline_drift=dict(BASELINE_DRIFT),
        runtime_metadata={
            "developer_only": True,
            "normal_today_unchanged": True,
            "setup_failed": True,
            "skip_reason": reason,
        },
    )


def _nutrition_payload(
    value_context: Mapping[str, Any], health_state: Any
) -> dict[str, Any]:
    nutrition = (
        value_context.get("approved_nutrition")
        if isinstance(value_context, Mapping)
        else {}
    )
    nutrition = nutrition if isinstance(nutrition, Mapping) else {}
    health_nutrition = getattr(health_state, "nutrition_state", None)
    macro_status = _safe_mapping(nutrition.get("macro_status") or {})
    actuals = _safe_mapping(nutrition.get("actuals") or {})
    macro_targets: dict[str, Any] = {}
    for macro, comparison in macro_status.items():
        if not isinstance(comparison, Mapping):
            continue
        macro_targets[str(macro)] = _drop_unknowns(
            {
                "actual": comparison.get("actual"),
                "target_min": comparison.get("target_min"),
                "target_max": comparison.get("target_max"),
                "delta_min": comparison.get("delta_min"),
                "delta_max": comparison.get("delta_max"),
                "target_status": comparison.get("target_status"),
                "confidence": comparison.get("confidence"),
                "display_allowed": comparison.get("display_allowed"),
                "limitations": comparison.get("limitations"),
            }
        )
    return _drop_unknowns(
        {
            "available": nutrition.get("available"),
            "date": nutrition.get("date"),
            "logging_completeness": nutrition.get("logging_completeness"),
            "confidence": nutrition.get("confidence"),
            "actuals": actuals,
            "macro_targets_actuals_deltas": macro_targets,
            "calories": getattr(health_nutrition, "calories", None),
            "protein_grams": getattr(health_nutrition, "protein_grams", None),
            "carbohydrate_grams": getattr(health_nutrition, "carbohydrate_grams", None),
            "fat_grams": getattr(health_nutrition, "fat_grams", None),
            "protein_status": getattr(health_nutrition, "protein_status", None),
            "calorie_status": getattr(health_nutrition, "calorie_status", None),
            "recovery_nutrition_status": getattr(
                health_nutrition, "recovery_nutrition_status", None
            ),
            "limitations": nutrition.get("limitations"),
            "priority": _nutrition_priority(macro_targets),
        }
    )


def _food_candidates(
    brief: ApprovedCoachBrief,
    value_context: Mapping[str, Any],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(item: Mapping[str, Any]) -> None:
        plain_name = _plain_food_name(
            item.get("plain_name_for_user")
            or item.get("display_name")
            or item.get("friendly_name")
            or item.get("canonical_name")
            or ""
        )
        if not plain_name:
            return
        key = plain_name.lower()
        if key in seen:
            return
        seen.add(key)
        candidates.append(
            _drop_unknowns(
                {
                    "display_name": plain_name,
                    "plain_name_for_user": plain_name,
                    "serving_size": item.get("serving_size")
                    or item.get("serving_display")
                    or item.get("suggested_grams"),
                    "estimated_calories": item.get("estimated_calories"),
                    "estimated_protein_g": item.get("estimated_protein_g"),
                    "estimated_carbs_g": item.get("estimated_carbs_g")
                    or item.get("estimated_carbohydrate_g"),
                    "estimated_fat_g": item.get("estimated_fat_g"),
                    "why_useful_today": _food_reason(
                        item.get("why_useful_today")
                        or item.get("macro_reason")
                        or item.get("macro_gap_addressed")
                        or item.get("summary")
                    ),
                    "helps_with": _macro_label(
                        item.get("helps_with") or item.get("macro_gap_addressed")
                    ),
                    "source": item.get("source") or "nutrition_suggestion",
                    "confidence": item.get("confidence"),
                }
            )
        )

    nutrition = (
        value_context.get("approved_nutrition")
        if isinstance(value_context, Mapping)
        else {}
    )
    if isinstance(nutrition, Mapping):
        for suggestion in nutrition.get("approved_food_suggestions") or []:
            if isinstance(suggestion, Mapping):
                add(suggestion)
    for action in brief.approved_food_actions:
        add(
            {
                "friendly_name": action.friendly_name,
                "canonical_name": action.canonical_name,
                "macro_reason": action.macro_reason,
                "serving_display": (
                    action.serving_display if action.serving_allowed else None
                ),
                "source": "coach_brief_food_action",
                "confidence": "backend_selected",
            }
        )
    return candidates[:limit]


def _training_payload(health_state: Any, synthesis: Any) -> dict[str, Any]:
    training_state = getattr(health_state, "training_state", None)
    candidate_text = " ".join(
        str(getattr(synthesis, name, ""))
        for name in (
            "training_signal",
            "workout_guidance",
            "execution_context",
            "plan_fit_note",
        )
    )
    return _drop_unknowns(
        {
            "has_workout_data": getattr(training_state, "has_workout_data", None),
            "workout_count": getattr(training_state, "workout_count", None),
            "adherence_level": getattr(training_state, "adherence_level", None),
            "training_trend": getattr(training_state, "training_trend", None),
            "total_volume_load": getattr(training_state, "total_volume_load", None),
            "avg_rir": getattr(training_state, "avg_rir", None),
            "training_load": getattr(training_state, "training_load", None),
            "recovery_demand": getattr(training_state, "recovery_demand", None),
            "scheduled_session_name": _extract_session_name(candidate_text),
            "training_suitability": _training_suitability(health_state),
            "actual_set_logging_completeness": (
                "available"
                if getattr(training_state, "has_workout_data", None)
                else "unknown"
            ),
        }
    )


def _recovery_payload(health_state: Any) -> dict[str, Any]:
    recovery_state = getattr(health_state, "recovery_state", None)
    return _drop_unknowns(
        {
            "readiness_level": getattr(recovery_state, "readiness_level", None),
            "fatigue_risk": getattr(recovery_state, "fatigue_risk", None),
            "recovery_score": getattr(recovery_state, "recovery_score", None),
            "avg_sleep": getattr(recovery_state, "avg_sleep", None),
            "avg_energy": getattr(recovery_state, "avg_energy", None),
            "avg_soreness": getattr(recovery_state, "avg_soreness", None),
            "sleep_trend": getattr(recovery_state, "sleep_trend", None),
            "weight_trend": getattr(recovery_state, "weight_trend", None),
            "weight_change": getattr(recovery_state, "weight_change", None),
            "readiness_interpretation": _readiness_interpretation(recovery_state),
        }
    )


def _user_profile(health_state: Any) -> dict[str, Any]:
    return _drop_unknowns(
        {
            "user_id": getattr(health_state, "user_id", None),
            "primary_goal": getattr(health_state, "primary_goal", None),
            "age": getattr(health_state, "age", None),
            "height_cm": getattr(health_state, "height_cm", None),
            "starting_weight": getattr(health_state, "starting_weight", None),
            "latest_body_weight": getattr(health_state, "latest_body_weight", None),
            "goal_weight": getattr(health_state, "goal_weight", None),
            "activity_level": getattr(health_state, "activity_level", None),
        }
    )


def _user_health_state_projection(
    health_state: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = _object_to_dict(health_state)
    included: dict[str, Any] = {}
    omitted: dict[str, str] = {}
    for key, value in raw.items():
        if key == "user_name":
            omitted[key] = "name not needed for provider ceiling trial"
            continue
        if _looks_like_app_prose_key(key):
            omitted[key] = "app prose omitted; packet supplies structured facts instead"
            continue
        if isinstance(value, Mapping):
            child_included: dict[str, Any] = {}
            for child_key, child_value in value.items():
                dotted = f"{key}.{child_key}"
                if _looks_like_app_prose_key(str(child_key)):
                    omitted[dotted] = (
                        "app prose omitted; packet supplies structured facts instead"
                    )
                    continue
                if _safe_scalar_or_collection(child_value):
                    child_included[str(child_key)] = child_value
            if child_included:
                included[key] = child_included
        elif _safe_scalar_or_collection(value):
            included[key] = value
    return included, {
        "included_fields": _flatten_keys(included),
        "omitted_fields": omitted,
    }


def _object_to_dict(value: Any, *, depth: int = 0) -> dict[str, Any]:
    if depth > 4:
        return {}
    if is_dataclass(value):
        value = asdict(value)
    elif hasattr(value, "__dict__"):
        value = vars(value)
    if not isinstance(value, Mapping):
        return {}
    payload: dict[str, Any] = {}
    for key, item in value.items():
        key_text = str(key)
        if _unsafe_key(key_text):
            continue
        if is_dataclass(item) or hasattr(item, "__dict__") or isinstance(item, Mapping):
            payload[key_text] = _object_to_dict(item, depth=depth + 1)
        elif _safe_scalar_or_collection(item):
            payload[key_text] = item
    return payload


def _safe_mapping(value: Any, *, depth: int = 0) -> dict[str, Any]:
    if depth > 5 or not isinstance(value, Mapping):
        return {}
    safe: dict[str, Any] = {}
    for key, item in value.items():
        key_text = str(key)
        if _unsafe_key(key_text):
            continue
        if isinstance(item, Mapping):
            safe[key_text] = _safe_mapping(item, depth=depth + 1)
        elif isinstance(item, list | tuple):
            safe[key_text] = [
                (
                    _safe_mapping(child, depth=depth + 1)
                    if isinstance(child, Mapping)
                    else child
                )
                for child in item[:20]
                if _safe_scalar_or_collection(child)
            ]
        elif _safe_scalar_or_collection(item):
            safe[key_text] = item
    return safe


def _unsafe_key(key: str) -> bool:
    lowered = key.lower()
    return any(
        token in lowered
        for token in ("raw", "payload", "secret", "api_key", "token", "password")
    )


def _looks_like_app_prose_key(key: str) -> bool:
    lowered = key.lower()
    return any(
        token in lowered for token in ("summary", "focus", "guidance", "signal", "note")
    )


def _available_data(
    nutrition: Mapping[str, Any],
    training: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> list[str]:
    available: list[str] = []
    if nutrition.get("available") is True or nutrition.get(
        "macro_targets_actuals_deltas"
    ):
        available.append("nutrition")
    if training:
        available.append("training")
    if recovery:
        available.append("recovery")
    return available


def _missing_data(
    nutrition: Mapping[str, Any],
    training: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> list[str]:
    missing: list[str] = []
    if not nutrition or nutrition.get("available") is False:
        missing.append("complete_nutrition")
    if not training:
        missing.append("training_context")
    if not recovery:
        missing.append("recovery_context")
    return missing


def _uncertainty_flags(
    nutrition: Mapping[str, Any],
    training: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> list[str]:
    flags: list[str] = []
    if nutrition.get("logging_completeness") not in (None, "Complete", "complete"):
        flags.append("nutrition_logging_may_be_incomplete")
    if nutrition.get("confidence") not in (None, "High", "high"):
        flags.append("nutrition_confidence_limited")
    if not training.get("has_workout_data"):
        flags.append("workout_completion_not_assumed")
    if recovery.get("fatigue_risk") in ("High", "high"):
        flags.append("fatigue_risk_present")
    return flags


def _nutrition_priority(macro_targets: Mapping[str, Any]) -> str | None:
    for macro in ("protein_g", "calories", "calorie", "carbs_g", "fat_g"):
        item = macro_targets.get(macro)
        if isinstance(item, Mapping) and str(item.get("target_status", "")).lower() in {
            "below",
            "low",
            "short",
        }:
            return _macro_label(macro)
    return None


def _training_suitability(health_state: Any) -> str | None:
    recovery_state = getattr(health_state, "recovery_state", None)
    readiness = str(getattr(recovery_state, "readiness_level", "") or "").lower()
    fatigue = str(getattr(recovery_state, "fatigue_risk", "") or "").lower()
    if "high" in fatigue:
        return "train conservatively if training is still appropriate"
    if readiness in {"supportive", "good", "high", "strong"}:
        return "training appears supportable from available recovery facts"
    return None


def _readiness_interpretation(recovery_state: Any) -> str | None:
    if recovery_state is None:
        return None
    readiness = getattr(recovery_state, "readiness_level", None)
    fatigue = getattr(recovery_state, "fatigue_risk", None)
    if readiness and fatigue:
        return f"readiness={readiness}; fatigue_risk={fatigue}"
    if readiness:
        return f"readiness={readiness}"
    return None


def _extract_session_name(text: str) -> str | None:
    match = re.search(r"([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+){1,5} Session)", text)
    return match.group(1) if match else None


def _food_reason(value: Any) -> str | None:
    text = _macro_label(value)
    if text in (None, ""):
        return None
    replacements = {
        "protein_g": "protein is still short",
        "calories": "calories are still short",
        "calorie": "calories are still short",
        "carbs_g": "carbs may help if training fuel is short",
        "fat_g": "fat may help if calories are still short",
    }
    return replacements.get(str(value), text)


def _macro_label(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).replace("_g", "").replace("_", " ").strip()
    if text == "protein":
        return "protein"
    if text == "calorie":
        return "calories"
    return text


def _plain_food_name(value: Any) -> str:
    text = str(value or "").strip()
    replacements = (
        ("Tuna, Canned in Water", "canned tuna"),
        ("Chicken Breast, Cooked, Skinless", "cooked chicken breast"),
        ("Turkey Breast, Cooked", "turkey breast"),
        ("Greek Yogurt, Plain Nonfat", "Greek yogurt"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    text = text.replace("approved", "").replace("  ", " ").strip(" ,")
    return text


def _drop_unknowns(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if value not in (None, "", "Unknown", [], {})
    }


def _safe_scalar_or_collection(value: Any) -> bool:
    return value is None or isinstance(value, str | int | float | bool | list | tuple)


def _flatten_keys(value: Mapping[str, Any], prefix: str = "") -> list[str]:
    keys: list[str] = []
    for key, item in value.items():
        dotted = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, Mapping):
            keys.extend(_flatten_keys(item, dotted))
        else:
            keys.append(dotted)
    return keys


def _prompt_variants() -> dict[str, DailyCoachFullUserDayPromptVariant]:
    return {
        "free_range_full_user_day_minimal": DailyCoachFullUserDayPromptVariant(
            variant_id="free_range_full_user_day_minimal",
            label="Free-range full user-day minimal",
            purpose="Full useful user-day data packet with the shortest practical instruction.",
            writer_instruction="Write today’s Daily Coach note.",
        ),
        "free_range_full_user_day_practical_coach": DailyCoachFullUserDayPromptVariant(
            variant_id="free_range_full_user_day_practical_coach",
            label="Free-range full user-day practical coach",
            purpose="Full useful user-day data packet with practical human coach framing.",
            writer_instruction="Write today’s Daily Coach note like a practical human coach talking directly to the user.",
        ),
        "free_range_full_user_day_direct_coach": DailyCoachFullUserDayPromptVariant(
            variant_id="free_range_full_user_day_direct_coach",
            label="Free-range full user-day direct coach",
            purpose="Full useful user-day data packet with direct, no-fluff coaching framing.",
            writer_instruction="Write today’s Daily Coach note directly. Be useful, specific, and concise.",
        ),
    }


def _default_variant_order() -> tuple[str, ...]:
    return (
        "free_range_full_user_day_minimal",
        "free_range_full_user_day_practical_coach",
        "free_range_full_user_day_direct_coach",
    )


def _resolve_variant(variant_id: str) -> DailyCoachFullUserDayPromptVariant:
    variants = _prompt_variants()
    if variant_id not in variants:
        valid = ", ".join(variants)
        raise DailyCoachFullUserDayFreeRangeError(
            f"unknown_prompt_variant:{variant_id}; valid={valid}"
        )
    return variants[variant_id]


def _configured_provider(provider: str, env: Mapping[str, str]) -> str:
    return (env.get(FULL_USER_DAY_PROVIDER_ENV) or provider).strip().lower()


def _timeout_seconds(provider: str, env: Mapping[str, str]) -> float:
    key = (
        FULL_USER_DAY_OPENAI_TIMEOUT_ENV
        if provider == PROVIDER_OPENAI
        else FULL_USER_DAY_DIRECT_OLLAMA_TIMEOUT_ENV
    )
    value = env.get(key)
    if not value:
        return 60.0 if provider == PROVIDER_OPENAI else 120.0
    try:
        return max(1.0, float(value))
    except ValueError:
        return 60.0 if provider == PROVIDER_OPENAI else 120.0


def _provider_generate(provider: str) -> FullUserDayProviderCallable:
    if provider == PROVIDER_OPENAI:
        return _call_openai_full_user_day_note
    if provider == PROVIDER_DIRECT_OLLAMA:
        return _call_direct_ollama_full_user_day_note
    raise DailyCoachFullUserDayFreeRangeError(f"unsupported_provider:{provider}")


def _call_openai_full_user_day_note(
    model: str,
    prompt: str,
    timeout_seconds: float,
    env: Mapping[str, str],
) -> DailyCoachFullUserDayProviderCallResult:
    api_key = env.get(OPENAI_API_KEY_ENV)
    if not api_key:
        raise DailyCoachFullUserDayFreeRangeError("openai_missing_api_key")
    try:
        from openai import OpenAI

        client_kwargs: dict[str, Any] = {"api_key": api_key}
        base_url = env.get(OPENAI_BASE_URL_ENV)
        if base_url:
            client_kwargs["base_url"] = base_url.rstrip("/")
        client = OpenAI(**client_kwargs)
        response = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=900,
            timeout=timeout_seconds,
        )
    except Exception as exc:  # pragma: no cover - manual/live only
        raise DailyCoachFullUserDayFreeRangeError(
            f"openai_provider_error:{_safe_error(exc)}"
        ) from exc
    text = _extract_openai_text(response)
    if not text:
        raise DailyCoachFullUserDayFreeRangeError("openai_missing_response_text")
    usage = _extract_usage(response)
    return DailyCoachFullUserDayProviderCallResult(
        raw_text=text,
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
        total_tokens=usage.get("total_tokens"),
        cached_input_tokens=usage.get("cached_input_tokens"),
        estimated_cost_usd=_estimate_cost_usd(usage, env),
        cost_estimate_basis=_cost_estimate_basis(usage, env),
    )


def _call_direct_ollama_full_user_day_note(
    model: str,
    prompt: str,
    timeout_seconds: float,
    env: Mapping[str, str],
) -> DailyCoachFullUserDayProviderCallResult:
    base_url = (env.get(OLLAMA_BASE_URL_ENV) or DEFAULT_OLLAMA_BASE_URL).rstrip("/")
    payload = {
        "model": model.removeprefix("ollama/"),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.4},
    }
    request = urllib.request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        response_payload = json.loads(response.read().decode("utf-8"))
    text = str(response_payload.get("response") or "").strip()
    if not text:
        raise DailyCoachFullUserDayFreeRangeError("ollama_missing_response_text")
    return DailyCoachFullUserDayProviderCallResult(
        raw_text=text, cost_estimate_basis="ollama_local_no_cost"
    )


def _extract_openai_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text).strip()
    pieces: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                pieces.append(str(text))
    return "\n".join(pieces).strip()


def _extract_usage(response: Any) -> dict[str, int | None]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    input_tokens = getattr(usage, "input_tokens", None)
    output_tokens = getattr(usage, "output_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)
    details = getattr(usage, "input_tokens_details", None)
    cached = getattr(details, "cached_tokens", None) if details is not None else None
    return {
        "input_tokens": _optional_int(input_tokens),
        "output_tokens": _optional_int(output_tokens),
        "total_tokens": _optional_int(total_tokens)
        or _sum_optional_ints(input_tokens, output_tokens),
        "cached_input_tokens": _optional_int(cached),
    }


def _estimate_cost_usd(
    usage: Mapping[str, Any], env: Mapping[str, str]
) -> float | None:
    input_cost = _optional_float(env.get(FULL_USER_DAY_INPUT_COST_PER_MILLION_ENV))
    output_cost = _optional_float(env.get(FULL_USER_DAY_OUTPUT_COST_PER_MILLION_ENV))
    if input_cost is None or output_cost is None:
        return None
    input_tokens = _optional_int(usage.get("input_tokens")) or 0
    output_tokens = _optional_int(usage.get("output_tokens")) or 0
    return round(
        (input_tokens / 1_000_000 * input_cost)
        + (output_tokens / 1_000_000 * output_cost),
        6,
    )


def _cost_estimate_basis(
    usage: Mapping[str, Any], env: Mapping[str, str]
) -> str | None:
    if _estimate_cost_usd(usage, env) is None:
        return None
    return f"env:{FULL_USER_DAY_INPUT_COST_PER_MILLION_ENV}+{FULL_USER_DAY_OUTPUT_COST_PER_MILLION_ENV}"


def _optional_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_optional_ints(left: Any, right: Any) -> int | None:
    left_value = _optional_int(left)
    right_value = _optional_int(right)
    if left_value is None and right_value is None:
        return None
    return (left_value or 0) + (right_value or 0)


def _deterministic_free_range_draft(
    packet: DailyCoachFullUserDayPacket, variant_id: str
) -> str:
    protein_food = next(
        (
            food
            for food in packet.food_candidates
            if food.get("helps_with") == "protein"
        ),
        None,
    )
    food_line = ""
    if protein_food:
        food_line = (
            f" If protein is still short, eat {protein_food['plain_name_for_user']}."
        )
    training_line = "Keep today’s training controlled."
    if packet.training.get("scheduled_session_name"):
        training_line = f"Run today’s {packet.training['scheduled_session_name']} and keep the work controlled."
    recovery_line = (
        packet.recovery.get("readiness_interpretation")
        or "Use recovery data without over-reading it."
    )
    return (
        f"Today’s useful signal is simple: {training_line} {recovery_line}. "
        "Log what actually happens before making the next progression call."
        f"{food_line}"
    ).strip()


def _build_run_id(provider: str, scenario_id: str) -> str:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    safe_scenario = re.sub(r"[^a-zA-Z0-9_-]+", "_", scenario_id)
    return f"daily_coach_full_user_day_free_range_payload_baseline_v1_{safe_scenario}_{provider}_{timestamp.replace(':', '').replace('+', 'z')}"


def _packet_summaries(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    for run in results:
        for variant in run.variants:
            packet = variant.full_user_day_packet
            if packet is None:
                continue
            key = (packet.scenario_id, packet.user_id, packet.date)
            if key in seen:
                continue
            seen.add(key)
            rows.append(packet.to_dict())
    return rows


def _render_packet_summary(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = ["# Full User-Day Packet Summary", ""]
    for packet in _packet_summaries(results):
        lines.extend(
            [
                f"## {packet['scenario_id']}",
                f"User/date: {packet['user_id']} / {packet['date']}",
                f"Packet version: {packet['packet_version']}",
                f"Food candidates: {len(packet.get('food_candidates') or [])}",
                f"Nutrition macros: {', '.join((packet.get('nutrition') or {}).get('macro_targets_actuals_deltas', {}).keys()) or 'none'}",
                f"UserHealthState included fields: {len((packet.get('user_health_state_field_coverage') or {}).get('included_fields') or [])}",
                f"UserHealthState omitted fields: {len((packet.get('user_health_state_field_coverage') or {}).get('omitted_fields') or {})}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_prompt_variants() -> str:
    lines = ["# Prompt Variants", ""]
    for variant in _prompt_variants().values():
        lines.extend(
            [
                f"## {variant.variant_id}",
                f"Label: {variant.label}",
                f"Purpose: {variant.purpose}",
                "",
                variant.writer_instruction,
                "",
            ]
        )
    return "\n".join(lines)


def _render_first_pass_drafts(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# First-Pass Draft Capture",
        "",
        "Exact returned coach-note text. No repair, fallback, phrase cleanup, or product-language rewrite is applied before capture.",
        "",
    ]
    for run in results:
        lines.append(f"## {run.scenario_id}")
        for variant in run.variants:
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


def _render_first_pass_drafts_compact(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = ["# Compact First-Pass Drafts", ""]
    for run in results:
        lines.extend([f"## {run.scenario_id}", ""])
        for variant in run.variants:
            lines.extend(
                [
                    f"### {variant.variant_id} / repeat {variant.repeat_index}",
                    _compact_text(
                        variant.first_pass_draft or variant.skip_reason or "(no draft)"
                    ),
                    "",
                ]
            )
    return "\n".join(lines)


def _render_side_by_side_comparison(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = ["# Side-by-Side Comparison", ""]
    for run in results:
        lines.append(f"## {run.scenario_id}")
        for variant in run.variants:
            lines.extend(
                [
                    f"### {variant.variant_id} / repeat {variant.repeat_index}",
                    variant.first_pass_draft or "(no draft)",
                    "",
                ]
            )
    return "\n".join(lines)


def _render_best_variant_summary(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Best Variant Summary",
        "",
        "Heuristic review aid only. This is not an approval gate.",
        "",
    ]
    for run in results:
        best = _select_best_variant(run)
        if best is None:
            lines.extend([f"## {run.scenario_id}", "Best variant: unavailable", ""])
            continue
        lines.extend(
            [
                f"## {run.scenario_id}",
                f"Best variant: {best.variant_id}",
                f"Repeat: {best.repeat_index}",
                f"Provider/model: {best.provider} / {best.model or 'default'}",
                f"App-copy findings: {len(_variant_app_copy_findings(best))}",
                f"Claim-risk findings: {len(scan_full_user_day_claim_risk(best.first_pass_draft))}",
                "",
                best.first_pass_draft or "(no draft)",
                "",
            ]
        )
    return "\n".join(lines)


def _render_product_language_findings(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Product / App-Copy Findings",
        "",
        "Diagnostic only. This is not a final approval gate.",
        "",
    ]
    for run in results:
        lines.extend([f"## {run.scenario_id}", ""])
        for variant in run.variants:
            findings = _variant_app_copy_findings(variant)
            lines.append(f"### {variant.variant_id} / repeat {variant.repeat_index}")
            if not findings:
                lines.extend(["No configured app-copy findings.", ""])
                continue
            for finding in findings:
                lines.append(
                    f"- Source: {finding['source']}; pattern: `{finding['pattern']}`; category: {finding['category']}"
                )
            lines.append("")
    return "\n".join(lines)


def _render_claim_risk_summary(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Claim Risk Summary",
        "",
        "Post-hoc diagnostic only. First-pass drafts are not altered.",
        "",
    ]
    for run in results:
        lines.append(f"## {run.scenario_id}")
        for variant in run.variants:
            findings = scan_full_user_day_claim_risk(variant.first_pass_draft)
            lines.append(f"### {variant.variant_id} / repeat {variant.repeat_index}")
            if not findings:
                lines.append("No configured claim-risk findings.")
            else:
                for finding in findings:
                    lines.append(f"- `{finding['pattern']}` — {finding['category']}")
            lines.append("")
    return "\n".join(lines)


def _render_consistency_summary(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Consistency Summary",
        "",
        "Repeat-run diagnostic. Similarity is a simple token-overlap heuristic.",
        "",
    ]
    for run in results:
        lines.append(f"## {run.scenario_id}")
        by_variant: dict[str, list[str]] = {}
        for variant in run.variants:
            if not variant.skipped:
                by_variant.setdefault(variant.variant_id, []).append(
                    variant.first_pass_draft
                )
        for variant_id, drafts in by_variant.items():
            lines.append(
                f"- {variant_id}: repeats={len(drafts)}; similarity={_similarity_score(drafts)}"
            )
        if not by_variant:
            lines.append("- No non-skipped drafts available.")
        lines.append("")
    return "\n".join(lines)


def _render_token_cost_telemetry(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Token / Cost Telemetry",
        "",
        "Cost is estimated only when provider usage and explicit cost-per-million environment values are available.",
        "",
        "| Scenario | Variant | Repeat | Provider | Model | Input tokens | Output tokens | Total tokens | Cached input tokens | Estimated cost USD | Cost basis |",
        "|---|---|---:|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for run in results:
        for variant in run.variants:
            meta = variant.runtime_metadata
            lines.append(
                "| "
                f"{run.scenario_id} | {variant.variant_id} | {variant.repeat_index} | {variant.provider} | {variant.model or ''} | "
                f"{_blank(meta.get('input_tokens'))} | {_blank(meta.get('output_tokens'))} | {_blank(meta.get('total_tokens'))} | "
                f"{_blank(meta.get('cached_input_tokens'))} | {_blank(meta.get('estimated_cost_usd'))} | {meta.get('cost_estimate_basis') or ''} |"
            )
    return "\n".join(lines) + "\n"


def _write_telemetry_csv(
    path: Path, results: Sequence[DailyCoachFullUserDayTrialRunResult]
) -> None:
    rows: list[dict[str, Any]] = []
    for run in results:
        for variant in run.variants:
            meta = variant.runtime_metadata
            rows.append(
                {
                    "scenario_id": run.scenario_id,
                    "variant_id": variant.variant_id,
                    "repeat_index": variant.repeat_index,
                    "provider": variant.provider,
                    "model": variant.model or "",
                    "skipped": variant.skipped,
                    "skip_reason": variant.skip_reason or "",
                    "prompt_character_count": meta.get("prompt_character_count"),
                    "input_tokens": meta.get("input_tokens"),
                    "output_tokens": meta.get("output_tokens"),
                    "total_tokens": meta.get("total_tokens"),
                    "cached_input_tokens": meta.get("cached_input_tokens"),
                    "estimated_cost_usd": meta.get("estimated_cost_usd"),
                    "cost_estimate_basis": meta.get("cost_estimate_basis"),
                    "raw_output_length": meta.get("raw_output_length"),
                }
            )
    with path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(rows[0]) if rows else ["scenario_id"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _render_artifact_safety_summary(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
    write_provider_payload_debug: bool,
) -> str:
    return "\n".join(
        [
            "# Artifact Safety Summary",
            "",
            "- Developer-only artifacts: True",
            f"- Provider payload debug written: {write_provider_payload_debug}",
            "- Exact provider input prompt available when debug is enabled: True",
            "- Raw provider envelopes persisted: False",
            "- Secrets allowed: False",
            "- Raw DB rows allowed: False",
            "- Normal Today behavior changed: False",
            f"- Runs inspected: {len(results)}",
        ]
    )


def _render_pasteback_report(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
    write_provider_payload_debug: bool,
) -> str:
    lines = [
        "# Daily Coach Full User-Day Free-Range Payload Baseline v1 — Pasteback Report",
        "",
        f"Provider payload debug written: {write_provider_payload_debug}",
        "Normal Today unchanged: True",
        "Provider promotion: False",
        "Repair/fallback before first-pass capture: False",
        "Known baseline drift: tests/test_daily_narrative_rich_day_service.py",
        "",
    ]
    for run in results:
        lines.extend(
            [
                f"## {run.scenario_id}",
                f"Run id: {run.run_id}",
                f"Provider/model: {run.provider} / {run.model or 'default'}",
                f"Variants/repeats: {len(run.variants)}",
                "",
            ]
        )
        packet = next(
            (
                variant.full_user_day_packet
                for variant in run.variants
                if variant.full_user_day_packet
            ),
            None,
        )
        if packet:
            lines.extend(
                [
                    f"Food candidates: {len(packet.food_candidates)}",
                    f"Macro fields: {', '.join(packet.nutrition.get('macro_targets_actuals_deltas', {}).keys()) or 'none'}",
                    f"UserHealthState included fields: {len(packet.user_health_state_field_coverage.get('included_fields') or [])}",
                    "",
                ]
            )
        best = _select_best_variant(run)
        if best:
            lines.extend(
                [
                    f"Best variant: {best.variant_id} / repeat {best.repeat_index}",
                    "",
                    "Full best-variant first-pass text:",
                    "",
                    best.first_pass_draft or "(no draft)",
                    "",
                ]
            )
        lines.extend(["Compact drafts:", ""])
        for variant in run.variants:
            lines.extend(
                [
                    f"- {variant.variant_id} / repeat {variant.repeat_index}: {_compact_text(variant.first_pass_draft or variant.skip_reason or '(no draft)', limit=500)}",
                ]
            )
        lines.append("")
    return "\n".join(lines)


def _render_provider_input_prompt_debug(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Provider Input Prompt Debug",
        "",
        "Exact prompt strings sent to the provider. Developer-only, opt-in artifact. Raw provider envelopes are not persisted.",
        "",
    ]
    for run in results:
        lines.append(f"## {run.scenario_id}")
        for variant in run.variants:
            lines.extend(
                [
                    f"### {variant.variant_id} / repeat {variant.repeat_index}",
                    f"Prompt character count: {len(variant.provider_input_prompt or '')}",
                    "",
                    "```text",
                    variant.provider_input_prompt or "(no prompt)",
                    "```",
                    "",
                ]
            )
    return "\n".join(lines)


def _payload_debug(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for run in results:
        for variant in run.variants:
            packet = variant.full_user_day_packet
            prompt = variant.provider_input_prompt or ""
            rows.append(
                {
                    "run_id": run.run_id,
                    "scenario_id": run.scenario_id,
                    "provider": run.provider,
                    "model": run.model,
                    "variant_id": variant.variant_id,
                    "repeat_index": variant.repeat_index,
                    "prompt_character_count": len(prompt),
                    "provider_input_prompt": prompt,
                    "full_user_day_packet": packet.to_dict() if packet else None,
                    "product_language_scan_prompt": scan_full_user_day_app_copy(prompt),
                    "product_language_scan_packet": (
                        scan_full_user_day_app_copy(
                            json.dumps(packet.to_dict(), default=str)
                        )
                        if packet
                        else []
                    ),
                    "food_choices_passed": (
                        list(packet.food_candidates) if packet else []
                    ),
                    "macro_fields_passed": list(
                        (
                            packet.nutrition.get("macro_targets_actuals_deltas", {})
                            if packet
                            else {}
                        ).keys()
                    ),
                    "training_fields_passed": (
                        list(packet.training.keys()) if packet else []
                    ),
                    "recovery_fields_passed": (
                        list(packet.recovery.keys()) if packet else []
                    ),
                    "redaction_safety_summary": {
                        "raw_provider_envelope_persisted": False,
                        "secrets_persisted": False,
                        "raw_db_rows_persisted": False,
                    },
                }
            )
    return {
        "milestone": "daily_coach_full_user_day_free_range_payload_baseline_v1",
        "debug_artifact_opt_in": True,
        "records": rows,
    }


def _select_best_variant(
    run: DailyCoachFullUserDayTrialRunResult,
) -> DailyCoachFullUserDayDraftResult | None:
    candidates = [variant for variant in run.variants if not variant.skipped]
    if not candidates:
        return None
    order = {
        "free_range_full_user_day_practical_coach": 3,
        "free_range_full_user_day_direct_coach": 2,
        "free_range_full_user_day_minimal": 1,
    }
    return max(
        candidates,
        key=lambda variant: (
            _variant_score(variant),
            order.get(variant.variant_id, 0),
            -variant.repeat_index,
        ),
    )


def _variant_score(variant: DailyCoachFullUserDayDraftResult) -> int:
    score = 10
    score -= 3 * len(_variant_app_copy_findings(variant))
    score -= 4 * len(scan_full_user_day_claim_risk(variant.first_pass_draft))
    if len(variant.first_pass_draft) >= 120:
        score += 2
    return score


def _variant_app_copy_findings(
    variant: DailyCoachFullUserDayDraftResult,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    sources = {
        "first_pass_draft": variant.first_pass_draft or "",
        "provider_input_prompt": variant.provider_input_prompt or "",
    }
    for source, text in sources.items():
        for finding in scan_full_user_day_app_copy(text):
            findings.append({**finding, "source": source})
    return findings


def _similarity_score(drafts: Sequence[str]) -> str:
    if len(drafts) < 2:
        return "single-draft"
    token_sets = [
        set(re.findall(r"[a-zA-Z]+", draft.lower())) for draft in drafts if draft
    ]
    if len(token_sets) < 2:
        return "insufficient"
    scores = []
    for index, left in enumerate(token_sets):
        for right in token_sets[index + 1 :]:
            if not left and not right:
                continue
            scores.append(len(left & right) / max(1, len(left | right)))
    if not scores:
        return "insufficient"
    return f"{sum(scores) / len(scores):.2f}"


def _compact_text(value: str, *, limit: int = 900) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3].rstrip()}..."


def _blank(value: Any) -> str:
    return "" if value is None else str(value)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )


def _assert_packet_sanitized(packet: DailyCoachFullUserDayPacket) -> None:
    serialized = json.dumps(packet.to_dict(), default=str).lower()
    _assert_text_sanitized(serialized, label="full user-day packet")
    if "approved option" in serialized or "approved food option" in serialized:
        raise DailyCoachFullUserDayFreeRangeError(
            "full_user_day_packet_contains_backend_approval_language"
        )


def _assert_run_sanitized(result: DailyCoachFullUserDayTrialRunResult) -> None:
    _assert_text_sanitized(
        json.dumps(result.to_dict(), default=str), label="full user-day run"
    )


def _assert_text_sanitized(text: str, *, label: str) -> None:
    lowered = text.lower()
    if any(pattern in lowered for pattern in SECRET_PATTERNS):
        raise DailyCoachFullUserDayFreeRangeError(f"{label}_contains_secret_like_text")
    if (
        "raw_provider_envelope" in lowered
        and "raw_provider_envelope_persisted" not in lowered
    ):
        raise DailyCoachFullUserDayFreeRangeError(
            f"{label}_contains_raw_provider_envelope"
        )


def _safe_error(exc: Exception) -> str:
    return re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", str(exc).replace("\n", " ")[:180])
