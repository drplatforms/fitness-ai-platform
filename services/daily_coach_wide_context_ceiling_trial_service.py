from __future__ import annotations

import csv
import json
import os
import re
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from models.daily_coach_natural_draft_audit_models import (
    AddressingPolicy,
    ApprovedCoachBrief,
    NaturalCoachDraft,
)
from models.daily_coach_wide_context_models import (
    DailyCoachWideContextDraftResult,
    DailyCoachWideContextPacket,
    DailyCoachWideContextPromptVariant,
    DailyCoachWideContextProviderCallResult,
    DailyCoachWideContextTrialRunResult,
)
from services.daily_coach_approved_brief_service import build_approved_coach_brief
from services.daily_coach_natural_draft_audit_service import (
    get_daily_coach_natural_draft_scenario,
    list_daily_coach_natural_draft_scenarios,
    run_daily_coach_natural_draft_audit_scenario,
)
from services.daily_coach_natural_draft_service import write_natural_coach_draft
from services.daily_coach_synthesis_service import build_daily_coach_synthesis
from services.daily_coach_value_narrative_service import (
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OPENAI_BASE_URL,
    OLLAMA_BASE_URL_ENV,
    OPENAI_API_KEY_ENV,
    OPENAI_BASE_URL_ENV,
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
    build_daily_coach_value_aware_provider_context,
)
from services.user_state_service import build_user_health_state

DEFAULT_WIDE_CONTEXT_OUTPUT_DIR = (
    "docs/provider_trials/daily_coach_wide_context_uncaged_gpt55_ceiling_trial_v1"
)
DEFAULT_WIDE_CONTEXT_MODEL = "gpt-5.5"
DEFAULT_WIDE_CONTEXT_PROVIDER = PROVIDER_DETERMINISTIC
WIDE_CONTEXT_PROVIDER_ENV = "DAILY_COACH_WIDE_CONTEXT_PROVIDER"
WIDE_CONTEXT_MODEL_ENV = "DAILY_COACH_WIDE_CONTEXT_MODEL"
WIDE_CONTEXT_OPENAI_TIMEOUT_ENV = "DAILY_COACH_WIDE_CONTEXT_OPENAI_TIMEOUT_SECONDS"
WIDE_CONTEXT_DIRECT_OLLAMA_TIMEOUT_ENV = (
    "DAILY_COACH_WIDE_CONTEXT_DIRECT_OLLAMA_TIMEOUT_SECONDS"
)
WIDE_CONTEXT_INPUT_COST_PER_MILLION_ENV = (
    "DAILY_COACH_WIDE_CONTEXT_INPUT_COST_PER_MILLION"
)
WIDE_CONTEXT_OUTPUT_COST_PER_MILLION_ENV = (
    "DAILY_COACH_WIDE_CONTEXT_OUTPUT_COST_PER_MILLION"
)
SUPPORTED_WIDE_CONTEXT_PROVIDERS = (
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
    "architecture_decision": "document_do_not_block_ceiling_trial",
    "patched_in_this_milestone": False,
}

WideContextProviderCallable = Callable[
    [str, str, float, Mapping[str, str]], DailyCoachWideContextProviderCallResult
]


class DailyCoachWideContextCeilingTrialError(ValueError):
    """Raised when wide-context ceiling-trial inputs are invalid."""


def list_daily_coach_wide_context_scenarios() -> list[dict[str, Any]]:
    return list_daily_coach_natural_draft_scenarios()


def list_daily_coach_wide_context_prompt_variants() -> list[dict[str, Any]]:
    return [variant.to_dict() for variant in _prompt_variants().values()]


def build_daily_coach_wide_context_packet(
    *,
    user_id: int,
    target_date: str,
    scenario_id: str,
    brief: ApprovedCoachBrief | None = None,
    synthesis: Any | None = None,
    health_state: Any | None = None,
    value_context: Mapping[str, Any] | None = None,
) -> DailyCoachWideContextPacket:
    """Build a rich sanitized context packet from backend-approved sources.

    The packet is deliberately wider than ApprovedCoachBrief, but it still avoids
    raw DB rows, raw notes, secrets, raw source payloads, and provider envelopes.
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

    nutrition_context = _public_safe_mapping(
        resolved_value_context.get("approved_nutrition") or {}
    )
    training_context = _training_context(resolved_synthesis, resolved_health_state)
    recovery_context = _recovery_context(resolved_synthesis, resolved_health_state)
    packet = DailyCoachWideContextPacket(
        packet_version="daily_coach_wide_context_uncaged_gpt55_ceiling_trial_v1",
        user_id=user_id,
        date=target_date,
        scenario_id=scenario_id,
        day_context={
            "scenario": getattr(resolved_synthesis, "scenario", scenario_id),
            "confidence": getattr(resolved_synthesis, "confidence", "Unknown"),
            "summary": getattr(resolved_synthesis, "today_summary", None),
            "recommended_focus": getattr(resolved_synthesis, "recommended_focus", None),
            "reason_codes": list(getattr(resolved_synthesis, "reason_codes", []))[:12],
            "limitations": list(getattr(resolved_synthesis, "limitations", []))[:8],
        },
        available_daily_data=_available_data(
            nutrition_context, training_context, recovery_context
        ),
        missing_daily_data=_missing_data(
            nutrition_context, training_context, recovery_context
        ),
        profile_context=_profile_context(resolved_health_state),
        nutrition_context=nutrition_context,
        food_choices=tuple(_food_choices(resolved_brief, resolved_value_context)),
        training_context=training_context,
        recovery_context=recovery_context,
        allowed_interpretations=tuple(
            _bounded_strings(resolved_brief.approved_interpretations, limit=10)
        ),
        blocked_interpretations=(
            "Do not invent foods, serving sizes, timing, targets, workouts, causes, or medical claims.",
            "Do not call incomplete logging low or zero intake unless backend context explicitly says so.",
            "Do not claim overtraining, stalled fat loss, injury, disease, or metabolic damage.",
            "Do not use internal process wording in the user-facing coach note.",
        ),
        display_policy={
            "addressing": resolved_brief.addressing_policy.to_dict(),
            "servings": "only when explicitly present in the food choice",
            "food_names": "use friendly food names when provided",
            "uncertainty": "say less when context is thin or confidence is limited",
            "raw_rows": "not included",
            "provider_envelopes": "not included",
        },
        context_sources=(
            "DailyCoachSynthesis",
            "UserHealthState",
            "DailyCoachValueAwareProviderContext",
            "ApprovedCoachBrief",
        ),
    )
    _assert_packet_sanitized(packet)
    return packet


def build_wide_context_writer_prompt(
    packet: DailyCoachWideContextPacket,
    variant_id: str,
) -> str:
    variant = _resolve_variant(variant_id)
    if variant.variant_id == "current_narrow_path":
        return ""
    writer_context = _render_packet_for_writer(packet)
    return (
        f"{variant.writer_instruction}\n\n"
        "Factual boundaries:\n"
        "- Use only the context below.\n"
        "- Be specific only where the context supports it.\n"
        "- Say less when context is thin, missing, or limited-confidence.\n"
        "- Do not invent foods, servings, timing, targets, workouts, causes, medical claims, or user data.\n"
        "- Return only the coach note. No JSON, markdown table, labels, or explanation of your process.\n\n"
        f"{writer_context}\n"
    )


def run_daily_coach_wide_context_ceiling_trial_scenario(
    *,
    scenario_id: str,
    provider: str = DEFAULT_WIDE_CONTEXT_PROVIDER,
    model: str | None = None,
    variants: Sequence[str] | None = None,
    allow_live_provider: bool = False,
    output_dir: Path | None = None,
    environ: Mapping[str, str] | None = None,
    provider_generate: WideContextProviderCallable | None = None,
) -> DailyCoachWideContextTrialRunResult:
    scenario = get_daily_coach_natural_draft_scenario(scenario_id)
    env = dict(os.environ if environ is None else environ)
    resolved_provider = _configured_provider(provider, env)
    if resolved_provider not in SUPPORTED_WIDE_CONTEXT_PROVIDERS:
        resolved_provider = PROVIDER_DETERMINISTIC
    resolved_model = (
        model or env.get(WIDE_CONTEXT_MODEL_ENV) or DEFAULT_WIDE_CONTEXT_MODEL
    )
    selected_variants = tuple(variants or _default_variant_order())
    run_id = _build_run_id(resolved_provider, scenario_id)

    user_id = int(scenario["user_id"])
    target_date = str(scenario["target_date"])
    try:
        packet = build_daily_coach_wide_context_packet(
            user_id=user_id,
            target_date=target_date,
            scenario_id=scenario_id,
        )
    except Exception as exc:  # noqa: BLE001 - developer trial records setup failure safely
        result = _skipped_setup_run(
            run_id=run_id,
            scenario_id=scenario_id,
            user_id=user_id,
            target_date=target_date,
            provider=resolved_provider,
            model=resolved_model,
            variants=selected_variants,
            reason=f"wide_context_packet_build_failed:{_safe_error(exc)}",
        )
        if output_dir:
            write_wide_context_ceiling_trial_artifacts(output_dir, [result])
        return result

    deterministic_baseline = _deterministic_baseline_note(packet)
    current_narrow = _current_narrow_path_output(
        scenario_id=scenario_id,
        provider=resolved_provider,
        model=resolved_model,
        allow_live_provider=allow_live_provider,
        environ=env,
    )
    results = tuple(
        _run_variant(
            packet=packet,
            variant_id=variant_id,
            provider=resolved_provider,
            model=resolved_model,
            deterministic_baseline=deterministic_baseline,
            current_narrow_path_output=current_narrow,
            allow_live_provider=allow_live_provider,
            environ=env,
            provider_generate=provider_generate,
        )
        for variant_id in selected_variants
    )
    result = DailyCoachWideContextTrialRunResult(
        run_id=run_id,
        scenario_id=scenario_id,
        user_id=user_id,
        date=target_date,
        provider=resolved_provider,  # type: ignore[arg-type]
        model=resolved_model,
        variants=results,
        baseline_drift=dict(BASELINE_DRIFT),
        runtime_metadata={
            "developer_only": True,
            "normal_today_unchanged": True,
            "ceiling_trial_only": True,
            "provider_promotion": False,
            "raw_provider_envelope_persisted": False,
            "wide_context_packet_version": packet.packet_version,
            "variant_count": len(results),
        },
    )
    _assert_run_sanitized(result)
    if output_dir:
        write_wide_context_ceiling_trial_artifacts(output_dir, [result])
    return result


def run_daily_coach_wide_context_ceiling_trial_matrix(
    *,
    scenarios: Sequence[str],
    provider: str = DEFAULT_WIDE_CONTEXT_PROVIDER,
    model: str | None = None,
    variants: Sequence[str] | None = None,
    allow_live_provider: bool = False,
    output_dir: Path,
    environ: Mapping[str, str] | None = None,
    provider_generate: WideContextProviderCallable | None = None,
) -> list[DailyCoachWideContextTrialRunResult]:
    selected_scenarios = list(scenarios) or ["rich_nutrition_training_recovery"]
    results = [
        run_daily_coach_wide_context_ceiling_trial_scenario(
            scenario_id=scenario_id,
            provider=provider,
            model=model,
            variants=variants,
            allow_live_provider=allow_live_provider,
            environ=environ,
            provider_generate=provider_generate,
        )
        for scenario_id in selected_scenarios
    ]
    write_wide_context_ceiling_trial_artifacts(output_dir, results)
    return results


def write_wide_context_ceiling_trial_artifacts(
    output_dir: Path,
    results: Sequence[DailyCoachWideContextTrialRunResult],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_config = {
        "milestone": "daily_coach_wide_context_uncaged_gpt55_ceiling_trial_v1",
        "developer_only": True,
        "normal_today_unchanged": True,
        "run_count": len(results),
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "baseline_drift": dict(BASELINE_DRIFT),
    }
    (output_dir / "run_config.json").write_text(
        json.dumps(run_config, indent=2, sort_keys=True), encoding="utf-8"
    )
    (output_dir / "wide_context_packet_summary.json").write_text(
        json.dumps(_context_packet_summary(results), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "prompt_variants.md").write_text(
        _render_prompt_variants(), encoding="utf-8"
    )
    (output_dir / "first_pass_drafts.md").write_text(
        _render_first_pass_drafts(results), encoding="utf-8"
    )
    (output_dir / "side_by_side_comparison.md").write_text(
        _render_side_by_side_comparison(results), encoding="utf-8"
    )
    (output_dir / "review_summary.md").write_text(
        _render_review_summary(results), encoding="utf-8"
    )
    (output_dir / "token_cost_telemetry.md").write_text(
        _render_token_cost_telemetry(results), encoding="utf-8"
    )
    _write_telemetry_csv(output_dir / "token_cost_telemetry.csv", results)
    (output_dir / "scoring_template.md").write_text(
        _render_scoring_template(results), encoding="utf-8"
    )
    (output_dir / "baseline_drift.md").write_text(
        _render_baseline_drift(), encoding="utf-8"
    )
    (output_dir / "artifact_safety_summary.md").write_text(
        _render_artifact_safety_summary(results), encoding="utf-8"
    )
    serialized = "\n".join(
        path.read_text(encoding="utf-8")
        for path in output_dir.iterdir()
        if path.is_file()
    )
    _assert_text_sanitized(serialized, label="wide context ceiling trial artifacts")


def _skipped_setup_run(
    *,
    run_id: str,
    scenario_id: str,
    user_id: int,
    target_date: str,
    provider: str,
    model: str | None,
    variants: Sequence[str],
    reason: str,
) -> DailyCoachWideContextTrialRunResult:
    skipped_variants = tuple(
        DailyCoachWideContextDraftResult(
            scenario_id=scenario_id,
            user_id=user_id,
            date=target_date,
            provider=provider,  # type: ignore[arg-type]
            model=model,
            variant_id=_resolve_variant(variant_id).variant_id,
            skipped=True,
            skip_reason=reason,
            first_pass_draft="",
            writer_prompt=None,
            deterministic_baseline="",
            current_narrow_path_output=None,
            wide_context_packet=None,
            runtime_metadata={
                "developer_only": True,
                "normal_today_unchanged": True,
                "setup_failed": True,
                "skip_reason": reason,
            },
        )
        for variant_id in variants
    )
    return DailyCoachWideContextTrialRunResult(
        run_id=run_id,
        scenario_id=scenario_id,
        user_id=user_id,
        date=target_date,
        provider=provider,  # type: ignore[arg-type]
        model=model,
        variants=skipped_variants,
        baseline_drift=dict(BASELINE_DRIFT),
        runtime_metadata={
            "developer_only": True,
            "normal_today_unchanged": True,
            "ceiling_trial_only": True,
            "provider_promotion": False,
            "setup_failed": True,
            "skip_reason": reason,
        },
    )


def _run_variant(
    *,
    packet: DailyCoachWideContextPacket,
    variant_id: str,
    provider: str,
    model: str,
    deterministic_baseline: str,
    current_narrow_path_output: str | None,
    allow_live_provider: bool,
    environ: Mapping[str, str],
    provider_generate: WideContextProviderCallable | None,
) -> DailyCoachWideContextDraftResult:
    variant = _resolve_variant(variant_id)
    if variant.variant_id == "current_narrow_path":
        return DailyCoachWideContextDraftResult(
            scenario_id=packet.scenario_id,
            user_id=packet.user_id,
            date=packet.date,
            provider=provider,  # type: ignore[arg-type]
            model=model,
            variant_id=variant.variant_id,
            skipped=current_narrow_path_output is None,
            skip_reason=None
            if current_narrow_path_output
            else "current_narrow_unavailable",
            first_pass_draft=current_narrow_path_output or "",
            writer_prompt=None,
            deterministic_baseline=deterministic_baseline,
            current_narrow_path_output=current_narrow_path_output,
            wide_context_packet=None,
            runtime_metadata={
                "developer_only": True,
                "normal_today_unchanged": True,
                "uses_existing_narrow_path": True,
                "wide_context_writer_attempted": False,
            },
        )

    prompt = build_wide_context_writer_prompt(packet, variant.variant_id)
    if provider != PROVIDER_DETERMINISTIC and not allow_live_provider:
        return DailyCoachWideContextDraftResult(
            scenario_id=packet.scenario_id,
            user_id=packet.user_id,
            date=packet.date,
            provider=provider,  # type: ignore[arg-type]
            model=model,
            variant_id=variant.variant_id,
            skipped=True,
            skip_reason="live_provider_not_allowed",
            first_pass_draft="",
            writer_prompt=prompt,
            deterministic_baseline=deterministic_baseline,
            current_narrow_path_output=current_narrow_path_output,
            wide_context_packet=packet,
            runtime_metadata={
                "developer_only": True,
                "normal_today_unchanged": True,
                "allow_live_provider": False,
                "prompt_character_count": len(prompt),
                "provider_attempted": False,
                "token_telemetry_available": False,
            },
        )

    if provider == PROVIDER_DETERMINISTIC:
        call_result = DailyCoachWideContextProviderCallResult(
            raw_text=_deterministic_wide_context_draft(packet, variant.variant_id),
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            cached_input_tokens=None,
            estimated_cost_usd=None,
            cost_estimate_basis="deterministic_no_provider_cost",
        )
    else:
        generate = provider_generate or _provider_generate(provider)
        try:
            call_result = generate(
                model, prompt, _timeout_seconds(provider, environ), environ
            )
        except Exception as exc:  # noqa: BLE001 - developer trial captures failure safely
            return DailyCoachWideContextDraftResult(
                scenario_id=packet.scenario_id,
                user_id=packet.user_id,
                date=packet.date,
                provider=provider,  # type: ignore[arg-type]
                model=model,
                variant_id=variant.variant_id,
                skipped=True,
                skip_reason=_safe_error(exc),
                first_pass_draft="",
                writer_prompt=prompt,
                deterministic_baseline=deterministic_baseline,
                current_narrow_path_output=current_narrow_path_output,
                wide_context_packet=packet,
                runtime_metadata={
                    "developer_only": True,
                    "normal_today_unchanged": True,
                    "allow_live_provider": allow_live_provider,
                    "prompt_character_count": len(prompt),
                    "provider_attempted": True,
                    "provider_error": _safe_error(exc),
                    "token_telemetry_available": False,
                },
            )
    return DailyCoachWideContextDraftResult(
        scenario_id=packet.scenario_id,
        user_id=packet.user_id,
        date=packet.date,
        provider=provider,  # type: ignore[arg-type]
        model=model,
        variant_id=variant.variant_id,
        skipped=False,
        skip_reason=None,
        first_pass_draft=call_result.raw_text.strip(),
        writer_prompt=prompt,
        deterministic_baseline=deterministic_baseline,
        current_narrow_path_output=current_narrow_path_output,
        wide_context_packet=packet,
        runtime_metadata={
            "developer_only": True,
            "normal_today_unchanged": True,
            "allow_live_provider": allow_live_provider,
            "prompt_character_count": len(prompt),
            "provider_attempted": provider != PROVIDER_DETERMINISTIC,
            "input_tokens": call_result.input_tokens,
            "output_tokens": call_result.output_tokens,
            "total_tokens": call_result.total_tokens,
            "cached_input_tokens": call_result.cached_input_tokens,
            "estimated_cost_usd": call_result.estimated_cost_usd,
            "cost_estimate_basis": call_result.cost_estimate_basis,
            "token_telemetry_available": call_result.total_tokens is not None,
            "raw_output_length": len(call_result.raw_text),
            "raw_provider_envelope_persisted": False,
        },
    )


def _render_packet_for_writer(packet: DailyCoachWideContextPacket) -> str:
    sections = [
        "Useful context for today:",
        f"- Scenario: {packet.day_context.get('scenario') or packet.scenario_id}",
        f"- Confidence: {packet.day_context.get('confidence') or 'Unknown'}",
        f"- Summary: {packet.day_context.get('summary') or 'No summary available.'}",
        f"- Main focus: {packet.day_context.get('recommended_focus') or 'Keep the next action simple and verifiable.'}",
    ]
    if packet.profile_context:
        sections.append("\nProfile context:")
        sections.extend(_render_mapping_lines(packet.profile_context))
    if packet.recovery_context:
        sections.append("\nRecovery context:")
        sections.extend(_render_mapping_lines(packet.recovery_context))
    if packet.training_context:
        sections.append("\nTraining context:")
        sections.extend(_render_mapping_lines(packet.training_context))
    if packet.nutrition_context:
        sections.append("\nNutrition context:")
        sections.extend(_render_mapping_lines(packet.nutrition_context, max_depth=2))
    if packet.food_choices:
        sections.append("\nFood choices that may be mentioned if relevant:")
        for choice in packet.food_choices[:5]:
            name = choice.get("friendly_name") or choice.get("canonical_name")
            reason = choice.get("macro_reason") or choice.get("suggestion_summary")
            serving = choice.get("serving_display") or choice.get("suggested_grams")
            parts = [str(name)] if name else []
            if reason:
                parts.append(f"reason: {reason}")
            if serving:
                parts.append(f"amount: {serving}")
            if parts:
                sections.append(f"- {'; '.join(parts)}")
    if packet.allowed_interpretations:
        sections.append("\nInterpretations you may use:")
        sections.extend(f"- {item}" for item in packet.allowed_interpretations[:8])
    if packet.blocked_interpretations:
        sections.append("\nDo not say:")
        sections.extend(f"- {item}" for item in packet.blocked_interpretations)
    if packet.missing_daily_data:
        sections.append("\nMissing or uncertain data:")
        sections.extend(f"- {item}" for item in packet.missing_daily_data)
    return "\n".join(sections)


def _render_mapping_lines(
    value: Mapping[str, Any], *, max_depth: int = 1, depth: int = 0
) -> list[str]:
    lines: list[str] = []
    for key, item in value.items():
        if item in (None, "", "Unknown"):
            continue
        label = str(key).replace("_", " ")
        if isinstance(item, Mapping) and depth < max_depth:
            lines.append(f"- {label}:")
            for child in _render_mapping_lines(
                item, max_depth=max_depth, depth=depth + 1
            ):
                lines.append(f"  {child}")
        elif isinstance(item, list | tuple):
            if item:
                lines.append(
                    f"- {label}: {', '.join(str(child) for child in item[:5])}"
                )
        else:
            lines.append(f"- {label}: {item}")
    return lines


def _provider_generate(provider: str) -> WideContextProviderCallable:
    if provider == PROVIDER_OPENAI:
        return _call_openai_wide_context_note
    if provider == PROVIDER_DIRECT_OLLAMA:
        return _call_direct_ollama_wide_context_note
    raise DailyCoachWideContextCeilingTrialError(f"unsupported_provider:{provider}")


def _call_openai_wide_context_note(
    model: str,
    prompt: str,
    timeout_seconds: float,
    env: Mapping[str, str],
) -> DailyCoachWideContextProviderCallResult:
    api_key = env.get(OPENAI_API_KEY_ENV)
    if not api_key:
        raise DailyCoachWideContextCeilingTrialError("openai_missing_api_key")
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
    except Exception as exc:  # pragma: no cover - exercised with mocks/manual runs
        raise DailyCoachWideContextCeilingTrialError(
            f"openai_provider_error:{_safe_error(exc)}"
        ) from exc
    text = _extract_openai_text(response)
    if not text:
        raise DailyCoachWideContextCeilingTrialError("openai_missing_response_text")
    usage = _extract_usage(response)
    return DailyCoachWideContextProviderCallResult(
        raw_text=text,
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
        total_tokens=usage.get("total_tokens"),
        cached_input_tokens=usage.get("cached_input_tokens"),
        estimated_cost_usd=_estimate_cost_usd(usage, env),
        cost_estimate_basis=_cost_estimate_basis(usage, env),
    )


def _call_direct_ollama_wide_context_note(
    model: str,
    prompt: str,
    timeout_seconds: float,
    env: Mapping[str, str],
) -> DailyCoachWideContextProviderCallResult:
    base_url = (env.get(OLLAMA_BASE_URL_ENV) or DEFAULT_OLLAMA_BASE_URL).rstrip("/")
    payload = {
        "model": _normalize_ollama_model(model),
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
    raw_text = response_payload.get("response")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise DailyCoachWideContextCeilingTrialError("direct_ollama_missing_response")
    return DailyCoachWideContextProviderCallResult(
        raw_text=raw_text,
        input_tokens=_optional_int(response_payload.get("prompt_eval_count")),
        output_tokens=_optional_int(response_payload.get("eval_count")),
        total_tokens=_sum_optional_ints(
            response_payload.get("prompt_eval_count"),
            response_payload.get("eval_count"),
        ),
        cached_input_tokens=None,
        estimated_cost_usd=0.0,
        cost_estimate_basis="local_ollama_no_api_cost",
    )


def _extract_openai_text(response: Any) -> str | None:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    output = getattr(response, "output", None)
    if not isinstance(output, list):
        return output_text if isinstance(output_text, str) else None
    text_parts: list[str] = []
    for item in output:
        content = getattr(item, "content", None)
        if not isinstance(content, list):
            continue
        for part in content:
            text = getattr(part, "text", None)
            if isinstance(text, str):
                text_parts.append(text)
    return "".join(text_parts).strip() or None


def _extract_usage(response: Any) -> dict[str, int | None]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "cached_input_tokens": None,
        }
    if isinstance(usage, Mapping):
        data = usage
    else:
        data = {
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
            "input_tokens_details": getattr(usage, "input_tokens_details", None),
        }
    cached = None
    details = data.get("input_tokens_details")
    if isinstance(details, Mapping):
        cached = _optional_int(details.get("cached_tokens"))
    else:
        cached = _optional_int(getattr(details, "cached_tokens", None))
    return {
        "input_tokens": _optional_int(data.get("input_tokens")),
        "output_tokens": _optional_int(data.get("output_tokens")),
        "total_tokens": _optional_int(data.get("total_tokens")),
        "cached_input_tokens": cached,
    }


def _estimate_cost_usd(
    usage: Mapping[str, int | None], env: Mapping[str, str]
) -> float | None:
    input_cost = _optional_float(env.get(WIDE_CONTEXT_INPUT_COST_PER_MILLION_ENV))
    output_cost = _optional_float(env.get(WIDE_CONTEXT_OUTPUT_COST_PER_MILLION_ENV))
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if (
        input_cost is None
        or output_cost is None
        or input_tokens is None
        or output_tokens is None
    ):
        return None
    return round(
        ((input_tokens / 1_000_000) * input_cost)
        + ((output_tokens / 1_000_000) * output_cost),
        6,
    )


def _cost_estimate_basis(
    usage: Mapping[str, int | None], env: Mapping[str, str]
) -> str | None:
    if usage.get("total_tokens") is None:
        return "provider_usage_unavailable"
    if env.get(WIDE_CONTEXT_INPUT_COST_PER_MILLION_ENV) and env.get(
        WIDE_CONTEXT_OUTPUT_COST_PER_MILLION_ENV
    ):
        return "env_configured_cost_per_million_tokens"
    return "token_counts_available_cost_not_estimated"


def _current_narrow_path_output(
    *,
    scenario_id: str,
    provider: str,
    model: str,
    allow_live_provider: bool,
    environ: Mapping[str, str],
) -> str | None:
    try:
        result = run_daily_coach_natural_draft_audit_scenario(
            scenario_id=scenario_id,
            provider=provider,
            model=model,
            allow_live_provider=allow_live_provider,
            environ=environ,
        )
    except Exception:
        return None
    draft = result.draft or result.final_copy or result.deterministic_fallback
    if draft is None:
        return None
    return _draft_to_text(draft)


def _deterministic_baseline_note(packet: DailyCoachWideContextPacket) -> str:
    try:
        scenario = get_daily_coach_natural_draft_scenario(packet.scenario_id)
        brief = build_approved_coach_brief(
            user_id=int(scenario["user_id"]),
            target_date=str(scenario["target_date"]),
            scenario_id=packet.scenario_id,
            addressing_policy=AddressingPolicy(),
        )
        draft = write_natural_coach_draft(brief, provider=PROVIDER_DETERMINISTIC)
        return _draft_to_text(draft)
    except Exception:
        return _deterministic_wide_context_draft(packet, "wide_context_minimal_prompt")


def _deterministic_wide_context_draft(
    packet: DailyCoachWideContextPacket, variant_id: str
) -> str:
    nutrition = packet.nutrition_context
    training = packet.training_context
    recovery = packet.recovery_context
    food = packet.food_choices[0] if packet.food_choices else None
    summary = str(
        packet.day_context.get("summary") or "Use the clearest available signal today."
    )
    training_line = str(
        training.get("workout_guidance")
        or training.get("training_signal")
        or "Keep training controlled."
    )
    recovery_line = str(
        recovery.get("recovery_signal") or "Use recovery context cautiously."
    )
    logging = str(
        nutrition.get("logging_completeness") or "unknown logging completeness"
    )
    food_line = ""
    if food:
        name = food.get("friendly_name") or food.get("canonical_name")
        reason = food.get("macro_reason") or "the relevant nutrition gap"
        food_line = (
            f" For food, {name} is the backed option if {reason} still matters today."
        )
    prefix = "" if variant_id == "wide_context_no_style_guidance" else "Today, "
    return (
        f"{prefix}{summary} {training_line} {recovery_line} "
        f"Nutrition logging is {logging}, so keep conclusions matched to the data."
        f"{food_line}"
    ).strip()


def _draft_to_text(draft: NaturalCoachDraft) -> str:
    return f"{draft.headline}\n\n{draft.body}".strip()


def _profile_context(health_state: Any) -> dict[str, Any]:
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


def _training_context(synthesis: Any, health_state: Any) -> dict[str, Any]:
    training_state = getattr(health_state, "training_state", None)
    return _drop_unknowns(
        {
            "training_signal": getattr(synthesis, "training_signal", None),
            "workout_guidance": getattr(synthesis, "workout_guidance", None),
            "execution_context": getattr(synthesis, "execution_context", None),
            "plan_fit_note": getattr(synthesis, "plan_fit_note", None),
            "workout_summary": getattr(training_state, "workout_summary", None),
            "workout_count": getattr(training_state, "workout_count", None),
            "adherence_level": getattr(training_state, "adherence_level", None),
            "training_trend": getattr(training_state, "training_trend", None),
            "avg_rir": getattr(training_state, "avg_rir", None),
            "training_load": getattr(training_state, "training_load", None),
            "recovery_demand": getattr(training_state, "recovery_demand", None),
        }
    )


def _recovery_context(synthesis: Any, health_state: Any) -> dict[str, Any]:
    recovery_state = getattr(health_state, "recovery_state", None)
    return _drop_unknowns(
        {
            "recovery_signal": getattr(synthesis, "recovery_signal", None),
            "readiness_level": getattr(recovery_state, "readiness_level", None),
            "fatigue_risk": getattr(recovery_state, "fatigue_risk", None),
            "recovery_score": getattr(recovery_state, "recovery_score", None),
            "avg_sleep": getattr(recovery_state, "avg_sleep", None),
            "avg_energy": getattr(recovery_state, "avg_energy", None),
            "avg_soreness": getattr(recovery_state, "avg_soreness", None),
            "sleep_trend": getattr(recovery_state, "sleep_trend", None),
            "weight_trend": getattr(recovery_state, "weight_trend", None),
        }
    )


def _food_choices(
    brief: ApprovedCoachBrief, value_context: Mapping[str, Any]
) -> list[dict[str, Any]]:
    choices: list[dict[str, Any]] = []
    for action in brief.approved_food_actions[:4]:
        choices.append(
            _drop_unknowns(
                {
                    "friendly_name": action.friendly_name,
                    "canonical_name": action.canonical_name,
                    "macro_reason": action.macro_reason,
                    "allowed_conditions": list(action.allowed_conditions),
                    "serving_display": action.serving_display
                    if action.serving_allowed
                    else None,
                }
            )
        )
    nutrition = (
        value_context.get("approved_nutrition")
        if isinstance(value_context, Mapping)
        else None
    )
    if isinstance(nutrition, Mapping):
        for suggestion in nutrition.get("approved_food_suggestions") or []:
            if not isinstance(suggestion, Mapping):
                continue
            display_name = suggestion.get("display_name")
            if not display_name:
                continue
            item = _drop_unknowns(
                {
                    "friendly_name": display_name,
                    "macro_reason": suggestion.get("macro_gap_addressed"),
                    "suggestion_summary": suggestion.get("summary"),
                    "suggested_grams": suggestion.get("suggested_grams"),
                    "estimated_calories": suggestion.get("estimated_calories"),
                    "estimated_protein_g": suggestion.get("estimated_protein_g"),
                    "estimated_carbohydrate_g": suggestion.get(
                        "estimated_carbohydrate_g"
                    ),
                    "estimated_fat_g": suggestion.get("estimated_fat_g"),
                    "confidence": suggestion.get("confidence"),
                }
            )
            if item not in choices:
                choices.append(item)
    return choices[:5]


def _available_data(
    nutrition: Mapping[str, Any],
    training: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> tuple[str, ...]:
    available: list[str] = []
    if nutrition.get("available") is True or nutrition.get("macro_status"):
        available.append("nutrition")
    if training:
        available.append("training")
    if recovery:
        available.append("recovery")
    return tuple(available)


def _missing_data(
    nutrition: Mapping[str, Any],
    training: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> tuple[str, ...]:
    missing: list[str] = []
    if not nutrition or nutrition.get("available") is False:
        missing.append("complete_nutrition")
    if not training:
        missing.append("training_context")
    if not recovery:
        missing.append("recovery_context")
    return tuple(missing)


def _public_safe_mapping(value: Any, *, depth: int = 0) -> dict[str, Any]:
    if depth > 5 or not isinstance(value, Mapping):
        return {}
    safe: dict[str, Any] = {}
    for key, item in value.items():
        key_text = str(key)
        lowered = key_text.lower()
        if any(
            token in lowered
            for token in ("raw", "payload", "secret", "api_key", "token", "password")
        ):
            continue
        if isinstance(item, Mapping):
            safe[key_text] = _public_safe_mapping(item, depth=depth + 1)
        elif isinstance(item, list | tuple):
            safe[key_text] = [
                _public_safe_mapping(child, depth=depth + 1)
                if isinstance(child, Mapping)
                else child
                for child in item[:8]
                if _safe_scalar_or_collection(child)
            ]
        elif _safe_scalar_or_collection(item):
            safe[key_text] = item
    return safe


def _safe_scalar_or_collection(value: Any) -> bool:
    return value is None or isinstance(value, str | int | float | bool | list | tuple)


def _drop_unknowns(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if value is not None and value != "" and value != "Unknown"
    }


def _bounded_strings(values: Sequence[Any], *, limit: int) -> list[str]:
    return [str(value) for value in values if str(value).strip()][:limit]


def _prompt_variants() -> dict[str, DailyCoachWideContextPromptVariant]:
    return {
        "current_narrow_path": DailyCoachWideContextPromptVariant(
            variant_id="current_narrow_path",
            label="Current narrow path",
            purpose="Compare against the existing Natural Draft / Product Voice Audit path.",
            writer_instruction="",
            uses_wide_context=False,
        ),
        "wide_context_minimal_prompt": DailyCoachWideContextPromptVariant(
            variant_id="wide_context_minimal_prompt",
            label="Wide context minimal prompt",
            purpose="Rich backend-safe context with the smallest useful writing instruction.",
            writer_instruction=(
                "You are writing one Daily Coach note for a fitness app. Write like a practical coach talking directly to the user. Tell them what matters today."
            ),
        ),
        "wide_context_practical_coach": DailyCoachWideContextPromptVariant(
            variant_id="wide_context_practical_coach",
            label="Wide context practical coach",
            purpose="Test whether practical coach framing improves usefulness without adding a sentence cage.",
            writer_instruction=(
                "Write a useful Daily Coach note. Be concrete, calm, and practical. Explain how training, nutrition, and recovery fit together today, then give the next sensible action."
            ),
        ),
        "wide_context_direct_coach": DailyCoachWideContextPromptVariant(
            variant_id="wide_context_direct_coach",
            label="Wide context direct coach",
            purpose="Test more direct/plainspoken coaching with the same approved context.",
            writer_instruction=(
                "Be direct. Skip motivational fluff. Tell the user what to do today, how hard to push, what food issue matters, and what not to overdo."
            ),
        ),
        "wide_context_no_style_guidance": DailyCoachWideContextPromptVariant(
            variant_id="wide_context_no_style_guidance",
            label="Wide context with factual boundaries only",
            purpose="Optional ceiling probe: context plus boundaries, almost no style steering.",
            writer_instruction="Write one Daily Coach note from the context packet.",
        ),
    }


def _default_variant_order() -> tuple[str, ...]:
    return (
        "current_narrow_path",
        "wide_context_minimal_prompt",
        "wide_context_practical_coach",
        "wide_context_direct_coach",
    )


def _resolve_variant(variant_id: str) -> DailyCoachWideContextPromptVariant:
    variants = _prompt_variants()
    if variant_id not in variants:
        valid = ", ".join(variants)
        raise DailyCoachWideContextCeilingTrialError(
            f"unknown_prompt_variant:{variant_id}; valid={valid}"
        )
    return variants[variant_id]


def _configured_provider(provider: str, env: Mapping[str, str]) -> str:
    return (env.get(WIDE_CONTEXT_PROVIDER_ENV) or provider).strip().lower()


def _timeout_seconds(provider: str, env: Mapping[str, str]) -> float:
    key = (
        WIDE_CONTEXT_OPENAI_TIMEOUT_ENV
        if provider == PROVIDER_OPENAI
        else WIDE_CONTEXT_DIRECT_OLLAMA_TIMEOUT_ENV
    )
    value = env.get(key)
    if not value:
        return 60.0 if provider == PROVIDER_OPENAI else 120.0
    try:
        return max(1.0, float(value))
    except ValueError:
        return 60.0 if provider == PROVIDER_OPENAI else 120.0


def _normalize_ollama_model(model: str) -> str:
    return model.removeprefix("ollama/")


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


def _build_run_id(provider: str, scenario_id: str) -> str:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    safe_scenario = re.sub(r"[^a-zA-Z0-9_-]+", "_", scenario_id)
    return f"daily_coach_wide_context_uncaged_gpt55_ceiling_trial_v1_{safe_scenario}_{provider}_{timestamp.replace(':', '').replace('+', 'z')}"


def _context_packet_summary(
    results: Sequence[DailyCoachWideContextTrialRunResult],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    for run in results:
        for variant in run.variants:
            packet = variant.wide_context_packet
            if packet is None:
                continue
            key = (packet.scenario_id, packet.user_id, packet.date)
            if key in seen:
                continue
            seen.add(key)
            rows.append(packet.to_dict())
    return rows


def _render_prompt_variants() -> str:
    lines = ["# Prompt Variants", ""]
    for variant in _prompt_variants().values():
        lines.extend(
            [
                f"## {variant.variant_id}",
                f"Label: {variant.label}",
                f"Purpose: {variant.purpose}",
                f"Uses wide context: {variant.uses_wide_context}",
            ]
        )
        if variant.writer_instruction:
            lines.extend(["", variant.writer_instruction])
        lines.append("")
    return "\n".join(lines)


def _render_first_pass_drafts(
    results: Sequence[DailyCoachWideContextTrialRunResult],
) -> str:
    lines = [
        "# First-Pass Draft Capture",
        "",
        "This file captures exact returned coach-note text for each variant. It does not include raw provider envelopes.",
        "",
    ]
    for run in results:
        lines.append(f"## {run.scenario_id}")
        for variant in run.variants:
            lines.extend(
                [
                    f"### {variant.variant_id}",
                    f"Skipped: {variant.skipped}",
                    f"Skip reason: {variant.skip_reason or 'none'}",
                    "",
                    variant.first_pass_draft or "(no draft)",
                    "",
                ]
            )
    return "\n".join(lines)


def _render_side_by_side_comparison(
    results: Sequence[DailyCoachWideContextTrialRunResult],
) -> str:
    lines = ["# Side-by-Side Comparison", ""]
    for run in results:
        lines.append(f"## {run.scenario_id}")
        baseline = run.variants[0].deterministic_baseline if run.variants else ""
        narrow = run.variants[0].current_narrow_path_output if run.variants else None
        lines.extend(
            [
                "### Deterministic baseline",
                baseline or "(unavailable)",
                "",
                "### Current narrow path",
                narrow or "(unavailable)",
                "",
            ]
        )
        for variant in run.variants:
            if variant.variant_id == "current_narrow_path":
                continue
            lines.extend(
                [
                    f"### {variant.variant_id}",
                    variant.first_pass_draft or "(no draft)",
                    "",
                ]
            )
    return "\n".join(lines)


def _render_review_summary(
    results: Sequence[DailyCoachWideContextTrialRunResult],
) -> str:
    lines = [
        "# QA Review Summary",
        "",
        "This is a developer-only ceiling trial. It does not approve provider output for normal Today display.",
        "",
    ]
    for run in results:
        lines.extend(
            [
                f"## {run.scenario_id}",
                f"Provider: {run.provider}",
                f"Model: {run.model or 'default'}",
                f"Variants: {len(run.variants)}",
                "Normal Today unchanged: True",
                "Provider promotion: False",
                "",
                "Review questions:",
                "- Is the wide-context first pass meaningfully better than deterministic fallback?",
                "- Is it more useful than the current narrow path?",
                "- Did it invent unsupported facts, foods, servings, timing, workouts, or causes?",
                "- Did it sound like a practical coach instead of a validator/report?",
                "",
            ]
        )
    return "\n".join(lines)


def _render_token_cost_telemetry(
    results: Sequence[DailyCoachWideContextTrialRunResult],
) -> str:
    lines = [
        "# Token / Cost Telemetry",
        "",
        "Cost is estimated only when provider usage and explicit cost-per-million environment values are available.",
        "",
        "| Scenario | Variant | Provider | Model | Input tokens | Output tokens | Total tokens | Cached input tokens | Estimated cost USD | Cost basis |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for run in results:
        for variant in run.variants:
            meta = variant.runtime_metadata
            lines.append(
                "| "
                f"{run.scenario_id} | {variant.variant_id} | {variant.provider} | {variant.model or ''} | "
                f"{_blank(meta.get('input_tokens'))} | {_blank(meta.get('output_tokens'))} | {_blank(meta.get('total_tokens'))} | "
                f"{_blank(meta.get('cached_input_tokens'))} | {_blank(meta.get('estimated_cost_usd'))} | {meta.get('cost_estimate_basis') or ''} |"
            )
    return "\n".join(lines) + "\n"


def _write_telemetry_csv(
    path: Path, results: Sequence[DailyCoachWideContextTrialRunResult]
) -> None:
    rows: list[dict[str, Any]] = []
    for run in results:
        for variant in run.variants:
            meta = variant.runtime_metadata
            rows.append(
                {
                    "scenario_id": run.scenario_id,
                    "variant_id": variant.variant_id,
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
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)


def _render_scoring_template(
    results: Sequence[DailyCoachWideContextTrialRunResult],
) -> str:
    lines = [
        "# Wide Context Ceiling Trial Scoring Template",
        "",
        "| Scenario | Variant | Better than deterministic? | Better than narrow path? | Coach feel | Specificity | Action clarity | Factual safety | Notes |",
        "|---|---|---|---|---:|---:|---:|---:|---|",
    ]
    for run in results:
        for variant in run.variants:
            lines.append(
                f"| {run.scenario_id} | {variant.variant_id} |  |  |  |  |  |  |  |"
            )
    return "\n".join(lines) + "\n"


def _render_baseline_drift() -> str:
    return "\n".join(
        [
            "# Known Baseline Drift",
            "",
            f"Test file: `{BASELINE_DRIFT['test_file']}`",
            f"Example test: `{BASELINE_DRIFT['example_test']}`",
            f"Expected: `{BASELINE_DRIFT['example_expected']}`",
            f"Actual: `{BASELINE_DRIFT['example_actual']}`",
            "",
            "Architecture decision: document this drift and do not block the ceiling trial.",
            "This milestone must not claim full-suite green if this drift remains.",
            "This milestone must not broaden into Daily Narrative rich-day copy cleanup.",
        ]
    )


def _render_artifact_safety_summary(
    results: Sequence[DailyCoachWideContextTrialRunResult],
) -> str:
    return "\n".join(
        [
            "# Artifact Safety Summary",
            "",
            "- Developer-only artifacts: True",
            "- Raw provider envelopes persisted: False",
            "- Secrets allowed: False",
            "- Raw DB rows allowed: False",
            "- Normal Today behavior changed: False",
            f"- Runs inspected: {len(results)}",
        ]
    )


def _blank(value: Any) -> str:
    return "" if value is None else str(value)


def _assert_packet_sanitized(packet: DailyCoachWideContextPacket) -> None:
    serialized = json.dumps(packet.to_dict(), default=str).lower()
    _assert_text_sanitized(serialized, label="wide context packet")
    forbidden = ("raw_source_payload", "password", "api_key")
    if any(token in serialized for token in forbidden):
        raise DailyCoachWideContextCeilingTrialError(
            "wide_context_packet_contains_forbidden_raw_or_secret_field"
        )


def _assert_run_sanitized(result: DailyCoachWideContextTrialRunResult) -> None:
    serialized = json.dumps(result.to_dict(), default=str).lower()
    _assert_text_sanitized(serialized, label="wide context trial run")


def _assert_text_sanitized(text: str, *, label: str) -> None:
    lowered = text.lower()
    if any(pattern in lowered for pattern in SECRET_PATTERNS):
        raise DailyCoachWideContextCeilingTrialError(
            f"{label}_contains_secret_like_text"
        )
    if (
        "raw_provider_envelope" in lowered
        and 'raw_provider_envelope_persisted": false' not in lowered
    ):
        raise DailyCoachWideContextCeilingTrialError(
            f"{label}_contains_raw_provider_envelope"
        )


def _safe_error(exc: Exception) -> str:
    return re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", str(exc).replace("\n", " ")[:180])


# Keep imported constants visibly used for connector/source review and future model swaps.
assert DEFAULT_OPENAI_BASE_URL
