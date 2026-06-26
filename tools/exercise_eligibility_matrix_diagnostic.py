"""Developer diagnostic for Exercise Eligibility Matrix v1.

This tool is intentionally diagnostic-only. It does not change workout
selection behavior. It classifies catalog exercises into generator-facing
eligibility buckets, then overlays the current deterministic generation sweep
so Backend/Architecture can decide the smallest safe implementation change.
"""

# ruff: noqa: E402, SLF001

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
ACCESSORY_PATTERNS = {
    "arms_biceps",
    "arms_triceps",
}
CORE_PATTERNS = {
    "core_anti_extension",
    "core_anti_rotation",
}
CONDITIONING_PATTERNS = {
    "conditioning",
    "carry",
}
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

KNOWN_EXAMPLES_TO_INSPECT = [
    "Reverse Lunge",
    "Split Squat",
    "Glute Bridge",
    "Side Plank",
    "Dead Bug",
    "Dumbbell Bench Press",
    "Dumbbell Row",
    "Dumbbell RDL",
    "Dumbbell Split Squat",
    "Hip Thrust",
    "Band-Assisted Pull-Up",
    "Band Pull-Apart",
    "Band Face Pull",
    "Cable Face Pull",
    "Cable Woodchop",
    "Bird Dog",
    "Dumbbell Rear Delt Fly",
    "Farmer Carry",
    "Suitcase Carry",
    "Treadmill Incline Walk",
    "Bike Steady State",
]


def _normalize_token(value: str) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_name(value: str) -> str:
    return workout_plans._normalize_exercise_name(value)


def _equipment_allowed(
    equipment_required: list[str], constraints: WorkoutConstraints
) -> bool:
    return workout_plans._equipment_allowed(equipment_required, constraints)


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
    return (
        entry.movement_pattern in SPECIALIZED_PATTERNS
        or entry.movement_pattern in ACCESSORY_PATTERNS
        or entry.movement_pattern in CORE_PATTERNS
        or entry.movement_pattern in CONDITIONING_PATTERNS
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


def collect_exercise_eligibility_matrix_diagnostic(
    *,
    variation_count: int = 10,
    sizes: list[str] | None = None,
    available_equipment: list[str] | None = None,
) -> dict[str, Any]:
    """Collect current generator-facing exercise eligibility diagnostics."""

    sizes = sizes or ["quick", "standard", "full"]
    available_equipment = available_equipment or list(DEFAULT_HOME_GYM_EQUIPMENT)
    constraints = WorkoutConstraints(
        available_equipment=available_equipment,
        unavailable_equipment=["machine"],
        confidence="Moderate",
        reason_codes=["exercise_eligibility_matrix_diagnostic"],
    )
    utilization_report = collect_catalog_utilization_diagnostic(
        sizes=sizes,
        variation_count=variation_count,
        available_equipment=available_equipment,
    )
    catalog = get_exercise_catalog()
    candidate_names = _candidate_names_from_utilization(utilization_report)
    selected_by_size = _selected_names_by_size(utilization_report)
    selected_names = (
        set().union(*selected_by_size.values()) if selected_by_size else set()
    )
    observed_slot_families = _slot_families_by_exercise(utilization_report)

    exercise_rows: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    exclusion_counts: Counter[str] = Counter()
    reachable_by_size_counts: Counter[str] = Counter()
    reachable_by_slot_family_counts: Counter[str] = Counter()
    movement_family_counts: Counter[str] = Counter()

    for entry in catalog:
        normalized_name = _normalize_name(entry.name)
        pattern = _normalize_token(entry.movement_pattern)
        slot_families = list(PATTERN_TO_SLOT_FAMILIES.get(pattern, []))
        roles = _eligibility_roles(entry)
        equipment_compatible = _equipment_allowed(entry.equipment_required, constraints)
        selected_sizes = sorted(
            size for size, names in selected_by_size.items() if normalized_name in names
        )
        selected_slot_families = sorted(observed_slot_families.get(normalized_name, []))
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

        row = {
            "exercise_id": entry.id,
            "exercise_name": entry.name,
            "exercise_type": entry.exercise_type,
            "movement_pattern": entry.movement_pattern,
            "primary_muscle_groups": list(entry.primary_muscle_groups),
            "equipment_required": list(entry.equipment_required),
            "difficulty": entry.difficulty,
            "eligibility_roles": roles,
            "slot_families": slot_families,
            "duplicate_family": workout_plans._exercise_rotation_group(entry.name),
            "is_equipment_compatible": equipment_compatible,
            "is_generator_eligible": is_generator_eligible,
            "is_specialized_or_accessory": _is_specialized_or_accessory(entry),
            "reachability_status": reachability_status,
            "reachable_by_sizes": selected_sizes,
            "observed_candidate_slot_families": selected_slot_families,
            "exclusion_reasons": reasons,
        }
        exercise_rows.append(row)
        if not roles:
            category_counts["not_supported_by_current_generator"] += 1
        for role in roles or ["not_supported_by_current_generator"]:
            category_counts[role] += 1
        if equipment_compatible:
            category_counts["equipment_compatible"] += 1
        else:
            category_counts["equipment_excluded"] += 1
        if selected_sizes:
            category_counts["reachable_in_deterministic_sweep"] += 1
        else:
            category_counts["not_reachable_in_deterministic_sweep"] += 1
        if is_generator_eligible:
            category_counts["generator_eligible"] += 1
        for reason in reasons:
            exclusion_counts[reason] += 1
        for size in selected_sizes:
            reachable_by_size_counts[size] += 1
        for slot_family in slot_families:
            reachable_by_slot_family_counts[slot_family] += 1
        movement_family_counts[entry.movement_pattern] += 1

    known_examples = {
        name: next(
            (
                row
                for row in exercise_rows
                if _normalize_name(row["exercise_name"]) == _normalize_name(name)
            ),
            None,
        )
        for name in KNOWN_EXAMPLES_TO_INSPECT
    }
    high_value_not_reachable = [
        row
        for row in exercise_rows
        if row["is_equipment_compatible"]
        and row["is_generator_eligible"]
        and not row["reachable_by_sizes"]
    ]
    weak_movement_families = [
        pattern
        for pattern, count in movement_family_counts.items()
        if count >= 3
        and not any(
            pattern == row["movement_pattern"] and row["reachable_by_sizes"]
            for row in exercise_rows
        )
    ]

    report = {
        "diagnostic_scope": {
            "sizes": sizes,
            "variation_count": variation_count,
            "available_equipment": available_equipment,
            "unavailable_equipment": constraints.unavailable_equipment,
        },
        "catalog_totals": {
            "total_active_exercises": len(catalog),
            "total_exercises_with_usable_metadata": sum(
                1
                for row in exercise_rows
                if not any(
                    reason.startswith("metadata_incomplete")
                    for reason in row["exclusion_reasons"]
                )
            ),
            "total_equipment_compatible_exercises": category_counts[
                "equipment_compatible"
            ],
            "total_specialized_or_accessory_movements": sum(
                1 for row in exercise_rows if row["is_specialized_or_accessory"]
            ),
        },
        "eligibility_status_counts": dict(category_counts.most_common()),
        "reachability_summary": {
            "total_generator_eligible": category_counts["generator_eligible"],
            "total_reachable_in_deterministic_sweep": category_counts[
                "reachable_in_deterministic_sweep"
            ],
            "total_not_reachable_in_deterministic_sweep": category_counts[
                "not_reachable_in_deterministic_sweep"
            ],
            "reachable_by_size": dict(reachable_by_size_counts.most_common()),
            "reachable_by_slot_family": dict(
                reachable_by_slot_family_counts.most_common()
            ),
            "weak_movement_families": sorted(weak_movement_families),
            "high_value_not_reachable_examples": high_value_not_reachable[:40],
        },
        "exclusion_reason_counts": dict(exclusion_counts.most_common()),
        "known_examples": known_examples,
        "exercise_rows": exercise_rows,
        "underlying_catalog_utilization_findings": utilization_report[
            "diagnostic_findings"
        ],
    }
    report["diagnostic_findings"] = _build_findings(report)
    return report


def _build_findings(report: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    totals = report["catalog_totals"]
    reachability = report["reachability_summary"]
    findings.append(
        f"Classified {totals['total_active_exercises']} active catalog exercises; "
        f"{totals['total_equipment_compatible_exercises']} are equipment-compatible."
    )
    findings.append(
        f"{reachability['total_generator_eligible']} exercises are currently classified as generator-eligible."
    )
    findings.append(
        f"{reachability['total_reachable_in_deterministic_sweep']} exercises appeared in the deterministic generation sweep."
    )
    if reachability["high_value_not_reachable_examples"]:
        findings.append(
            f"{len(reachability['high_value_not_reachable_examples'])} generator-eligible/equipment-compatible examples were not selected in the sweep sample."
        )
    if report["exclusion_reason_counts"]:
        top_reason, top_count = next(iter(report["exclusion_reason_counts"].items()))
        findings.append(f"Top exclusion reason: {top_reason} ({top_count}).")
    return findings


def _print_text_report(report: dict[str, Any]) -> None:
    print("=" * 80)
    print("EXERCISE ELIGIBILITY MATRIX DIAGNOSTIC V1")
    print("=" * 80)
    for finding in report["diagnostic_findings"]:
        print(f"- {finding}")

    print("\nCATALOG TOTALS")
    for key, value in report["catalog_totals"].items():
        print(f"{key}: {value}")

    print("\nELIGIBILITY STATUS COUNTS")
    for key, value in report["eligibility_status_counts"].items():
        print(f"{key}: {value}")

    print("\nREACHABILITY SUMMARY")
    for key, value in report["reachability_summary"].items():
        if key == "high_value_not_reachable_examples":
            print(f"{key}: {len(value)} examples shown in JSON")
        else:
            print(f"{key}: {value}")

    print("\nEXCLUSION REASON COUNTS")
    for key, value in report["exclusion_reason_counts"].items():
        print(f"{key}: {value}")

    print("\nKNOWN EXAMPLES")
    for name, row in report["known_examples"].items():
        if row is None:
            print(f"- {name}: missing_from_catalog")
            continue
        print(
            f"- {name}: roles={row['eligibility_roles']} "
            f"slots={row['slot_families']} status={row['reachability_status']} "
            f"sizes={row['reachable_by_sizes']} reasons={row['exclusion_reasons']}"
        )

    print("\nUNDERLYING CATALOG UTILIZATION FINDINGS")
    for finding in report["underlying_catalog_utilization_findings"]:
        print(f"- {finding}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report generator-facing Exercise Eligibility Matrix diagnostics."
    )
    parser.add_argument("--variation-count", type=int, default=10)
    parser.add_argument(
        "--sizes",
        nargs="+",
        default=["quick", "standard", "full"],
        choices=["quick", "standard", "full"],
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        help="Optional path for JSON output. Text output is printed when format=text.",
    )
    args = parser.parse_args()

    report = collect_exercise_eligibility_matrix_diagnostic(
        sizes=list(args.sizes),
        variation_count=args.variation_count,
    )
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
