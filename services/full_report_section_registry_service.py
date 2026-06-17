from __future__ import annotations

from models.full_report_section_registry_models import FullReportSectionDefinition

FULL_REPORT_SECTION_REGISTRY_VERSION = "full_report_section_registry_v1"

SECTION_MATURITY_DETERMINISTIC_STATIC = 0
SECTION_MATURITY_SOURCE_DATA_FALLBACK = 1
SECTION_MATURITY_DERIVED_EVIDENCE = 2
SECTION_MATURITY_APPROVED_CLAIMS = 3
SECTION_MATURITY_PROVIDER_EXPLANATION = 4
SECTION_MATURITY_FULL_REPORT_INTEGRATED = 5

PROVIDER_STATUS_NONE = "none"
PROVIDER_STATUS_NOT_FULL_REPORT_INTEGRATED = "not_full_report_integrated"
PROVIDER_STATUS_OPT_IN_FULL_REPORT_INTEGRATED = "opt_in_full_report_integrated"

SECTION_ID_PROFILE_CONTEXT = "profile_context"
SECTION_ID_GROUNDED_RECOMMENDATION = "grounded_recommendation"
SECTION_ID_NUTRITION_TARGET_DISPLAY = "nutrition_target_display"
SECTION_ID_TRAINING = "training"
SECTION_ID_OVERALL_SCORE = "overall_score"
SECTION_ID_BIGGEST_ISSUE = "biggest_issue"
SECTION_ID_LIKELY_CAUSE = "likely_cause"
SECTION_ID_PRIORITY_ACTION = "priority_action"
SECTION_ID_BEST_RECOMMENDATION = "best_recommendation"


def get_full_report_section_registry() -> tuple[FullReportSectionDefinition, ...]:
    """Return the explicit full-report section ownership map.

    The registry is intentionally static for v1. It documents the current public
    report sections rendered by services.coordinator_service.render_unified_health_report
    and separates the mature training provider path from deterministic/current-state
    sections that are not yet provider-owned in the full report.
    """

    return (
        FullReportSectionDefinition(
            section_id=SECTION_ID_OVERALL_SCORE,
            public_display_name="Overall Score",
            current_source="UnifiedHealthReport overall_score",
            deterministic_fallback_owner="services.coordinator_service._build_fallback_unified_report",
            provider_status=PROVIDER_STATUS_NONE,
            evidence_source="UserHealthState and CoachingDecision scenario context",
            approved_claim_source="CoachingDecision strategy and deterministic renderer guardrails",
            render_fields=["overall_score"],
            metadata_fields=[],
            maturity_level=SECTION_MATURITY_SOURCE_DATA_FALLBACK,
            notes=(
                "Currently a deterministic/coordinator-structured field. It is not "
                "mature enough for provider ownership."
            ),
        ),
        FullReportSectionDefinition(
            section_id=SECTION_ID_PROFILE_CONTEXT,
            public_display_name="Profile Context",
            current_source="UserHealthState profile fields",
            deterministic_fallback_owner="services.coordinator_service._format_profile_context",
            provider_status=PROVIDER_STATUS_NONE,
            evidence_source="User profile, bodyweight, goal, and activity fields",
            approved_claim_source="Backend profile fields and CoachingDecision scenario focus",
            render_fields=[
                "age",
                "height_cm",
                "latest_body_weight",
                "starting_weight",
                "goal_weight",
                "primary_goal",
                "activity_level",
            ],
            metadata_fields=[],
            maturity_level=SECTION_MATURITY_SOURCE_DATA_FALLBACK,
            notes="User-facing profile framing is deterministic and not provider-backed.",
        ),
        FullReportSectionDefinition(
            section_id=SECTION_ID_GROUNDED_RECOMMENDATION,
            public_display_name="Grounded Recommendation",
            current_source="ApprovedActionPlan",
            deterministic_fallback_owner="services.recommendation_engine_service.build_approved_action_plan",
            provider_status=PROVIDER_STATUS_NOT_FULL_REPORT_INTEGRATED,
            evidence_source="UserHealthState, NutritionTargets, TrainingConstraints, RecommendationContext",
            approved_claim_source="ApprovedActionPlan validation boundary",
            render_fields=[
                "daily_coaching_recommendation",
                "workout_recommendation",
                "nutrition_action",
                "rationale",
                "confidence",
                "reason_codes",
            ],
            metadata_fields=[],
            maturity_level=SECTION_MATURITY_APPROVED_CLAIMS,
            notes=(
                "The recommendation contract is approved and renderable. Candidate "
                "providers remain separate from full-report section ownership."
            ),
        ),
        FullReportSectionDefinition(
            section_id=SECTION_ID_NUTRITION_TARGET_DISPLAY,
            public_display_name="Nutrition Target Display",
            current_source="NutritionTargets display contract",
            deterministic_fallback_owner="services.coordinator_service._render_nutrition_target_display",
            provider_status=PROVIDER_STATUS_NONE,
            evidence_source="Formula-derived target display flags and confidence gates",
            approved_claim_source="Backend-owned NutritionTargets display approval flags",
            render_fields=[
                "allow_calorie_targets",
                "allow_protein_targets",
                "allow_carbohydrate_targets",
                "allow_fat_targets",
                "nutrition_display_message",
            ],
            metadata_fields=[],
            maturity_level=SECTION_MATURITY_DERIVED_EVIDENCE,
            notes="Target display is deterministic and provider output cannot unlock hidden targets.",
        ),
        FullReportSectionDefinition(
            section_id=SECTION_ID_TRAINING,
            public_display_name="Training Report Section",
            current_source="ApprovedTrainingReportSection",
            deterministic_fallback_owner="services.training_report_section_provider_service.build_deterministic_training_report_section_with_metadata",
            provider_status=PROVIDER_STATUS_OPT_IN_FULL_REPORT_INTEGRATED,
            evidence_source="ApprovedTrainingQuoteContext and TrainingEvidenceClaimService",
            approved_claim_source="Training evidence claim service, strict parser, exact-anchor validator, and provider boundary",
            render_fields=[
                "section_summary",
                "key_observations",
                "performance_interpretation",
                "fatigue_recovery_interpretation",
                "suggested_focus",
                "limitations_context",
            ],
            metadata_fields=[
                "training_section_source",
                "provider_enabled",
                "provider_attempted",
                "selected_provider",
                "selected_model",
                "fallback_used",
                "fallback_reason",
                "validation_status",
                "validation_errors_count",
            ],
            maturity_level=SECTION_MATURITY_FULL_REPORT_INTEGRATED,
            notes=(
                "Training is the first mature provider-integrated full-report section. "
                "direct_ollama remains opt-in/background-only and deterministic fallback remains mandatory."
            ),
        ),
        FullReportSectionDefinition(
            section_id=SECTION_ID_BIGGEST_ISSUE,
            public_display_name="Biggest Issue",
            current_source="CrewAI structured coordinator output if valid, otherwise deterministic fallback",
            deterministic_fallback_owner="services.coordinator_service._build_fallback_unified_report",
            provider_status=PROVIDER_STATUS_NONE,
            evidence_source="UserHealthState and CoachingDecision scenario contract",
            approved_claim_source="validate_report_language and CoachingDecision scenario validation",
            render_fields=["biggest_issue"],
            metadata_fields=[
                "full_report_composer_source",
                "coordinator_attempted",
                "coordinator_fallback_used",
                "coordinator_fallback_reason",
            ],
            maturity_level=SECTION_MATURITY_SOURCE_DATA_FALLBACK,
            notes="This field is not provider-owned; invalid coordinator output falls back deterministically.",
        ),
        FullReportSectionDefinition(
            section_id=SECTION_ID_LIKELY_CAUSE,
            public_display_name="Likely Cause",
            current_source="CrewAI structured coordinator output if valid, otherwise deterministic fallback",
            deterministic_fallback_owner="services.coordinator_service._build_fallback_unified_report",
            provider_status=PROVIDER_STATUS_NONE,
            evidence_source="UserHealthState and CoachingDecision scenario contract",
            approved_claim_source="validate_report_language and CoachingDecision scenario validation",
            render_fields=["likely_cause"],
            metadata_fields=[
                "full_report_composer_source",
                "coordinator_attempted",
                "coordinator_fallback_used",
                "coordinator_fallback_reason",
            ],
            maturity_level=SECTION_MATURITY_SOURCE_DATA_FALLBACK,
            notes="This field is not provider-owned; raw coordinator text is never persisted directly.",
        ),
        FullReportSectionDefinition(
            section_id=SECTION_ID_PRIORITY_ACTION,
            public_display_name="Highest Priority Action",
            current_source="CrewAI structured coordinator output if valid, otherwise deterministic fallback",
            deterministic_fallback_owner="services.coordinator_service._build_fallback_unified_report",
            provider_status=PROVIDER_STATUS_NONE,
            evidence_source="CoachingDecision action fields and UserHealthState",
            approved_claim_source="validate_report_language and CoachingDecision scenario validation",
            render_fields=["priority_action"],
            metadata_fields=[
                "full_report_composer_source",
                "coordinator_attempted",
                "coordinator_fallback_used",
                "coordinator_fallback_reason",
            ],
            maturity_level=SECTION_MATURITY_SOURCE_DATA_FALLBACK,
            notes="This field is strategy-bound but not a mature provider-backed section.",
        ),
        FullReportSectionDefinition(
            section_id=SECTION_ID_BEST_RECOMMENDATION,
            public_display_name="Best Recommendation",
            current_source="CrewAI structured coordinator output if valid, otherwise deterministic fallback",
            deterministic_fallback_owner="services.coordinator_service._build_fallback_unified_report",
            provider_status=PROVIDER_STATUS_NONE,
            evidence_source="CoachingDecision, ApprovedActionPlan, and UserHealthState",
            approved_claim_source="validate_report_language and CoachingDecision scenario validation",
            render_fields=["recommendation"],
            metadata_fields=[
                "full_report_composer_source",
                "coordinator_attempted",
                "coordinator_fallback_used",
                "coordinator_fallback_reason",
            ],
            maturity_level=SECTION_MATURITY_SOURCE_DATA_FALLBACK,
            notes="This is deterministic/coordinator-structured report copy, not qwen-owned product voice.",
        ),
    )


def get_full_report_section_definition(
    section_id: str,
) -> FullReportSectionDefinition | None:
    for section in get_full_report_section_registry():
        if section.section_id == section_id:
            return section
    return None


def get_full_report_section_ids() -> list[str]:
    return [section.section_id for section in get_full_report_section_registry()]


def get_provider_integrated_full_report_section_ids() -> list[str]:
    return [
        section.section_id
        for section in get_full_report_section_registry()
        if section.provider_status == PROVIDER_STATUS_OPT_IN_FULL_REPORT_INTEGRATED
    ]


def get_full_report_section_registry_metadata() -> dict[str, str]:
    """Return safe summary metadata for persisted report history."""

    return {
        "full_report_section_registry_version": FULL_REPORT_SECTION_REGISTRY_VERSION,
        "full_report_section_ids": ",".join(get_full_report_section_ids()),
        "provider_integrated_report_sections": ",".join(
            get_provider_integrated_full_report_section_ids()
        ),
    }
