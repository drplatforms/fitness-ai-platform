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
    "docs/provider_trials/daily_coach_free_range_prompt_payload_decaging_v4"
)
DEFAULT_FULL_USER_DAY_MODEL = "gpt-5.5"
DEFAULT_FULL_USER_DAY_PROVIDER = PROVIDER_DETERMINISTIC
FULL_USER_DAY_PROVIDER_ENV = "DAILY_COACH_FULL_USER_DAY_PROVIDER"
FULL_USER_DAY_MODEL_ENV = "DAILY_COACH_FULL_USER_DAY_MODEL"
FULL_USER_DAY_OPENAI_TIMEOUT_ENV = "DAILY_COACH_FULL_USER_DAY_OPENAI_TIMEOUT_SECONDS"
FULL_USER_DAY_DIRECT_OLLAMA_TIMEOUT_ENV = (
    "DAILY_COACH_FULL_USER_DAY_DIRECT_OLLAMA_TIMEOUT_SECONDS"
)
FULL_USER_DAY_MAX_OUTPUT_TOKENS_ENV = "DAILY_COACH_FULL_USER_DAY_MAX_OUTPUT_TOKENS"
DEFAULT_FULL_USER_DAY_MAX_OUTPUT_TOKENS = 1400
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
    {"pattern": "GREEN LIGHT", "category": "raw_enum_or_label"},
    {"pattern": "max-effort grind", "category": "awkward_gym_phrase"},
    {"pattern": "protein anchor", "category": "awkward_food_phrase"},
    {"pattern": "real protein feeding", "category": "awkward_food_phrase"},
    {"pattern": "real protein serving", "category": "awkward_food_phrase"},
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

BACKEND_LABELS_TO_DECAGE: tuple[str, ...] = (
    "volume_load",
    "main lever",
    "confidence",
    "limiter",
    "anchor",
    "gap",
    "rapid increase",
    "progressing",
    "high",
    "low",
    "moderate",
    "weight_change",
    "internal_workout_model",
    "value_precision",
    "quote_style",
    "macro_gap",
    "training_load",
    "set_level_data_available",
)

MODEL_FACING_DECAGING_POLICY = {
    "debug_may_include_backend_labels": True,
    "model_facing_uses_plain_language": True,
    "first_pass_drafts_unmodified": True,
    "post_hoc_audit_only": True,
}

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
    write_model_input_manifest: bool = False,
    write_precision_summary: bool = False,
    write_food_candidate_summary: bool = False,
    write_completion_diagnostics: bool = False,
    write_food_option_card: bool = False,
    write_macro_display_card: bool = False,
    write_ai_snack_candidates: bool = False,
    write_number_formatting_summary: bool = False,
    write_voice_style_findings: bool = False,
    write_model_facing_coach_facts: bool = False,
    write_decaging_summary: bool = False,
    write_backend_label_exposure_summary: bool = False,
    include_voice_variants: bool = False,
    prefer_decaged_prompt: bool = False,
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
    selected_variants = tuple(
        variants
        or _default_variant_order(include_voice_variants=include_voice_variants)
    )
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
                write_model_input_manifest=write_model_input_manifest,
                write_precision_summary=write_precision_summary,
                write_food_candidate_summary=write_food_candidate_summary,
                write_completion_diagnostics=write_completion_diagnostics,
                write_food_option_card=write_food_option_card,
                write_macro_display_card=write_macro_display_card,
                write_ai_snack_candidates=write_ai_snack_candidates,
                write_number_formatting_summary=write_number_formatting_summary,
                write_voice_style_findings=write_voice_style_findings,
                write_model_facing_coach_facts=write_model_facing_coach_facts,
                write_decaging_summary=write_decaging_summary,
                write_backend_label_exposure_summary=write_backend_label_exposure_summary,
                include_voice_variants=include_voice_variants,
                prefer_decaged_prompt=prefer_decaged_prompt,
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
                    prefer_decaged_prompt=prefer_decaged_prompt,
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
            "model_input_manifest_available": write_model_input_manifest,
            "precision_summary_available": write_precision_summary,
            "food_candidate_summary_available": write_food_candidate_summary,
            "completion_diagnostics_available": write_completion_diagnostics,
            "food_option_card_available": write_food_option_card,
            "macro_display_card_available": write_macro_display_card,
            "ai_snack_candidates_available": write_ai_snack_candidates,
            "number_formatting_summary_available": write_number_formatting_summary,
            "voice_style_findings_available": write_voice_style_findings,
            "model_facing_coach_facts_available": write_model_facing_coach_facts,
            "decaging_summary_available": write_decaging_summary,
            "backend_label_exposure_summary_available": write_backend_label_exposure_summary,
            "include_voice_variants": include_voice_variants,
            "prefer_decaged_prompt": prefer_decaged_prompt,
        },
    )
    _assert_run_sanitized(result)
    if output_dir:
        write_daily_coach_full_user_day_artifacts(
            output_dir,
            [result],
            write_provider_payload_debug=write_provider_payload_debug,
            write_model_input_manifest=write_model_input_manifest,
            write_precision_summary=write_precision_summary,
            write_food_candidate_summary=write_food_candidate_summary,
            write_completion_diagnostics=write_completion_diagnostics,
            write_food_option_card=write_food_option_card,
            write_macro_display_card=write_macro_display_card,
            write_ai_snack_candidates=write_ai_snack_candidates,
            write_number_formatting_summary=write_number_formatting_summary,
            write_voice_style_findings=write_voice_style_findings,
            write_model_facing_coach_facts=write_model_facing_coach_facts,
            write_decaging_summary=write_decaging_summary,
            write_backend_label_exposure_summary=write_backend_label_exposure_summary,
            include_voice_variants=include_voice_variants,
            prefer_decaged_prompt=prefer_decaged_prompt,
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
    write_model_input_manifest: bool = False,
    write_precision_summary: bool = False,
    write_food_candidate_summary: bool = False,
    write_completion_diagnostics: bool = False,
    write_food_option_card: bool = False,
    write_macro_display_card: bool = False,
    write_ai_snack_candidates: bool = False,
    write_number_formatting_summary: bool = False,
    write_voice_style_findings: bool = False,
    write_model_facing_coach_facts: bool = False,
    write_decaging_summary: bool = False,
    write_backend_label_exposure_summary: bool = False,
    include_voice_variants: bool = False,
    prefer_decaged_prompt: bool = False,
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
            write_model_input_manifest=write_model_input_manifest,
            write_precision_summary=write_precision_summary,
            write_food_candidate_summary=write_food_candidate_summary,
            write_completion_diagnostics=write_completion_diagnostics,
            write_food_option_card=write_food_option_card,
            write_macro_display_card=write_macro_display_card,
            write_ai_snack_candidates=write_ai_snack_candidates,
            write_number_formatting_summary=write_number_formatting_summary,
            write_voice_style_findings=write_voice_style_findings,
            write_model_facing_coach_facts=write_model_facing_coach_facts,
            write_decaging_summary=write_decaging_summary,
            write_backend_label_exposure_summary=write_backend_label_exposure_summary,
            include_voice_variants=include_voice_variants,
            prefer_decaged_prompt=prefer_decaged_prompt,
        )
        for scenario_id in selected_scenarios
    ]
    write_daily_coach_full_user_day_artifacts(
        output_dir,
        results,
        write_provider_payload_debug=write_provider_payload_debug,
        write_model_input_manifest=write_model_input_manifest,
        write_precision_summary=write_precision_summary,
        write_food_candidate_summary=write_food_candidate_summary,
        write_completion_diagnostics=write_completion_diagnostics,
        write_food_option_card=write_food_option_card,
        write_macro_display_card=write_macro_display_card,
        write_ai_snack_candidates=write_ai_snack_candidates,
        write_number_formatting_summary=write_number_formatting_summary,
        write_voice_style_findings=write_voice_style_findings,
        write_model_facing_coach_facts=write_model_facing_coach_facts,
        write_decaging_summary=write_decaging_summary,
        write_backend_label_exposure_summary=write_backend_label_exposure_summary,
        include_voice_variants=include_voice_variants,
        prefer_decaged_prompt=prefer_decaged_prompt,
    )
    return results


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


def _macro_value_precision(comparison: Mapping[str, Any]) -> str:
    confidence = str(comparison.get("confidence") or "").lower()
    if confidence in {"low", "limited", "unknown"}:
        return "unknown_or_incomplete"
    if comparison.get("display_allowed") is False:
        return "unknown_or_incomplete"
    return "exact_app_calculated"


def _macro_quote_style(comparison: Mapping[str, Any]) -> str:
    return (
        "direct"
        if _macro_value_precision(comparison) == "exact_app_calculated"
        else "hedged"
    )


def _food_value_precision(item: Mapping[str, Any], *, source: str | None = None) -> str:
    explicit = item.get("value_precision")
    if explicit:
        return str(explicit)
    confidence = str(item.get("confidence") or "").lower()
    has_macro_values = any(
        item.get(key) is not None
        for key in (
            "estimated_calories",
            "estimated_protein_g",
            "estimated_carbs_g",
            "estimated_carbohydrate_g",
            "estimated_fat_g",
        )
    )
    if source == "coach_brief_food_action" and not has_macro_values:
        return "unknown_or_incomplete"
    if confidence in {"low", "generic", "estimate", "estimated"}:
        return "generic_estimate"
    if has_macro_values:
        return "database_calculated"
    return "unknown_or_incomplete"


def _food_quote_style(precision: str) -> str:
    if precision in {
        "exact_app_calculated",
        "database_calculated",
        "rounded_from_database",
    }:
        return "direct"
    return "hedged"


def _format_serving_size(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, int | float):
        return f"{value:g}g"
    text = str(value).strip()
    if text.isdigit():
        return f"{text}g"
    return text


def _food_display_phrase(
    *,
    plain_name: str,
    serving_size: str | None,
    calories: Any,
    protein: Any,
    carbs: Any,
    fat: Any,
    quote_style: str,
) -> str:
    prefix = "roughly " if quote_style == "hedged" else ""
    parts: list[str] = []
    if protein not in (None, ""):
        parts.append(f"{prefix}{protein}g protein")
    if calories not in (None, ""):
        parts.append(f"{prefix}{calories} calories")
    if carbs not in (None, ""):
        parts.append(f"{prefix}{carbs}g carbs")
    if fat not in (None, ""):
        parts.append(f"{prefix}{fat}g fat")
    food = f"{serving_size} {plain_name}" if serving_size else plain_name
    return f"{food} — {', '.join(parts)}" if parts else food


def _food_category(helps_with: Any) -> str | None:
    value = str(helps_with or "").lower()
    if "protein" in value:
        return "protein_foods_that_may_help"
    if "carb" in value:
        return "carb_foods_that_may_help"
    if "fat" in value:
        return "fat_support_foods_that_may_help"
    if "calorie" in value:
        return "calorie_foods_that_may_help"
    return "food_choices_that_fit_today"


def _set_level_training_data(training_state: Any) -> list[dict[str, Any]]:
    if training_state is None:
        return []
    for attr in (
        "set_level_data",
        "exercise_sets",
        "logged_sets",
        "actual_sets",
        "sets",
        "recent_sets",
    ):
        value = getattr(training_state, attr, None)
        if not isinstance(value, list | tuple):
            continue
        rows = []
        for item in value[:40]:
            if isinstance(item, Mapping):
                rows.append(_safe_mapping(item))
            else:
                rows.append(_object_to_dict(item))
        return [row for row in rows if row]
    return []


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
        "free_range_full_user_day_direct_clean": DailyCoachFullUserDayPromptVariant(
            variant_id="free_range_full_user_day_direct_clean",
            label="Free-range full user-day direct clean",
            purpose="Direct coach voice with clean plain-language facts and no decorative Markdown.",
            writer_instruction="Write today’s Daily Coach note in a clean direct voice. Lead with the coaching message, use only the details that help, and keep it natural.",
        ),
        "free_range_full_user_day_hypeman_clean": DailyCoachFullUserDayPromptVariant(
            variant_id="free_range_full_user_day_hypeman_clean",
            label="Free-range full user-day hypeman clean",
            purpose="High-energy coach voice with safety boundaries and no gym-bro clutter.",
            writer_instruction="Write today’s Daily Coach note with high energy and a strong finish. Motivate hard work, but avoid reckless maxing, pain-ignoring, emoji spam, and decorative Markdown.",
        ),
        "free_range_full_user_day_practical_direct": DailyCoachFullUserDayPromptVariant(
            variant_id="free_range_full_user_day_practical_direct",
            label="Free-range full user-day practical direct",
            purpose="Practical direct coaching that selects the few facts that matter most today.",
            writer_instruction="Write today’s Daily Coach note as a practical direct coach. Choose what matters most today instead of mentioning every number.",
        ),
        "free_range_full_user_day_direct_with_hypeman_closer": DailyCoachFullUserDayPromptVariant(
            variant_id="free_range_full_user_day_direct_with_hypeman_closer",
            label="Free-range full user-day direct with hypeman closer",
            purpose="Clean direct coaching with one energetic closing line when safe.",
            writer_instruction="Write today’s Daily Coach note in a direct voice, then end with one energetic closer if the facts support it. Keep it safe and useful.",
        ),
        "free_range_full_user_day_strict_coach": DailyCoachFullUserDayPromptVariant(
            variant_id="free_range_full_user_day_strict_coach",
            label="Free-range full user-day strict coach",
            purpose="Firm, assertive, no-nonsense coaching without cruelty or unsafe intensity.",
            writer_instruction="Write today’s Daily Coach note as a strict coach: firm, clear, and no-nonsense, but never cruel or reckless.",
        ),
        "free_range_full_user_day_empathetic_coach": DailyCoachFullUserDayPromptVariant(
            variant_id="free_range_full_user_day_empathetic_coach",
            label="Free-range full user-day empathetic coach",
            purpose="Understanding, reassuring, motivational coaching that still uses the facts.",
            writer_instruction="Write today’s Daily Coach note as an empathetic coach: reassuring, human, and motivating while staying specific.",
        ),
        "free_range_full_user_day_hypeman_coach": DailyCoachFullUserDayPromptVariant(
            variant_id="free_range_full_user_day_hypeman_coach",
            label="Free-range full user-day hypeman coach",
            purpose="Energetic, exciting coaching that motivates hard work while preserving safe constraints.",
            writer_instruction="Write today’s Daily Coach note as a high-energy hypeman coach: motivating and intense, but keep reps safe, clean, and inside the plan.",
        ),
    }


def _default_variant_order(*, include_voice_variants: bool = False) -> tuple[str, ...]:
    base = (
        "free_range_full_user_day_minimal",
        "free_range_full_user_day_practical_coach",
        "free_range_full_user_day_direct_coach",
    )
    if not include_voice_variants:
        return base
    return base + (
        "free_range_full_user_day_direct_clean",
        "free_range_full_user_day_hypeman_clean",
        "free_range_full_user_day_practical_direct",
        "free_range_full_user_day_direct_with_hypeman_closer",
        "free_range_full_user_day_strict_coach",
        "free_range_full_user_day_empathetic_coach",
        "free_range_full_user_day_hypeman_coach",
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
    explicit_provider = (provider or "").strip().lower()
    if explicit_provider:
        return explicit_provider
    return (
        (env.get(FULL_USER_DAY_PROVIDER_ENV) or DEFAULT_FULL_USER_DAY_PROVIDER)
        .strip()
        .lower()
    )


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


def _render_voice_variant_summary() -> str:
    lines = ["# Voice Variant Summary", ""]
    for variant in _prompt_variants().values():
        lines.extend(
            [
                f"## {variant.variant_id}",
                f"Label: {variant.label}",
                f"Purpose: {variant.purpose}",
                "No phrase bans or old app-copy examples are included in this voice definition.",
                "",
            ]
        )
    return "\n".join(lines)


def _render_precision_usage_summary(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Precision Usage Summary",
        "",
        "Precision contract: quote direct values directly when quote_style is direct; hedge only when quote_style is hedged or value_precision is an estimate.",
        "",
    ]
    for packet in _packet_summaries(results):
        lines.extend([f"## {packet['scenario_id']}", ""])
        food_counts: dict[str, int] = {}
        quote_counts: dict[str, int] = {}
        for food in packet.get("food_candidates") or []:
            food_counts[str(food.get("value_precision") or "missing")] = (
                food_counts.get(str(food.get("value_precision") or "missing"), 0) + 1
            )
            quote_counts[str(food.get("quote_style") or "missing")] = (
                quote_counts.get(str(food.get("quote_style") or "missing"), 0) + 1
            )
        lines.append(f"Food value precision: {food_counts or 'none'}")
        lines.append(f"Food quote styles: {quote_counts or 'none'}")
        macro_rows = (packet.get("nutrition") or {}).get(
            "macro_targets_actuals_deltas", {}
        )
        if macro_rows:
            lines.append("Macro precision:")
            for macro, data in macro_rows.items():
                lines.append(
                    f"- {macro}: value_precision={data.get('value_precision')}; quote_style={data.get('quote_style')}"
                )
        else:
            lines.append("Macro precision: none")
        lines.append("")
    return "\n".join(lines)


def _render_food_candidate_summary(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = ["# Food Candidate Summary", ""]
    for packet in _packet_summaries(results):
        foods = packet.get("food_candidates") or []
        lines.extend(
            [
                f"## {packet['scenario_id']}",
                f"Food candidate count: {len(foods)}",
                "",
            ]
        )
        for food in foods:
            lines.append(
                f"- {food.get('display_phrase') or food.get('plain_name_for_user')}: category={food.get('category')}; value_precision={food.get('value_precision')}; quote_style={food.get('quote_style')}; source={food.get('source')}"
            )
        lines.append("")
    return "\n".join(lines)


def _render_model_input_manifest(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Model Input Manifest",
        "",
        "Answers what the provider saw. Developer-only diagnostic; raw provider envelopes and secrets are not persisted.",
        "",
    ]
    for run in results:
        lines.extend(
            [
                f"## {run.scenario_id}",
                f"Provider/model: {run.provider} / {run.model or 'default'}",
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
        prompt = (
            next(
                (
                    variant.provider_input_prompt
                    for variant in run.variants
                    if variant.provider_input_prompt
                ),
                "",
            )
            or ""
        )
        if not packet:
            lines.extend(["Packet unavailable.", ""])
            continue
        packet_text = json.dumps(packet.to_dict(), default=str)
        lines.extend(
            [
                f"Prompt character count: {len(prompt)}",
                f"Food candidates seen: {len(packet.food_candidates)}",
                f"Macro fields seen: {', '.join(packet.nutrition.get('macro_targets_actuals_deltas', {}).keys()) or 'none'}",
                f"Training fields seen: {', '.join(packet.training.keys()) or 'none'}",
                f"Set-level data available: {packet.training.get('set_level_data_available', False)}",
                f"Set-level data reason: {packet.training.get('set_level_data_unavailable_reason', 'available')}",
                f"Recovery fields seen: {', '.join(packet.recovery.keys()) or 'none'}",
                f"UserHealthState included fields: {len(packet.user_health_state_field_coverage.get('included_fields') or [])}",
                f"UserHealthState omitted fields: {len(packet.user_health_state_field_coverage.get('omitted_fields') or {})}",
                f"Prompt app-copy findings: {scan_full_user_day_app_copy(prompt)}",
                f"Packet app-copy findings: {scan_full_user_day_app_copy(packet_text)}",
                f"Prompt contains phrase bans: {_contains_phrase_ban(prompt)}",
                f"Prompt contains old app examples: {_contains_old_app_example(prompt)}",
                "",
                "Food candidates:",
            ]
        )
        for food in packet.food_candidates:
            lines.append(
                f"- {food.get('display_phrase') or food.get('plain_name_for_user')} | precision={food.get('value_precision')} | quote_style={food.get('quote_style')} | category={food.get('category')}"
            )
        lines.append("")
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


def _precision_debug_summary(
    packet: DailyCoachFullUserDayPacket | None,
) -> dict[str, Any]:
    if packet is None:
        return {}
    food_precision: dict[str, int] = {}
    quote_styles: dict[str, int] = {}
    for food in packet.food_candidates:
        precision = str(food.get("value_precision") or "missing")
        quote = str(food.get("quote_style") or "missing")
        food_precision[precision] = food_precision.get(precision, 0) + 1
        quote_styles[quote] = quote_styles.get(quote, 0) + 1
    macro_precision = {
        macro: {
            "value_precision": data.get("value_precision"),
            "quote_style": data.get("quote_style"),
        }
        for macro, data in packet.nutrition.get(
            "macro_targets_actuals_deltas", {}
        ).items()
        if isinstance(data, Mapping)
    }
    return {
        "food_value_precision": food_precision,
        "food_quote_styles": quote_styles,
        "macro_precision": macro_precision,
    }


def _select_best_variant(
    run: DailyCoachFullUserDayTrialRunResult,
) -> DailyCoachFullUserDayDraftResult | None:
    candidates = [variant for variant in run.variants if not variant.skipped]
    if not candidates:
        return None
    order = {
        "free_range_full_user_day_practical_coach": 6,
        "free_range_full_user_day_empathetic_coach": 5,
        "free_range_full_user_day_strict_coach": 4,
        "free_range_full_user_day_direct_coach": 3,
        "free_range_full_user_day_hypeman_coach": 2,
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


def _contains_phrase_ban(text: str) -> bool:
    lowered = text.lower()
    return any(
        phrase in lowered
        for phrase in (
            "do not use the phrase",
            "never say",
            "banned phrase",
            "forbidden phrase",
        )
    )


def _contains_old_app_example(text: str) -> bool:
    lowered = text.lower()
    return any(
        phrase in lowered
        for phrase in (
            "old daily coach copy",
            "deterministic fallback example",
            "current narrow path",
            "product voice audit example",
        )
    )


def _compact_text(value: str, *, limit: int = 900) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3].rstrip()}..."


def _blank(value: Any) -> str:
    return "" if value is None else str(value)


def _model_facing_coach_facts(packet: DailyCoachFullUserDayPacket) -> dict[str, Any]:
    macro_card = packet.macro_display_card or _macro_display_card_from_targets(
        packet.nutrition.get("macro_targets_actuals_deltas", {})
    )
    food_card = packet.food_option_card or _food_option_card(packet.food_candidates)
    snacks = list(packet.ai_snack_candidates)
    training = packet.training
    recovery = packet.recovery
    facts = {
        "packet_version": "model_facing_coach_facts_v4",
        "user_context": _drop_unknowns(
            {
                "goal": packet.user_profile.get("primary_goal"),
                "activity_level": _normalize_label(
                    packet.user_profile.get("activity_level")
                ),
                "date": packet.date,
                "scenario_id": packet.scenario_id,
            }
        ),
        "today_for_the_coach": {
            "main_job": "Choose the most useful coaching message from training, nutrition, recovery, and logging facts.",
            "editorial_permission": "You do not need to mention every number. Lead with the coaching message and use details only when they support it.",
            "logged_intake_context": "Nutrition values are logged intake so far, not necessarily the final day.",
            "macro_range_context": "Do not frame broad macro ranges as panic-level deficits. Use the macro card for details and coach the next useful meal.",
        },
        "training_facts_for_coach": _drop_unknowns(
            {
                "summary": _plain_training_summary(training),
                "session_name": training.get("user_facing_session_name")
                or training.get("session_name"),
                "session_type": training.get("session_type"),
                "session_intensity": training.get("session_intensity"),
                "session_name_source": training.get("session_name_source"),
                "set_level_data_available": training.get("set_level_data_available"),
                "set_level_note": _set_level_plain_note(training),
                "coach_guidance": (
                    "Train steadily, keep reps clean, and do not turn today into a max test."
                    if training
                    else None
                ),
            }
        ),
        "nutrition_facts_for_coach": _drop_unknowns(
            {
                "summary": _plain_nutrition_summary(packet.nutrition),
                "macro_card": macro_card,
                "next_meal_guidance": "Start with protein, then add carbs if meals remain or carbs are low.",
            }
        ),
        "food_options_for_coach": {
            "heading": "Food choices that fit today",
            "display_policy": "Use natural names. Do not say approved option, anchor, gap, or limiter.",
            "food_option_card": food_card,
        },
        "approximate_meal_options_for_coach": {
            "heading": "Approximate meal options",
            "display_policy": "Introduce these as approximate once; do not repeat roughly on every value and do not hedge zero values.",
            "snack_candidates": snacks,
        },
        "recovery_facts_for_coach": _drop_unknowns(
            {
                "summary": _plain_recovery_summary(recovery),
                "readiness_level": _normalize_label(recovery.get("readiness_level")),
                "fatigue_risk": _normalize_label(recovery.get("fatigue_risk")),
                "weight_trend_note": _plain_weight_note(recovery),
            }
        ),
        "writing_guidance": {
            "no_markdown_bold": True,
            "no_emoji_headers": True,
            "no_decorative_markdown": True,
            "translate_technical_metrics": True,
            "avoid_internal_labels": True,
            "safe_energy_allowed": True,
        },
        "do_not_infer": list(packet.do_not_infer),
    }
    return _drop_backend_labels_from_model_facts(facts)


def _plain_training_summary(training: Mapping[str, Any]) -> str:
    if not training:
        return "Training details are limited today."
    load = _normalize_label(training.get("training_load"))
    trend = _normalize_label(training.get("training_trend"))
    rir = training.get("avg_rir_display") or training.get("avg_rir")
    parts = []
    if load:
        parts.append(f"Recent training workload appears {load.lower()}.")
    if trend:
        parts.append(f"Training trend looks {trend.lower()} based on available logs.")
    if rir:
        parts.append(f"Recent effort looks controlled around {rir} RIR.")
    return (
        " ".join(parts)
        or "Use the available training facts without overexplaining technical metrics."
    )


def _set_level_plain_note(training: Mapping[str, Any]) -> str:
    if training.get("set_level_data_available"):
        return "Structured set-level workout data is available for the coach to interpret plainly."
    reason = (
        training.get("set_level_data_unavailable_reason")
        or "not available in this path"
    )
    return f"Set-level workout data is not available: {reason}."


def _plain_nutrition_summary(nutrition: Mapping[str, Any]) -> str:
    actuals = (
        nutrition.get("actuals")
        if isinstance(nutrition.get("actuals"), Mapping)
        else {}
    )
    calories = actuals.get("logged_calories") if isinstance(actuals, Mapping) else None
    protein = actuals.get("logged_protein_g") if isinstance(actuals, Mapping) else None
    parts = []
    if calories is not None:
        parts.append(f"Logged intake so far is {_format_calories(calories)}.")
    if protein is not None:
        parts.append(f"Logged protein so far is {_format_grams(protein)} protein.")
    parts.append(
        "Use the macro card for exact display details instead of narrating every deficit."
    )
    return " ".join(parts)


def _plain_recovery_summary(recovery: Mapping[str, Any]) -> str:
    readiness = _normalize_label(recovery.get("readiness_level"))
    fatigue = _normalize_label(recovery.get("fatigue_risk"))
    if readiness and fatigue:
        return f"Recovery looks {readiness.lower()} with {fatigue.lower()} fatigue risk based on available logs."
    if readiness:
        return f"Recovery looks {readiness.lower()} based on available logs."
    return "Recovery facts are available only where logged."


def _plain_weight_note(recovery: Mapping[str, Any]) -> str | None:
    if not recovery:
        return None
    if recovery.get("weight_trend_surface_to_coach") is False:
        reason = (
            recovery.get("weight_trend_suppression_reason") or "insufficient confidence"
        )
        return f"Do not emphasize the recent weight trend in the coach note: {reason}."
    change = recovery.get("weight_change_display")
    if change:
        return f"If useful, mention recent body-weight change as {change}, not as a raw decimal."
    return None


def _meal_display_phrase(
    name: str,
    protein: Any,
    calories: Any,
    carbs: Any,
    fat: Any,
    precision: str,
) -> str:
    values = []
    if protein is not None:
        values.append(f"{_format_grams(protein)} protein")
    if calories is not None:
        values.append(_format_calories(calories))
    if carbs is not None:
        values.append(f"{_format_grams(carbs)} carbs")
    if fat is not None:
        values.append(f"{_format_grams(fat)} fat")
    prefix = "About " if precision == "generic_estimate" else ""
    return f"{prefix}{name} — {', '.join(values)}"


def _drop_backend_labels_from_model_facts(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            _clean_model_key(str(key)): _drop_backend_labels_from_model_facts(item)
            for key, item in value.items()
            if _clean_model_key(str(key))
        }
    if isinstance(value, tuple):
        return tuple(_drop_backend_labels_from_model_facts(item) for item in value)
    if isinstance(value, list):
        return [_drop_backend_labels_from_model_facts(item) for item in value]
    if isinstance(value, str):
        return _clean_model_text(value)
    return value


def _clean_model_key(key: str) -> str:
    replacements = {
        "value_precision": "number_reliability",
        "quote_style": "number_wording",
        "macro_gap": "macro_need",
        "weight_change": "body_weight_change",
        "volume_load": "training_workload",
        "internal_workout_model": "workout_name_source",
    }
    return replacements.get(key, key)


def _clean_model_text(text: str) -> str:
    cleaned = text.replace("volume_load", "training workload")
    cleaned = cleaned.replace("weight_change", "body-weight change")
    cleaned = cleaned.replace("internal_workout_model", "internal workout label")
    cleaned = cleaned.replace("value_precision", "number reliability")
    cleaned = cleaned.replace("quote_style", "number wording")
    cleaned = cleaned.replace("macro_gap", "macro need")
    cleaned = cleaned.replace("Rapid Increase", "quick change")
    cleaned = cleaned.replace("Progressing", "moving forward")
    return cleaned


def _model_facing_coach_facts_payload(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> dict[str, Any]:
    records = []
    for run in results:
        packet = next(
            (
                variant.full_user_day_packet
                for variant in run.variants
                if variant.full_user_day_packet
            ),
            None,
        )
        records.append(
            {
                "run_id": run.run_id,
                "scenario_id": run.scenario_id,
                "model_facing_coach_facts": (
                    _model_facing_coach_facts(packet) if packet else None
                ),
            }
        )
    return {"records": records, "debug_payload_separate": True, "developer_only": True}


def _render_model_facing_coach_facts(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Model-Facing Coach Facts",
        "",
        "Clean source material intended for the provider prompt when decaged mode is enabled.",
        "Debug/internal labels remain in debug artifacts, not this coach-facing fact layer.",
        "",
    ]
    for record in _model_facing_coach_facts_payload(results)["records"]:
        lines.append(f"## {record['scenario_id']}")
        facts = record.get("model_facing_coach_facts") or {}
        lines.append("```json")
        lines.append(json.dumps(facts, indent=2, sort_keys=True, default=str))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _backend_label_hits(text: str) -> list[str]:
    lowered = text.lower()
    return sorted({label for label in BACKEND_LABELS_TO_DECAGE if label in lowered})


def _render_decaging_summary(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    payload = _model_facing_coach_facts_payload(results)
    lines = [
        "# Decaging Summary",
        "",
        "Backend computes facts. The decaged provider prompt uses clean coach facts and gives the model editorial judgment.",
        "",
    ]
    for record in payload["records"]:
        facts_text = json.dumps(
            record.get("model_facing_coach_facts") or {}, default=str
        )
        lines.append(f"## {record['scenario_id']}")
        lines.append(
            f"- Backend labels in model-facing facts: {_backend_label_hits(facts_text) or []}"
        )
        lines.append(
            "- Prompt policy: do not echo field labels or internal categories."
        )
        lines.append(
            "- Editorial judgment: model may choose what matters and omit technical metrics."
        )
        lines.append(
            "- Dense numeric detail: use compact cards when helpful, not main-paragraph overload."
        )
        lines.append("")
    return "\n".join(lines)


def _backend_label_exposure_payload(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> dict[str, Any]:
    records = []
    for run in results:
        for variant in run.variants:
            packet = variant.full_user_day_packet
            debug_text = json.dumps(packet.to_dict(), default=str) if packet else ""
            facts = _model_facing_coach_facts(packet) if packet else {}
            facts_text = json.dumps(facts, default=str)
            prompt = variant.provider_input_prompt or ""
            draft = variant.first_pass_draft or ""
            debug_labels = _backend_label_hits(debug_text)
            facts_labels = _backend_label_hits(facts_text)
            prompt_labels = _backend_label_hits(prompt)
            output_labels = _backend_label_hits(draft)
            records.append(
                {
                    "scenario_id": run.scenario_id,
                    "variant_id": variant.variant_id,
                    "repeat_index": variant.repeat_index,
                    "debug_internal_labels_present": debug_labels,
                    "removed_from_model_facing_facts": sorted(
                        set(debug_labels) - set(facts_labels)
                    ),
                    "model_facing_labels_present": facts_labels,
                    "provider_prompt_labels_present": prompt_labels,
                    "first_pass_output_labels_present": output_labels,
                }
            )
    return {"records": records, "developer_only": True, "post_hoc_only": True}


def _render_backend_label_exposure_summary(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Backend Label Exposure Summary",
        "",
        "Post-hoc diagnostic: proves which internal labels stayed in debug, were removed from model-facing facts, reached the prompt, or appeared in first-pass output.",
        "",
    ]
    for record in _backend_label_exposure_payload(results)["records"]:
        lines.append(
            f"## {record['scenario_id']} / {record['variant_id']} / repeat {record['repeat_index']}"
        )
        lines.append(
            f"- Debug/internal labels present: {record['debug_internal_labels_present'] or []}"
        )
        lines.append(
            f"- Removed from model-facing facts: {record['removed_from_model_facing_facts'] or []}"
        )
        lines.append(
            f"- Still in model-facing facts: {record['model_facing_labels_present'] or []}"
        )
        lines.append(
            f"- Reached provider prompt: {record['provider_prompt_labels_present'] or []}"
        )
        lines.append(
            f"- Appeared in first-pass output: {record['first_pass_output_labels_present'] or []}"
        )
        lines.append("")
    return "\n".join(lines)


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


# ---------------------------------------------------------------------------
# v3 output completion + coach surface polish helpers
# ---------------------------------------------------------------------------

PRACTICAL_FOOD_SEEDS: tuple[dict[str, Any], ...] = (
    {
        "display_name": "egg whites",
        "suggested_grams": 150,
        "estimated_calories": 78,
        "estimated_protein_g": 16,
        "estimated_carbohydrate_g": 1,
        "estimated_fat_g": 0,
        "macro_gap_addressed": "protein_g",
        "confidence": "database_calculated",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "whey protein",
        "suggested_grams": 31,
        "estimated_calories": 120,
        "estimated_protein_g": 24,
        "estimated_carbohydrate_g": 3,
        "estimated_fat_g": 2,
        "macro_gap_addressed": "protein_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "cottage cheese",
        "suggested_grams": 225,
        "estimated_calories": 206,
        "estimated_protein_g": 28,
        "estimated_carbohydrate_g": 8,
        "estimated_fat_g": 5,
        "macro_gap_addressed": "protein_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "lean ground beef",
        "suggested_grams": 170,
        "estimated_calories": 320,
        "estimated_protein_g": 42,
        "estimated_carbohydrate_g": 0,
        "estimated_fat_g": 16,
        "macro_gap_addressed": "protein_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "salmon",
        "suggested_grams": 170,
        "estimated_calories": 350,
        "estimated_protein_g": 38,
        "estimated_carbohydrate_g": 0,
        "estimated_fat_g": 22,
        "macro_gap_addressed": "fat_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "shrimp",
        "suggested_grams": 170,
        "estimated_calories": 170,
        "estimated_protein_g": 36,
        "estimated_carbohydrate_g": 1,
        "estimated_fat_g": 2,
        "macro_gap_addressed": "protein_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "rice",
        "suggested_grams": 180,
        "estimated_calories": 230,
        "estimated_protein_g": 4,
        "estimated_carbohydrate_g": 50,
        "estimated_fat_g": 1,
        "macro_gap_addressed": "carbs_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "potatoes",
        "suggested_grams": 300,
        "estimated_calories": 260,
        "estimated_protein_g": 7,
        "estimated_carbohydrate_g": 60,
        "estimated_fat_g": 0,
        "macro_gap_addressed": "carbs_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "oats",
        "suggested_grams": 80,
        "estimated_calories": 300,
        "estimated_protein_g": 10,
        "estimated_carbohydrate_g": 54,
        "estimated_fat_g": 6,
        "macro_gap_addressed": "carbs_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "banana",
        "suggested_grams": 120,
        "estimated_calories": 105,
        "estimated_protein_g": 1,
        "estimated_carbohydrate_g": 27,
        "estimated_fat_g": 0,
        "macro_gap_addressed": "carbs_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "bagel",
        "suggested_grams": 95,
        "estimated_calories": 260,
        "estimated_protein_g": 10,
        "estimated_carbohydrate_g": 52,
        "estimated_fat_g": 2,
        "macro_gap_addressed": "carbs_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "bread",
        "suggested_grams": 56,
        "estimated_calories": 150,
        "estimated_protein_g": 5,
        "estimated_carbohydrate_g": 28,
        "estimated_fat_g": 2,
        "macro_gap_addressed": "carbs_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "wrap",
        "suggested_grams": 70,
        "estimated_calories": 210,
        "estimated_protein_g": 6,
        "estimated_carbohydrate_g": 35,
        "estimated_fat_g": 5,
        "macro_gap_addressed": "carbs_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "pasta",
        "suggested_grams": 200,
        "estimated_calories": 315,
        "estimated_protein_g": 11,
        "estimated_carbohydrate_g": 63,
        "estimated_fat_g": 2,
        "macro_gap_addressed": "carbs_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "fruit",
        "suggested_grams": 200,
        "estimated_calories": 120,
        "estimated_protein_g": 1,
        "estimated_carbohydrate_g": 30,
        "estimated_fat_g": 0,
        "macro_gap_addressed": "carbs_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "avocado",
        "suggested_grams": 100,
        "estimated_calories": 160,
        "estimated_protein_g": 2,
        "estimated_carbohydrate_g": 9,
        "estimated_fat_g": 15,
        "macro_gap_addressed": "fat_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "olive oil",
        "suggested_grams": 14,
        "estimated_calories": 119,
        "estimated_protein_g": 0,
        "estimated_carbohydrate_g": 0,
        "estimated_fat_g": 14,
        "macro_gap_addressed": "fat_g",
        "confidence": "database_calculated",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "peanut butter",
        "suggested_grams": 32,
        "estimated_calories": 190,
        "estimated_protein_g": 8,
        "estimated_carbohydrate_g": 7,
        "estimated_fat_g": 16,
        "macro_gap_addressed": "fat_g",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "whole milk",
        "suggested_grams": 244,
        "estimated_calories": 149,
        "estimated_protein_g": 8,
        "estimated_carbohydrate_g": 12,
        "estimated_fat_g": 8,
        "macro_gap_addressed": "calories",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "trail mix",
        "suggested_grams": 60,
        "estimated_calories": 300,
        "estimated_protein_g": 8,
        "estimated_carbohydrate_g": 28,
        "estimated_fat_g": 18,
        "macro_gap_addressed": "calories",
        "confidence": "generic",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "chicken breast",
        "suggested_grams": 155,
        "estimated_calories": 256,
        "estimated_protein_g": 48,
        "estimated_carbohydrate_g": 0,
        "estimated_fat_g": 6,
        "macro_gap_addressed": "protein_g",
        "confidence": "database_calculated",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "turkey breast",
        "suggested_grams": 170,
        "estimated_calories": 230,
        "estimated_protein_g": 49,
        "estimated_carbohydrate_g": 0,
        "estimated_fat_g": 3,
        "macro_gap_addressed": "protein_g",
        "confidence": "database_calculated",
        "source": "v3_practical_seed",
    },
    {
        "display_name": "canned tuna",
        "suggested_grams": 150,
        "estimated_calories": 174,
        "estimated_protein_g": 38,
        "estimated_carbohydrate_g": 0,
        "estimated_fat_g": 1,
        "macro_gap_addressed": "protein_g",
        "confidence": "database_calculated",
        "source": "v3_practical_seed",
    },
)


def _max_output_tokens(env: Mapping[str, str]) -> int:
    configured = env.get(FULL_USER_DAY_MAX_OUTPUT_TOKENS_ENV)
    try:
        value = (
            int(configured) if configured else DEFAULT_FULL_USER_DAY_MAX_OUTPUT_TOKENS
        )
    except ValueError:
        value = DEFAULT_FULL_USER_DAY_MAX_OUTPUT_TOKENS
    return max(900, min(value, 2400))


def _format_number(value: Any, *, suffix: str = "", decimals: int = 0) -> str | None:
    number = _optional_float(value)
    if number is None:
        return None
    if decimals <= 0:
        text = f"{number:,.0f}"
    else:
        rounded = round(number, decimals)
        text = f"{rounded:,.{decimals}f}".rstrip("0").rstrip(".")
    return f"{text}{suffix}"


def _format_calories(value: Any) -> str | None:
    text = _format_number(value, decimals=0)
    return f"{text} calories" if text is not None else None


def _format_grams(value: Any) -> str | None:
    return _format_number(value, suffix="g", decimals=0)


def _format_pounds(value: Any) -> str | None:
    return _format_number(value, suffix=" lb", decimals=0)


def _format_rir(value: Any) -> str | None:
    return _format_number(value, suffix=" RIR", decimals=1)


def _format_range(
    low: Any, high: Any, *, formatter: Callable[[Any], str | None]
) -> str | None:
    low_text = formatter(low)
    high_text = formatter(high)
    if low_text and high_text:
        return f"{low_text}–{high_text}"
    return low_text or high_text


def _format_delta(value: Any, *, macro: str) -> str | None:
    number = _optional_float(value)
    if number is None:
        return None
    abs_value = abs(number)
    if macro == "calories":
        return _format_calories(abs_value)
    return _format_grams(abs_value)


def _macro_formatter(macro: str) -> Callable[[Any], str | None]:
    return _format_calories if macro == "calories" else _format_grams


def _display_macro_name(macro: str) -> str:
    return {
        "protein_g": "Protein",
        "carbs_g": "Carbs",
        "carbohydrate_g": "Carbs",
        "fat_g": "Fat",
        "calories": "Calories",
    }.get(macro, str(macro).replace("_", " ").title())


def _display_macro_payload(macro: str, comparison: Mapping[str, Any]) -> dict[str, Any]:
    formatter = _macro_formatter(macro)
    actual = formatter(comparison.get("actual"))
    target = _format_range(
        comparison.get("target_min"), comparison.get("target_max"), formatter=formatter
    )
    delta_min = comparison.get("delta_min")
    delta_max = comparison.get("delta_max")
    delta_display = _format_range(
        abs(_optional_float(delta_min) or 0),
        abs(_optional_float(delta_max) or 0),
        formatter=formatter,
    )
    compact = " / ".join(part for part in (actual, target) if part)
    status = str(comparison.get("target_status") or "").lower() or None
    return _drop_unknowns(
        {
            "label": _display_macro_name(macro),
            "actual_display": actual,
            "target_display": target,
            "delta_display": delta_display,
            "compact_display": compact,
            "status_display": status,
            "value_precision": _macro_value_precision(comparison),
            "quote_style": _macro_quote_style(comparison),
        }
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
    display_actuals = {
        "logged_calories": _format_calories(actuals.get("logged_calories")),
        "logged_protein_g": _format_grams(actuals.get("logged_protein_g")),
        "logged_carbs_g": _format_grams(actuals.get("logged_carbs_g")),
        "logged_fat_g": _format_grams(actuals.get("logged_fat_g")),
    }
    macro_targets: dict[str, Any] = {}
    for macro, comparison in macro_status.items():
        if not isinstance(comparison, Mapping):
            continue
        display = _display_macro_payload(str(macro), comparison)
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
                "value_precision": _macro_value_precision(comparison),
                "quote_style": _macro_quote_style(comparison),
                "display": display,
            }
        )
    return _drop_unknowns(
        {
            "available": nutrition.get("available"),
            "date": nutrition.get("date"),
            "logging_completeness": nutrition.get("logging_completeness"),
            "confidence": nutrition.get("confidence"),
            "actuals": actuals,
            "display_actuals": _drop_unknowns(display_actuals),
            "macro_targets_actuals_deltas": macro_targets,
            "macro_display_card": _macro_display_card_from_targets(macro_targets),
            "calories": getattr(health_nutrition, "calories", None),
            "calories_display": _format_calories(
                getattr(health_nutrition, "calories", None)
            ),
            "protein_grams": getattr(health_nutrition, "protein_grams", None),
            "protein_display": _format_grams(
                getattr(health_nutrition, "protein_grams", None)
            ),
            "carbohydrate_grams": getattr(health_nutrition, "carbohydrate_grams", None),
            "carbohydrate_display": _format_grams(
                getattr(health_nutrition, "carbohydrate_grams", None)
            ),
            "fat_grams": getattr(health_nutrition, "fat_grams", None),
            "fat_display": _format_grams(getattr(health_nutrition, "fat_grams", None)),
            "protein_status": _normalize_label(
                getattr(health_nutrition, "protein_status", None)
            ),
            "calorie_status": _normalize_label(
                getattr(health_nutrition, "calorie_status", None)
            ),
            "recovery_nutrition_status": _normalize_label(
                getattr(health_nutrition, "recovery_nutrition_status", None)
            ),
            "limitations": nutrition.get("limitations"),
            "priority": _nutrition_priority(macro_targets),
        }
    )


def _food_candidates(
    brief: ApprovedCoachBrief, value_context: Mapping[str, Any], *, limit: int
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(item: Mapping[str, Any], *, source: str | None = None) -> None:
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
        serving_size = _format_serving_size(
            item.get("serving_size")
            or item.get("serving_display")
            or item.get("suggested_grams")
        )
        precision = _food_value_precision(item, source=source)
        quote_style = _food_quote_style(precision)
        helps_with = _macro_label(
            item.get("helps_with") or item.get("macro_gap_addressed")
        )
        calories = item.get("estimated_calories")
        protein = item.get("estimated_protein_g")
        carbs = item.get("estimated_carbs_g") or item.get("estimated_carbohydrate_g")
        fat = item.get("estimated_fat_g")
        candidate = _drop_unknowns(
            {
                "display_name": plain_name,
                "plain_name_for_user": plain_name,
                "serving_size": serving_size,
                "estimated_calories": calories,
                "estimated_protein_g": protein,
                "estimated_carbs_g": carbs,
                "estimated_fat_g": fat,
                "calories_display": _format_calories(calories),
                "protein_display": _format_grams(protein),
                "carbs_display": _format_grams(carbs),
                "fat_display": _format_grams(fat),
                "value_precision": precision,
                "quote_style": quote_style,
                "display_phrase": _food_display_phrase(
                    plain_name=plain_name,
                    serving_size=serving_size,
                    calories=calories,
                    protein=protein,
                    carbs=carbs,
                    fat=fat,
                    quote_style=quote_style,
                ),
                "why_useful_today": _food_reason(
                    item.get("why_useful_today")
                    or item.get("macro_reason")
                    or item.get("macro_gap_addressed")
                    or item.get("summary")
                ),
                "helps_with": helps_with,
                "category": _food_category(helps_with),
                "source": source or item.get("source") or "nutrition_suggestion",
                "confidence": item.get("confidence"),
            }
        )
        candidates.append(candidate)

    nutrition = (
        value_context.get("approved_nutrition")
        if isinstance(value_context, Mapping)
        else {}
    )
    if isinstance(nutrition, Mapping):
        for suggestion in nutrition.get("approved_food_suggestions") or []:
            if isinstance(suggestion, Mapping):
                add(suggestion, source="nutrition_food_suggestion")
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
            },
            source="coach_brief_food_action",
        )
    for seed in PRACTICAL_FOOD_SEEDS:
        add(seed, source=str(seed.get("source") or "v3_practical_seed"))
    return candidates[: max(1, min(limit, 50))]


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
    set_level_data = _set_level_training_data(training_state)
    internal_name = _extract_session_name(candidate_text)
    total_volume = getattr(training_state, "total_volume_load", None)
    avg_rir = getattr(training_state, "avg_rir", None)
    return _drop_unknowns(
        {
            "has_workout_data": getattr(training_state, "has_workout_data", None),
            "workout_count": getattr(training_state, "workout_count", None),
            "adherence_level": _normalize_label(
                getattr(training_state, "adherence_level", None)
            ),
            "training_trend": _normalize_label(
                getattr(training_state, "training_trend", None)
            ),
            "total_volume_load": total_volume,
            "total_volume_load_display": (
                f"{_format_number(total_volume) or 'unknown'} total volume load"
                if total_volume is not None
                else None
            ),
            "avg_rir": avg_rir,
            "avg_rir_display": _format_rir(avg_rir),
            "training_load": _normalize_label(
                getattr(training_state, "training_load", None)
            ),
            "recovery_demand": _normalize_label(
                getattr(training_state, "recovery_demand", None)
            ),
            "internal_workout_model": internal_name,
            "user_facing_session_name": _user_facing_session_name(internal_name),
            "session_type": _session_type(internal_name),
            "session_intensity": _normalize_label(
                getattr(training_state, "training_load", None)
            ),
            "session_name_source": (
                "synthesis_guidance_extract" if internal_name else "unavailable"
            ),
            "scheduled_session_name": _user_facing_session_name(internal_name),
            "training_suitability": _training_suitability(health_state),
            "actual_set_logging_completeness": (
                "available"
                if getattr(training_state, "has_workout_data", None)
                else "unknown"
            ),
            "set_level_data_available": bool(set_level_data),
            "set_level_data": set_level_data,
            "set_level_data_unavailable_reason": (
                None
                if set_level_data
                else "no structured set-level data exposed by UserHealthState.training_state in this path"
            ),
        }
    )


def _recovery_payload(health_state: Any) -> dict[str, Any]:
    recovery_state = getattr(health_state, "recovery_state", None)
    weight_change = getattr(recovery_state, "weight_change", None)
    suppress_weight = _weight_change_is_anomalous(weight_change)
    return _drop_unknowns(
        {
            "readiness_level": _normalize_label(
                getattr(recovery_state, "readiness_level", None)
            ),
            "fatigue_risk": _normalize_label(
                getattr(recovery_state, "fatigue_risk", None)
            ),
            "recovery_score": getattr(recovery_state, "recovery_score", None),
            "recovery_score_display": _format_number(
                getattr(recovery_state, "recovery_score", None), decimals=0
            ),
            "avg_sleep": getattr(recovery_state, "avg_sleep", None),
            "avg_sleep_display": _format_number(
                getattr(recovery_state, "avg_sleep", None), suffix=" hours", decimals=1
            ),
            "avg_energy": getattr(recovery_state, "avg_energy", None),
            "avg_energy_display": _format_number(
                getattr(recovery_state, "avg_energy", None), decimals=0
            ),
            "avg_soreness": getattr(recovery_state, "avg_soreness", None),
            "avg_soreness_display": _format_number(
                getattr(recovery_state, "avg_soreness", None), decimals=0
            ),
            "sleep_trend": _normalize_label(
                getattr(recovery_state, "sleep_trend", None)
            ),
            "weight_trend": _normalize_label(
                getattr(recovery_state, "weight_trend", None)
            ),
            "weight_change": weight_change,
            "weight_change_display": _format_pounds(weight_change),
            "weight_trend_confidence": "low" if suppress_weight else "normal",
            "weight_trend_surface_to_coach": not suppress_weight,
            "weight_trend_suppression_reason": (
                "anomalous recent check-in / insufficient confidence"
                if suppress_weight
                else None
            ),
            "raw_weight_debug": {
                "weight_change": weight_change,
                "weight_trend": getattr(recovery_state, "weight_trend", None),
            },
            "readiness_interpretation": _readiness_interpretation(recovery_state),
        }
    )


def build_daily_coach_full_user_day_packet(
    *,
    user_id: int,
    target_date: str,
    scenario_id: str,
    synthesis: Any | None = None,
    health_state: Any | None = None,
    value_context: Mapping[str, Any] | None = None,
    brief: ApprovedCoachBrief | None = None,
    food_candidate_limit: int = 30,
) -> DailyCoachFullUserDayPacket:
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
    food_candidates = tuple(
        _food_candidates(
            resolved_brief,
            resolved_value_context,
            limit=max(1, min(food_candidate_limit, 50)),
        )
    )
    macro_card = _macro_display_card_from_targets(
        nutrition.get("macro_targets_actuals_deltas", {})
    )
    food_card = _food_option_card(food_candidates)
    snacks = tuple(_ai_snack_candidates(food_candidates))
    packet = DailyCoachFullUserDayPacket(
        packet_version="daily_coach_free_range_prompt_payload_decaging_v4",
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
        food_candidates=food_candidates,
        ai_snack_candidates=snacks,
        macro_display_card=macro_card,
        food_option_card=food_card,
        number_formatting=_number_formatting_summary_payload(
            nutrition, training, recovery, food_candidates
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
            "v3 practical food seed candidates for developer-only free-range trial",
        ),
    )
    _assert_packet_sanitized(packet)
    return packet


def build_full_user_day_free_range_prompt(
    packet: DailyCoachFullUserDayPacket,
    variant_id: str,
    *,
    prefer_decaged_prompt: bool = False,
) -> str:
    variant = _resolve_variant(variant_id)
    if prefer_decaged_prompt:
        coach_facts = _model_facing_coach_facts(packet)
        facts_json = json.dumps(coach_facts, indent=2, sort_keys=True, default=str)
        prompt = (
            f"{variant.writer_instruction}\n\n"
            "Use the coach facts below as clean source material.\n"
            "Write like a human coach, not a backend report.\n"
            "Use the facts, but do not echo field labels, internal categories, enum values, or debug wording.\n"
            "Do not copy backend wording into the note. If a detail sounds technical, translate it into normal coaching language or leave it out.\n"
            "You may choose what matters most today. You do not need to mention every fact or every number.\n"
            "Lead with the coaching message. Use details only when they support the message.\n"
            "Dense numeric detail belongs in compact cards, not the main paragraph.\n"
            "Food and meal-option numbers are estimates; introduce approximate sections once instead of repeating 'roughly' on every number. Do not hedge zero values.\n"
            "Logged intake is what is logged so far, not necessarily the final day. Do not frame broad macro ranges as a panic-level deficit.\n"
            "For Today-style coach prose: no Markdown bold, no emoji headers, and no decorative Markdown.\n"
            "If anything is missing, say that naturally. Do not invent facts.\n"
            "Return only the coach note.\n\n"
            "MODEL_FACING_COACH_FACTS_JSON:\n"
            f"{facts_json}\n"
        )
    else:
        packet_json = json.dumps(
            packet.to_dict(), indent=2, sort_keys=True, default=str
        )
        prompt = (
            f"{variant.writer_instruction}\n\n"
            "Use the structured data packet below.\n"
            "Write the full coach note; do not cut off mid-thought.\n"
            "Sound like a practical human coach with useful energy.\n"
            "Use display_ready values and display_phrase fields when quoting numbers.\n"
            "Use precision metadata: quote direct values directly when quote_style is direct; use about/roughly only when quote_style is hedged or value_precision is an estimate.\n"
            "If data is missing or uncertain, say that naturally.\n"
            "Do not invent facts.\n"
            "Return only the coach note.\n\n"
            "DATA_PACKET_JSON:\n"
            f"{packet_json}\n"
        )
    _assert_text_sanitized(prompt, label="full user-day provider input prompt")
    return prompt


def _extract_finish_reason(response: Any) -> str | None:
    reason = getattr(response, "finish_reason", None)
    if reason:
        return str(reason)
    for item in getattr(response, "output", []) or []:
        item_reason = getattr(item, "finish_reason", None) or getattr(
            item, "status", None
        )
        if item_reason:
            return str(item_reason)
    return None


def _extract_completion_status(response: Any) -> str | None:
    status = getattr(response, "status", None)
    if status:
        return str(status)
    return None


def _call_openai_full_user_day_note(
    model: str, prompt: str, timeout_seconds: float, env: Mapping[str, str]
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
        max_tokens = _max_output_tokens(env)
        response = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=max_tokens,
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
        finish_reason=_extract_finish_reason(response),
        completion_status=_extract_completion_status(response),
        max_output_tokens=_max_output_tokens(env),
    )


def _call_direct_ollama_full_user_day_note(
    model: str, prompt: str, timeout_seconds: float, env: Mapping[str, str]
) -> DailyCoachFullUserDayProviderCallResult:
    base_url = (env.get(OLLAMA_BASE_URL_ENV) or DEFAULT_OLLAMA_BASE_URL).rstrip("/")
    payload = {
        "model": model.removeprefix("ollama/"),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": _max_output_tokens(env)},
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
        raw_text=text,
        cost_estimate_basis="ollama_local_no_cost",
        finish_reason=str(response_payload.get("done_reason") or "complete"),
        completion_status="completed" if response_payload.get("done") else "unknown",
        max_output_tokens=_max_output_tokens(env),
    )


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
    prefer_decaged_prompt: bool = False,
) -> DailyCoachFullUserDayDraftResult:
    variant = _resolve_variant(variant_id)
    prompt = build_full_user_day_free_range_prompt(
        packet, variant.variant_id, prefer_decaged_prompt=prefer_decaged_prompt
    )
    if provider != PROVIDER_DETERMINISTIC and not allow_live_provider:
        return DailyCoachFullUserDayDraftResult(
            scenario_id=packet.scenario_id,
            user_id=packet.user_id,
            date=packet.date,
            provider=provider,
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
            finish_reason="complete",
            completion_status="completed",
            max_output_tokens=_max_output_tokens(environ),
        )
    else:
        generate = provider_generate or _provider_generate(provider)
        try:
            call_result = generate(
                model, prompt, _timeout_seconds(provider, environ), environ
            )
        except Exception as exc:  # noqa: BLE001
            return DailyCoachFullUserDayDraftResult(
                scenario_id=packet.scenario_id,
                user_id=packet.user_id,
                date=packet.date,
                provider=provider,
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
    reasons = _completion_truncation_reasons(
        call_result.raw_text,
        output_tokens=call_result.output_tokens,
        max_output_tokens=call_result.max_output_tokens,
        finish_reason=call_result.finish_reason,
    )
    return DailyCoachFullUserDayDraftResult(
        scenario_id=packet.scenario_id,
        user_id=packet.user_id,
        date=packet.date,
        provider=provider,
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
            "finish_reason": call_result.finish_reason,
            "completion_status": call_result.completion_status,
            "max_output_tokens": call_result.max_output_tokens,
            "truncated": bool(reasons),
            "truncation_heuristics": reasons,
            "raw_output_length": len(call_result.raw_text),
            "raw_provider_envelope_persisted": False,
            "repair_or_fallback_before_first_pass": False,
        },
    )


def write_daily_coach_full_user_day_artifacts(
    output_dir: Path,
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
    *,
    write_provider_payload_debug: bool = False,
    write_model_input_manifest: bool = False,
    write_precision_summary: bool = False,
    write_food_candidate_summary: bool = False,
    write_completion_diagnostics: bool = False,
    write_food_option_card: bool = False,
    write_macro_display_card: bool = False,
    write_ai_snack_candidates: bool = False,
    write_number_formatting_summary: bool = False,
    write_voice_style_findings: bool = False,
    write_model_facing_coach_facts: bool = False,
    write_decaging_summary: bool = False,
    write_backend_label_exposure_summary: bool = False,
    include_voice_variants: bool = False,
    prefer_decaged_prompt: bool = False,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_config = {
        "milestone": "daily_coach_free_range_prompt_payload_decaging_v4",
        "developer_only": True,
        "normal_today_unchanged": True,
        "run_count": len(results),
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "write_provider_payload_debug": write_provider_payload_debug,
        "write_model_input_manifest": write_model_input_manifest,
        "write_precision_summary": write_precision_summary,
        "write_food_candidate_summary": write_food_candidate_summary,
        "write_completion_diagnostics": write_completion_diagnostics,
        "write_food_option_card": write_food_option_card,
        "write_macro_display_card": write_macro_display_card,
        "write_ai_snack_candidates": write_ai_snack_candidates,
        "write_number_formatting_summary": write_number_formatting_summary,
        "write_voice_style_findings": write_voice_style_findings,
        "write_model_facing_coach_facts": write_model_facing_coach_facts,
        "write_decaging_summary": write_decaging_summary,
        "write_backend_label_exposure_summary": write_backend_label_exposure_summary,
        "include_voice_variants": include_voice_variants,
        "prefer_decaged_prompt": prefer_decaged_prompt,
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
    (output_dir / "voice_variant_summary.md").write_text(
        _render_voice_variant_summary(), encoding="utf-8"
    )
    (output_dir / "precision_usage_summary.md").write_text(
        _render_precision_usage_summary(results), encoding="utf-8"
    )
    (output_dir / "food_candidate_summary.md").write_text(
        _render_food_candidate_summary(results), encoding="utf-8"
    )
    (output_dir / "model_input_manifest.md").write_text(
        _render_model_input_manifest(results), encoding="utf-8"
    )
    (output_dir / "completion_diagnostics.md").write_text(
        _render_completion_diagnostics(results), encoding="utf-8"
    )
    _write_json(
        output_dir / "completion_diagnostics.json",
        _completion_diagnostics_payload(results),
    )
    (output_dir / "food_option_card.md").write_text(
        _render_food_option_card(results), encoding="utf-8"
    )
    _write_json(
        output_dir / "food_option_card.json", _food_option_card_payload(results)
    )
    (output_dir / "macro_display_card.md").write_text(
        _render_macro_display_card(results), encoding="utf-8"
    )
    _write_json(
        output_dir / "macro_display_card.json", _macro_display_card_payload(results)
    )
    (output_dir / "ai_snack_candidates.md").write_text(
        _render_ai_snack_candidates(results), encoding="utf-8"
    )
    _write_json(
        output_dir / "ai_snack_candidates.json", _ai_snack_candidates_payload(results)
    )
    (output_dir / "number_formatting_summary.md").write_text(
        _render_number_formatting_summary(results), encoding="utf-8"
    )
    (output_dir / "voice_style_findings.md").write_text(
        _render_voice_style_findings(results), encoding="utf-8"
    )
    if write_model_facing_coach_facts:
        (output_dir / "model_facing_coach_facts.md").write_text(
            _render_model_facing_coach_facts(results), encoding="utf-8"
        )
        _write_json(
            output_dir / "model_facing_coach_facts.json",
            _model_facing_coach_facts_payload(results),
        )
    if write_decaging_summary:
        (output_dir / "decaging_summary.md").write_text(
            _render_decaging_summary(results), encoding="utf-8"
        )
    if write_backend_label_exposure_summary:
        (output_dir / "backend_label_exposure_summary.md").write_text(
            _render_backend_label_exposure_summary(results), encoding="utf-8"
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


def _macro_display_card_from_targets(
    macro_targets: Mapping[str, Any],
) -> dict[str, Any]:
    rows = []
    for macro, data in macro_targets.items():
        if not isinstance(data, Mapping):
            continue
        display = (
            data.get("display")
            if isinstance(data.get("display"), Mapping)
            else _display_macro_payload(str(macro), data)
        )
        rows.append(_drop_unknowns({"macro": str(macro), **dict(display)}))
    return {
        "rows": rows,
        "display_policy": "compact values for coach/card use; avoid alarming exact deficit narration unless useful",
    }


def _food_option_card(foods: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    for food in foods[:15]:
        rows.append(
            _drop_unknowns(
                {
                    "option": food.get("plain_name_for_user")
                    or food.get("display_name"),
                    "serving": food.get("serving_size"),
                    "protein": food.get("protein_display"),
                    "calories": _strip_units(food.get("calories_display"), " calories"),
                    "carbs": food.get("carbs_display"),
                    "fat": food.get("fat_display"),
                    "display_phrase": food.get("display_phrase"),
                    "helps_with": food.get("helps_with"),
                }
            )
        )
    return {"rows": rows}


def _sum_numeric(values: Any) -> int | None:
    total = 0
    found = False
    for value in values:
        numeric = _optional_int(value)
        if numeric is None:
            continue
        total += numeric
        found = True
    return total if found else None


def _ai_snack_candidates(
    foods: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    by_name = {
        str(food.get("plain_name_for_user") or food.get("display_name")): food
        for food in foods
    }
    recipes = (
        ("Greek yogurt + banana", ("Greek yogurt", "banana"), "protein and carbs"),
        ("Tuna sandwich", ("canned tuna", "bread"), "protein and carbs"),
        (
            "Chicken breast + rice",
            ("cooked chicken breast", "rice"),
            "protein and carbs",
        ),
        ("Oatmeal + whey", ("oatmeal", "whey protein"), "protein and carbs"),
        ("Turkey wrap", ("turkey breast", "wrap"), "protein and carbs"),
        ("Salmon + potatoes", ("salmon", "potatoes"), "protein, calories, and carbs"),
    )
    snacks: list[dict[str, Any]] = []
    for snack_name, names, helps_with in recipes:
        parts = [by_name[name] for name in names if name in by_name]
        if len(parts) != len(names):
            continue
        calories = _sum_numeric(part.get("estimated_calories") for part in parts)
        protein = _sum_numeric(part.get("estimated_protein_g") for part in parts)
        carbs = _sum_numeric(part.get("estimated_carbs_g") for part in parts)
        fat = _sum_numeric(part.get("estimated_fat_g") for part in parts)
        precision = (
            "generic_estimate"
            if any(part.get("quote_style") == "hedged" for part in parts)
            else "database_calculated"
        )
        display_phrase = _meal_display_phrase(
            snack_name, protein, calories, carbs, fat, precision
        )
        snacks.append(
            _drop_unknowns(
                {
                    "snack_name": snack_name,
                    "foods_included": tuple(names),
                    "serving_notes": "combine the listed foods as one practical mini-meal option",
                    "estimated_calories": calories,
                    "estimated_protein_g": protein,
                    "estimated_carbs_g": carbs,
                    "estimated_fat_g": fat,
                    "helps_with": helps_with,
                    "value_precision": precision,
                    "quote_style": (
                        "hedged" if precision == "generic_estimate" else "direct"
                    ),
                    "display_phrase": display_phrase,
                    "display_policy": "aggregate ingredients before display; introduce meal options as approximate once rather than repeating roughly on every value",
                }
            )
        )
    return tuple(snacks)


def _number_formatting_summary_payload(
    nutrition: Mapping[str, Any],
    training: Mapping[str, Any],
    recovery: Mapping[str, Any],
    foods: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "raw_float_surface_allowed": False,
        "examples": {
            "calories": nutrition.get("calories_display"),
            "volume_load": training.get("total_volume_load_display"),
            "body_weight_change": recovery.get("weight_change_display"),
            "food": next(
                (
                    food.get("display_phrase")
                    for food in foods
                    if food.get("display_phrase")
                ),
                None,
            ),
        },
        "rules": (
            "whole calories displayed without .0",
            "grams displayed as whole g values",
            "pounds displayed as lb",
            "large training numbers use thousands separators",
        ),
    }


def _normalize_label(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).replace("_", " ").strip().lower()


def _strip_units(value: Any, suffix: str) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text.removesuffix(suffix)


def _user_facing_session_name(internal_name: str | None) -> str | None:
    if not internal_name:
        return None
    if "gradual progression" in internal_name.lower():
        return "strength session"
    return internal_name


def _session_type(internal_name: str | None) -> str | None:
    if not internal_name:
        return None
    lowered = internal_name.lower()
    if "strength" in lowered or "progression" in lowered:
        return "strength"
    return None


def _weight_change_is_anomalous(value: Any) -> bool:
    number = _optional_float(value)
    return number is not None and abs(number) >= 15


def _completion_truncation_reasons(
    text: str, *, output_tokens: Any, max_output_tokens: Any, finish_reason: Any
) -> list[str]:
    normalized = (text or "").strip()
    reasons: list[str] = []
    finish = str(finish_reason or "").lower()
    if finish in {"length", "max_tokens", "content_filter"}:
        reasons.append(f"finish_reason:{finish}")
    output_count = _optional_int(output_tokens)
    max_count = _optional_int(max_output_tokens)
    if (
        output_count is not None
        and max_count is not None
        and output_count >= int(max_count * 0.95)
    ):
        reasons.append("output_tokens_near_cap")
    if not normalized:
        return reasons
    if normalized[-1] not in ".!?)]}”’\n":
        reasons.append("no_terminal_punctuation")
    if re.search(r"(,|\band\b|\bor\b|\bwith\b|\bto\b|\bso\b)$", normalized.lower()):
        reasons.append("ends_mid_phrase")
    if normalized.count("|") >= 3 and not normalized.rstrip().endswith("|"):
        reasons.append("possible_unclosed_table_row")
    return sorted(set(reasons))


def _completion_truncated(
    text: str, *, output_tokens: Any, max_output_tokens: Any, finish_reason: Any
) -> bool:
    return bool(
        _completion_truncation_reasons(
            text,
            output_tokens=output_tokens,
            max_output_tokens=max_output_tokens,
            finish_reason=finish_reason,
        )
    )


def _completion_diagnostics_payload(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> dict[str, Any]:
    records = []
    for run in results:
        for variant in run.variants:
            metadata = variant.runtime_metadata
            records.append(
                {
                    "run_id": run.run_id,
                    "scenario_id": run.scenario_id,
                    "variant_id": variant.variant_id,
                    "repeat_index": variant.repeat_index,
                    "provider": variant.provider,
                    "finish_reason": metadata.get("finish_reason"),
                    "output_tokens": metadata.get("output_tokens"),
                    "max_output_tokens": metadata.get("max_output_tokens"),
                    "completion_status": metadata.get("completion_status"),
                    "truncated": bool(metadata.get("truncated")),
                    "truncation_heuristics": metadata.get("truncation_heuristics")
                    or [],
                    "skipped": variant.skipped,
                    "skip_reason": variant.skip_reason,
                }
            )
    expected = len(records)
    skipped = sum(1 for record in records if record["skipped"])
    truncated = sum(
        1 for record in records if record["truncated"] and not record["skipped"]
    )
    captured = sum(1 for record in records if not record["skipped"])
    complete = sum(
        1 for record in records if not record["skipped"] and not record["truncated"]
    )
    return {
        "summary": {
            "expected_drafts": expected,
            "captured_drafts": captured,
            "complete_drafts": complete,
            "truncated_drafts": truncated,
            "skipped_drafts": skipped,
            "acceptance_target": "0 truncated drafts",
        },
        "records": records,
        "developer_only": True,
        "post_hoc_only": True,
    }


def _render_completion_diagnostics(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    payload = _completion_diagnostics_payload(results)
    summary = payload["summary"]
    lines = [
        "# Completion Diagnostics",
        "",
        "Post-hoc only. First-pass drafts are not modified.",
        "",
        "## Summary",
        "",
        f"- expected_drafts: {summary['expected_drafts']}",
        f"- captured_drafts: {summary['captured_drafts']}",
        f"- complete_drafts: {summary['complete_drafts']}",
        f"- truncated_drafts: {summary['truncated_drafts']}",
        f"- skipped_drafts: {summary['skipped_drafts']}",
        f"- acceptance_target: {summary['acceptance_target']}",
        "",
        "## Records",
        "",
    ]
    for record in payload["records"]:
        lines.append(
            f"- {record['scenario_id']} / {record['variant_id']} / repeat {record['repeat_index']}: truncated={record['truncated']} skipped={record['skipped']} finish_reason={record['finish_reason'] or 'unknown'} output_tokens={record['output_tokens'] or 'unknown'} max_output_tokens={record['max_output_tokens'] or 'unknown'} reasons={record['truncation_heuristics'] or []}"
        )
    return "\n".join(lines)


def _food_option_card_payload(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> dict[str, Any]:
    return {
        "cards": [
            {
                "scenario_id": packet["scenario_id"],
                **(packet.get("food_option_card") or {}),
            }
            for packet in _packet_summaries(results)
        ]
    }


def _render_food_option_card(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Food Option Card",
        "",
        "| Option | Serving | Protein | Calories |",
        "|---|---:|---:|---:|",
    ]
    for card in _food_option_card_payload(results)["cards"]:
        for row in card.get("rows") or []:
            lines.append(
                f"| {row.get('option')} | {row.get('serving') or ''} | {row.get('protein') or ''} | {row.get('calories') or ''} |"
            )
    return "\n".join(lines) + "\n"


def _macro_display_card_payload(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> dict[str, Any]:
    return {
        "cards": [
            {
                "scenario_id": packet["scenario_id"],
                **(packet.get("macro_display_card") or {}),
            }
            for packet in _packet_summaries(results)
        ]
    }


def _render_macro_display_card(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Macro Display Card",
        "",
        "| Macro | Actual / Target | Status |",
        "|---|---:|---:|",
    ]
    for card in _macro_display_card_payload(results)["cards"]:
        for row in card.get("rows") or []:
            lines.append(
                f"| {row.get('label')} | {row.get('compact_display') or ''} | {row.get('status_display') or ''} |"
            )
    return "\n".join(lines) + "\n"


def _ai_snack_candidates_payload(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> dict[str, Any]:
    return {
        "snacks": [
            {
                "scenario_id": packet["scenario_id"],
                "snack_candidates": packet.get("ai_snack_candidates") or [],
                "skipped_reason": (
                    None
                    if packet.get("ai_snack_candidates")
                    else "insufficient candidate foods for safe snack combinations"
                ),
            }
            for packet in _packet_summaries(results)
        ]
    }


def _render_ai_snack_candidates(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# AI Snack Candidates",
        "",
        "Developer-only mini-meal candidates built only from known candidate foods.",
        "Numbers are approximate meal-option estimates; avoid repeating roughly on every macro.",
        "",
    ]
    for group in _ai_snack_candidates_payload(results)["snacks"]:
        lines.append(f"## {group['scenario_id']}")
        if group.get("skipped_reason"):
            lines.append(f"Skipped: {group['skipped_reason']}")
        else:
            lines.append("Approximate meal options:")
        for snack in group.get("snack_candidates") or []:
            lines.append(
                f"- {snack.get('display_phrase')} | foods={', '.join(snack.get('foods_included') or [])}"
            )
        lines.append("")
    return "\n".join(lines)


def _render_number_formatting_summary(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Number Formatting Summary",
        "",
        "Raw .0-style values should not be surfaced to coach prose when display-ready values are available.",
        "",
    ]
    for packet in _packet_summaries(results):
        formatting = packet.get("number_formatting") or {}
        lines.append(f"## {packet['scenario_id']}")
        for key, value in (formatting.get("examples") or {}).items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    return "\n".join(lines)


def _render_voice_style_findings(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
) -> str:
    lines = [
        "# Voice Style Findings",
        "",
        "Post-hoc voice notes; no first-pass text is changed.",
        "",
    ]
    for run in results:
        lines.append(f"## {run.scenario_id}")
        for variant in run.variants:
            draft = variant.first_pass_draft
            findings = []
            if "LET'S WORK" in draft.upper() or "LET’S WORK" in draft.upper():
                findings.append("strong_energy_signal")
            if "pain" in draft.lower() and "ignore" in draft.lower():
                findings.append("unsafe_pain_language_risk")
            lines.append(
                f"- {variant.variant_id} / repeat {variant.repeat_index}: {findings or ['no_special_voice_finding']}"
            )
        lines.append("")
    return "\n".join(lines)


def _render_pasteback_report(
    results: Sequence[DailyCoachFullUserDayTrialRunResult],
    write_provider_payload_debug: bool,
) -> str:
    lines = [
        "# Daily Coach Free-Range Prompt + Payload Decaging v4 — Pasteback Report",
        "",
        f"Provider payload debug written: {write_provider_payload_debug}",
        "Normal Today unchanged: True",
        "Provider promotion: False",
        "Repair/fallback before first-pass capture: False",
        "Known baseline drift: tests/test_daily_narrative_rich_day_service.py",
        "",
        "## Deterministic Provider Regression Status",
        "",
        "Deterministic provider is allowed without --allow-live-provider. External/live providers still require explicit opt-in.",
        "",
        "## Completion / Truncation Counts",
        "",
        _render_completion_diagnostics(results),
        "",
        "## Model-Facing Coach Facts Summary",
        "",
        _render_model_facing_coach_facts(results),
        "",
        "## Decaging Summary",
        "",
        _render_decaging_summary(results),
        "",
        "## Backend Label Exposure Summary",
        "",
        _render_backend_label_exposure_summary(results),
        "",
        "## Macro Range Framing Review",
        "",
        "Logged intake should be treated as what is logged so far, not a panic-level final deficit. Macro details belong in the compact macro card unless they support the coaching message.",
        "",
        "## Food candidate summary:",
        "",
        _render_food_candidate_summary(results),
        "",
        "## Food / Snack Formatting Review",
        "",
        _render_ai_snack_candidates(results),
        "",
        "## Roughly Overuse Review",
        "",
        "Meal-option numbers are introduced as approximate once. Zero values are not hedged.",
        "",
        "## Markdown Leak Review",
        "",
        "Today-style coach prose prompt says no Markdown bold, emoji headers, or decorative Markdown. Tables remain artifact/card only.",
        "",
        "## Backend-Bound Language Review",
        "",
        "See backend_label_exposure_summary.md for prompt/output exposure details.",
        "",
        "## Macro Display Card",
        "",
        _render_macro_display_card(results),
        "",
        "## Food Option Card",
        "",
        _render_food_option_card(results),
        "",
        "## Number Formatting Summary",
        "",
        _render_number_formatting_summary(results),
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
                    f"Snack candidates: {len(packet.ai_snack_candidates)}",
                    f"Set-level data available: {packet.training.get('set_level_data_available', False)}",
                    f"Workout/session naming: internal={packet.training.get('internal_workout_model') or 'none'}; user_facing={packet.training.get('user_facing_session_name') or 'none'}",
                    f"Weight trend handling: surface={packet.recovery.get('weight_trend_surface_to_coach', True)}; confidence={packet.recovery.get('weight_trend_confidence', 'unknown')}",
                    "",
                ]
            )
        direct_or_hype = [
            variant
            for variant in run.variants
            if "direct" in str(variant.variant_id)
            or "hypeman" in str(variant.variant_id)
        ]
        if direct_or_hype:
            lines.extend(["## Best Direct / Hypeman Outputs", ""])
            for variant in direct_or_hype[:4]:
                lines.extend(
                    [
                        f"### {variant.variant_id} / repeat {variant.repeat_index}",
                        "",
                        variant.first_pass_draft or "(no draft)",
                        "",
                    ]
                )
        best = _select_best_variant(run)
        if best:
            lines.extend(
                [
                    f"Best voice variant: {best.variant_id} / repeat {best.repeat_index}",
                    "",
                    "Best exact first-pass note:",
                    "",
                    best.first_pass_draft or "(no draft)",
                    "",
                ]
            )
    lines.extend(
        ["## Voice Style Findings", "", _render_voice_style_findings(results), ""]
    )
    lines.extend(["## Claim Risk Summary", "", _render_claim_risk_summary(results), ""])
    lines.extend(
        ["## Consistency Summary", "", _render_consistency_summary(results), ""]
    )
    lines.extend(
        ["## Token / Cost Summary", "", _render_token_cost_telemetry(results), ""]
    )
    lines.extend(
        [
            "## Artifact Safety",
            "",
            _render_artifact_safety_summary(results, write_provider_payload_debug),
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
                    "model_facing_coach_facts": (
                        _model_facing_coach_facts(packet) if packet else None
                    ),
                    "backend_label_exposure": _backend_label_exposure_payload(
                        [
                            DailyCoachFullUserDayTrialRunResult(
                                run_id=run.run_id,
                                scenario_id=run.scenario_id,
                                user_id=run.user_id,
                                date=run.date,
                                provider=run.provider,
                                model=run.model,
                                variants=(variant,),
                                baseline_drift=run.baseline_drift,
                            )
                        ]
                    )["records"][0],
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
                    "food_candidate_count": (
                        len(packet.food_candidates) if packet else 0
                    ),
                    "ai_snack_candidate_count": (
                        len(packet.ai_snack_candidates) if packet else 0
                    ),
                    "macro_display_card": packet.macro_display_card if packet else {},
                    "food_option_card": packet.food_option_card if packet else {},
                    "completion_diagnostics": variant.runtime_metadata.get(
                        "truncation_heuristics"
                    )
                    or [],
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
                    "precision_summary": (
                        _precision_debug_summary(packet) if packet else {}
                    ),
                    "set_level_data_available": (
                        packet.training.get("set_level_data_available")
                        if packet
                        else False
                    ),
                    "user_health_state_included_fields": (
                        packet.user_health_state_field_coverage.get("included_fields")
                        if packet
                        else []
                    ),
                    "user_health_state_omitted_fields": (
                        packet.user_health_state_field_coverage.get("omitted_fields")
                        if packet
                        else {}
                    ),
                    "redaction_safety_summary": {
                        "raw_provider_envelope_persisted": False,
                        "secrets_persisted": False,
                        "raw_db_rows_persisted": False,
                    },
                }
            )
    return {
        "milestone": "daily_coach_free_range_prompt_payload_decaging_v4",
        "debug_artifact_opt_in": True,
        "records": rows,
    }


def _build_run_id(provider: str, scenario_id: str) -> str:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    safe_scenario = re.sub(r"[^a-zA-Z0-9_-]+", "_", scenario_id)
    safe_time = timestamp.replace(":", "").replace("+", "z")
    return (
        "daily_coach_free_range_prompt_payload_decaging_v4_"
        f"{safe_scenario}_{provider}_{safe_time}"
    )
