from models.coaching_decision_models import CoachingDecision
from models.training_constraint_models import TrainingConstraints
from models.user_state_models import UserHealthState


def _has_low_rir_training(health_state: UserHealthState) -> bool:
    avg_rir = health_state.training_state.avg_rir
    return isinstance(avg_rir, int | float) and avg_rir <= 1.5


def build_training_constraints(
    health_state: UserHealthState,
    coaching_decision: CoachingDecision,
) -> TrainingConstraints:
    """Build v1 deterministic training boundaries for recommendation generation."""
    scenario = coaching_decision.scenario
    training_load = health_state.training_state.training_load
    low_rir_training = _has_low_rir_training(health_state)
    reason_codes = [scenario, f"training_load_{training_load.lower()}"]

    if low_rir_training:
        reason_codes.append("low_rir_high_effort_training")

    if scenario == "recovery_limited":
        return TrainingConstraints(
            recommended_rir_min=2,
            recommended_rir_max=3,
            low_rir_guidance=(
                "Keep most working sets around RIR 2-3 and avoid frequent RIR 0-1 work."
            ),
            progression_guidance=(
                "Hold or slightly reduce training stress until sleep, soreness, and energy improve."
            ),
            recovery_constraint="Recovery markers limit aggressive progression.",
            confidence="High",
            reason_codes=reason_codes,
        )

    if scenario == "improving_after_deload":
        return TrainingConstraints(
            recommended_rir_min=2,
            recommended_rir_max=3,
            low_rir_guidance=(
                "Keep most working sets around RIR 2-3 while recovery stabilizes."
            ),
            progression_guidance=(
                "Increase load or volume gradually rather than jumping back to frequent high-effort sets."
            ),
            recovery_constraint="Recent improvement favors controlled progression.",
            confidence="Moderate",
            reason_codes=reason_codes + ["controlled_progression"],
        )

    if scenario == "nutrition_training_mismatch":
        return TrainingConstraints(
            recommended_rir_min=2,
            recommended_rir_max=4,
            low_rir_guidance=(
                "Limit frequent RIR 0-1 work until nutrition support is clearer."
            ),
            progression_guidance=(
                "Keep training progression controlled while nutrition support is reviewed."
            ),
            recovery_constraint="Nutrition support may limit training progression confidence.",
            confidence="Moderate",
            reason_codes=reason_codes + ["nutrition_support_unclear"],
        )

    if scenario == "data_quality_limited":
        return TrainingConstraints(
            recommended_rir_min=2,
            recommended_rir_max=4,
            low_rir_guidance=(
                "Avoid major training changes from incomplete or unusual data alone."
            ),
            progression_guidance=(
                "Maintain manageable training while logging quality improves."
            ),
            recovery_constraint="Data quality limits confidence in stronger training changes.",
            confidence="Low",
            reason_codes=reason_codes + ["data_quality_limited"],
        )

    return TrainingConstraints(
        recommended_rir_min=2,
        recommended_rir_max=4,
        low_rir_guidance=(
            "RIR 0-1 work can remain occasional rather than the default."
        ),
        progression_guidance="Progress gradually while recovery markers remain stable.",
        recovery_constraint="No major recovery constraint is apparent.",
        confidence="High",
        reason_codes=reason_codes + ["aligned_managed"],
    )
