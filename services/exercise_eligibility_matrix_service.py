"""Generator-facing exercise eligibility matrix helpers.

The matrix makes the relationship between catalog exercises and deterministic
workout generation explicit.  It does not change selection behavior by itself;
it classifies active catalog entries, overlays the current deterministic sweep,
and exposes slot-family candidate pools that workout generation can consume in a
later narrow integration.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from models.workout_constraint_models import WorkoutConstraints
from services import workout_plan_service as workout_plans
from services.exercise_catalog_service import get_exercise_catalog
from tools.exercise_catalog_utilization_diagnostic import (
    DEFAULT_HOME_GYM_EQUIPMENT,
    SPECIALIZED_NAME_TERMS,
    SPECIALIZED_PATTERNS,
    collect_catalog_utilization_diagnostic,
)

PRIMARY_PATTERNS = {
    "squat",
    "lunge",
    "hinge",
    "horizontal_push",
    "vertical_push",
    "horizontal_pull",
    "vertical_pull",
}
ACCESSORY_PATTERNS = {"arms_biceps", "arms_triceps"}
CORE_PATTERNS = {"core_anti_extension", "core_anti_rotation"}
CONDITIONING_PATTERNS = {"conditioning", "carry"}
SUPPORTED_GENERATOR_PATTERNS = (
    PRIMARY_PATTERNS | ACCESSORY_PATTERNS | CORE_PATTERNS | CONDITIONING_PATTERNS
)

PATTERN_TO_SLOT_FAMILIES = {
    "squat": ["primary:squat"],
    "lunge": ["primary:lunge", "primary:squat_lunge_family"],
    "hinge": ["primary:hinge"],
    "horizontal_push": ["primary:horizontal_push"],
    "vertical_push": ["primary:vertical_push", "accessory:shoulder"],
    "horizontal_pull": ["primary:horizontal_pull", "accessory:upper_back"],
    "vertical_pull": ["primary:vertical_pull"],
    "arms_biceps": ["accessory:arms_biceps"],
    "arms_triceps": ["accessory:arms_triceps"],
    "core_anti_extension": ["core:anti_extension"],
    "core_anti_rotation": ["core:anti_rotation"],
    "conditioning": ["conditioning:easy_or_moderate"],
    "carry": ["conditioning:carry", "accessory:carry"],
}


def _normalize_token(value: str) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_name(value: str) -> str:
    return workout_plans._normalize_exercise_name(value)  # noqa: SLF001


@dataclass(frozen=True)
class ExerciseEligibilityRow:
    exercise_id: int
    exercise_name: str
    exercise_type: str
    movement_pattern: str
    primary_muscle_groups: list[str]
    equipment_required: list[str]
    difficulty: str
    eligibility_roles: list[str]
    slot_families: list[str]
    duplicate_family: str
    is_equipment_compatible: bool
    is_generator_eligible: bool
    is_specialized_or_accessory: bool
    reachability_status: str
    reachable_by_sizes: list[str]
    observed_candidate_slot_families: list[str]
    exclusion_reasons: list[str]


def _constraints_for(
    *,
    available_equipment: list[str] | None,
    unavailable_equipment: list[str] | None,
) -> WorkoutConstraints:
    return WorkoutConstraints(
        available_equipment=list(available_equipment or DEFAULT_HOME_GYM_EQUIPMENT),
        unavailable_equipment=list(unavailable_equipment or ["machine"]),
        confidence="Moderate",
        reason_codes=["exercise_eligibility_matrix"],
    )


def _equipment_allowed(
    equipment_required: list[str], constraints: WorkoutConstraints
) -> bool:
    return workout_plans._equipment_allowed(equipment_required, constraints)  # noqa: SLF001


def _equipment_exclusion_reasons(
    equipment_required: list[str], constraints: WorkoutConstraints
) -> list[str]:
    required = {_normalize_token(item) for item in equipment_required}
    available = {_normalize_token(item) for item in constraints.available_equipment}
    unavailable = {_normalize_token(item) for item in constraints.unavailable_equipment}
    reasons: list[str] = []
    for equipment in sorted(required & unavailable):
        reasons.append(f"blocked_unavailable_equipment:{equipment}")
    if available:
        for equipment in sorted(required - available):
            reasons.append(f"missing_available_equipment:{equipment}")
    return reasons


def _is_specialized_or_accessory(entry: Any) -> bool:
    normalized_name = entry.name.lower()
    pattern = _normalize_token(entry.movement_pattern)
    return (
        pattern in SPECIALIZED_PATTERNS
        or pattern in ACCESSORY_PATTERNS
        or pattern in CORE_PATTERNS
        or pattern in CONDITIONING_PATTERNS
        or any(term in normalized_name for term in SPECIALIZED_NAME_TERMS)
    )


def _eligibility_roles(entry: Any) -> list[str]:
    pattern = _normalize_token(entry.movement_pattern)
    roles: list[str] = []
    if pattern in PRIMARY_PATTERNS:
        roles.append("eligible_primary")
    if pattern in ACCESSORY_PATTERNS:
        roles.append("eligible_accessory")
    if pattern in CORE_PATTERNS:
        roles.append("eligible_core")
    if pattern in CONDITIONING_PATTERNS:
        roles.append("eligible_conditioning")
    if _is_specialized_or_accessory(entry) and "eligible_accessory" not in roles:
        roles.append("specialized_or_accessory")
    return roles


def _metadata_reasons(entry: Any) -> list[str]:
    reasons: list[str] = []
    if not entry.name:
        reasons.append("metadata_incomplete:name")
    if not entry.exercise_type:
        reasons.append("metadata_incomplete:exercise_type")
    if not entry.movement_pattern:
        reasons.append("metadata_incomplete:movement_pattern")
    if not entry.primary_muscle_groups:
        reasons.append("metadata_incomplete:primary_muscle_groups")
    if not entry.equipment_required:
        reasons.append("metadata_incomplete:equipment_required")
    return reasons


def _candidate_names_from_utilization(report: dict[str, Any]) -> set[str]:
    candidate_names = {
        _normalize_name(candidate_name)
        for record in report["slot_selection_records"]
        for candidate_name in record["top_candidate_names_before_scoring"]
    }
    candidate_names.update(
        _normalize_name(candidate["name"])
        for record in report["slot_selection_records"]
        for candidate in record["excluded_candidate_examples"]
    )
    return candidate_names


def _selected_names_by_size(report: dict[str, Any]) -> dict[str, set[str]]:
    selected: dict[str, set[str]] = defaultdict(set)
    for plan in report["generated_plan_sweep"]:
        selected[plan["size"]].update(
            _normalize_name(name) for name in plan["exercise_names"]
        )
    return selected


def _slot_families_by_exercise(report: dict[str, Any]) -> dict[str, set[str]]:
    slot_families: dict[str, set[str]] = defaultdict(set)
    for record in report["slot_selection_records"]:
        slot_label = f"{record['size']}:slot_{record['slot_index']}"
        for candidate_name in record["top_candidate_names_before_scoring"]:
            slot_families[_normalize_name(candidate_name)].add(slot_label)
        for candidate in record["excluded_candidate_examples"]:
            slot_families[_normalize_name(candidate["name"])].add(slot_label)
    return slot_families


def _exclusion_reasons(
    *,
    entry: Any,
    constraints: WorkoutConstraints,
    normalized_name: str,
    candidate_names: set[str],
    selected_names: set[str],
) -> list[str]:
    reasons = _metadata_reasons(entry)
    pattern = _normalize_token(entry.movement_pattern)
    equipment_compatible = _equipment_allowed(entry.equipment_required, constraints)
    if not equipment_compatible:
        reasons.extend(
            _equipment_exclusion_reasons(entry.equipment_required, constraints)
        )
    if pattern and pattern not in SUPPORTED_GENERATOR_PATTERNS:
        reasons.append(f"movement_pattern_unmapped:{pattern}")
    if equipment_compatible and pattern in SUPPORTED_GENERATOR_PATTERNS:
        if normalized_name not in candidate_names:
            reasons.append("not_supported_by_current_generator_candidate_pools")
        elif normalized_name not in selected_names:
            reasons.append("not_selected_in_deterministic_sweep")
    return reasons


def build_exercise_eligibility_matrix(
    *,
    available_equipment: list[str] | None = None,
    unavailable_equipment: list[str] | None = None,
    sizes: list[str] | None = None,
    variation_count: int = 10,
) -> list[ExerciseEligibilityRow]:
    """Build the generator-facing eligibility matrix for active catalog entries."""

    sizes = sizes or ["quick", "standard", "full"]
    constraints = _constraints_for(
        available_equipment=available_equipment,
        unavailable_equipment=unavailable_equipment,
    )
    utilization_report = collect_catalog_utilization_diagnostic(
        sizes=sizes,
        variation_count=variation_count,
        available_equipment=list(constraints.available_equipment),
    )
    candidate_names = _candidate_names_from_utilization(utilization_report)
    selected_by_size = _selected_names_by_size(utilization_report)
    selected_names = (
        set().union(*selected_by_size.values()) if selected_by_size else set()
    )
    observed_slot_families = _slot_families_by_exercise(utilization_report)

    rows: list[ExerciseEligibilityRow] = []
    for entry in get_exercise_catalog():
        normalized_name = _normalize_name(entry.name)
        pattern = _normalize_token(entry.movement_pattern)
        slot_families = list(PATTERN_TO_SLOT_FAMILIES.get(pattern, []))
        roles = _eligibility_roles(entry)
        equipment_compatible = _equipment_allowed(entry.equipment_required, constraints)
        selected_sizes = sorted(
            size for size, names in selected_by_size.items() if normalized_name in names
        )
        reasons = _exclusion_reasons(
            entry=entry,
            constraints=constraints,
            normalized_name=normalized_name,
            candidate_names=candidate_names,
            selected_names=selected_names,
        )
        is_generator_eligible = (
            equipment_compatible
            and not _metadata_reasons(entry)
            and pattern in SUPPORTED_GENERATOR_PATTERNS
            and bool(slot_families)
        )
        reachability_status = "selected_in_sweep" if selected_sizes else "not_reachable"
        if not selected_sizes and normalized_name in candidate_names:
            reachability_status = "candidate_only"
        if not equipment_compatible:
            reachability_status = "equipment_excluded"
        elif not is_generator_eligible:
            reachability_status = "not_generator_eligible"

        rows.append(
            ExerciseEligibilityRow(
                exercise_id=entry.id,
                exercise_name=entry.name,
                exercise_type=entry.exercise_type,
                movement_pattern=entry.movement_pattern,
                primary_muscle_groups=list(entry.primary_muscle_groups),
                equipment_required=list(entry.equipment_required),
                difficulty=entry.difficulty,
                eligibility_roles=roles,
                slot_families=slot_families,
                duplicate_family=workout_plans._exercise_rotation_group(entry.name),  # noqa: SLF001
                is_equipment_compatible=equipment_compatible,
                is_generator_eligible=is_generator_eligible,
                is_specialized_or_accessory=_is_specialized_or_accessory(entry),
                reachability_status=reachability_status,
                reachable_by_sizes=selected_sizes,
                observed_candidate_slot_families=sorted(
                    observed_slot_families.get(normalized_name, [])
                ),
                exclusion_reasons=reasons,
            )
        )
    return rows


def build_exercise_eligibility_summary(
    matrix: list[ExerciseEligibilityRow],
) -> dict[str, Any]:
    """Summarize matrix coverage and exclusion reasons."""

    status_counts: Counter[str] = Counter()
    exclusion_reason_counts: Counter[str] = Counter()
    reachable_by_size_counts: Counter[str] = Counter()
    reachable_by_slot_family_counts: Counter[str] = Counter()
    movement_family_counts: Counter[str] = Counter()
    reachable_movement_families: set[str] = set()

    for row in matrix:
        if row.is_equipment_compatible:
            status_counts["equipment_compatible"] += 1
        else:
            status_counts["equipment_excluded"] += 1
        if row.is_generator_eligible:
            status_counts["generator_eligible"] += 1
        if row.is_specialized_or_accessory:
            status_counts["specialized_or_accessory"] += 1
        if row.reachable_by_sizes:
            status_counts["reachable_in_deterministic_sweep"] += 1
            reachable_movement_families.add(row.movement_pattern)
        else:
            status_counts["not_reachable_in_deterministic_sweep"] += 1
        if not row.eligibility_roles:
            status_counts["not_supported_by_current_generator"] += 1
        for role in row.eligibility_roles or ["not_supported_by_current_generator"]:
            status_counts[role] += 1
        for reason in row.exclusion_reasons:
            exclusion_reason_counts[reason] += 1
        for size in row.reachable_by_sizes:
            reachable_by_size_counts[size] += 1
        for slot_family in row.slot_families:
            reachable_by_slot_family_counts[slot_family] += 1
        movement_family_counts[row.movement_pattern] += 1

    weak_families = sorted(
        pattern
        for pattern, count in movement_family_counts.items()
        if count >= 3 and pattern not in reachable_movement_families
    )

    return {
        "total_active_exercises": len(matrix),
        "total_equipment_compatible_exercises": status_counts["equipment_compatible"],
        "total_generator_eligible": status_counts["generator_eligible"],
        "total_reachable_in_deterministic_sweep": status_counts[
            "reachable_in_deterministic_sweep"
        ],
        "total_not_reachable_in_deterministic_sweep": status_counts[
            "not_reachable_in_deterministic_sweep"
        ],
        "eligibility_status_counts": dict(status_counts.most_common()),
        "exclusion_reason_counts": dict(exclusion_reason_counts.most_common()),
        "reachable_by_size": dict(reachable_by_size_counts.most_common()),
        "reachable_by_slot_family": dict(reachable_by_slot_family_counts.most_common()),
        "weak_movement_families": weak_families,
    }


def build_generator_slot_options(
    matrix: list[ExerciseEligibilityRow], slot_family: str
) -> list[tuple[str, list[str]]]:
    """Return current equipment-compatible generator options for a slot family."""

    return [
        (row.exercise_name, list(row.equipment_required))
        for row in matrix
        if row.is_equipment_compatible
        and row.is_generator_eligible
        and slot_family in row.slot_families
    ]
