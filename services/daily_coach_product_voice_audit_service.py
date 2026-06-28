from __future__ import annotations

import re

from models.daily_coach_natural_draft_audit_models import (
    ApprovedCoachBrief,
    NaturalCoachDraft,
    ProductVoiceAuditFinding,
    ProductVoiceAuditResult,
    ProductVoiceAuditScore,
)
from services.daily_coach_food_action_language_service import (
    backend_food_phrase_hits,
    food_action_language_passes,
    mechanical_food_action_hits,
)

STALE_SENTENCE_SKELETONS = (
    "recovery looks good enough to train today",
    "do the planned workout",
    "train as planned, keep a couple reps in reserve",
    "do not turn today into a max-effort test",
)

BAD_CAUSAL_LOGIC = (
    "do not overdo training intensity while nutrition gap",
    "do not overdo the training intensity while nutrition gap",
    "do not overdo training intensity while the nutrition gap is still open",
    "do not overdo the training intensity while the nutrition gap is still open",
    "make up for nutrition by pushing harder",
    "do not make up for nutrition by pushing harder",
    "solve calories by pushing harder",
    "solve protein by pushing harder",
    "do not solve calories/protein by pushing harder in the gym",
    "fix protein by pushing harder",
    "fix calories by pushing harder",
)


def audit_daily_coach_product_voice(
    draft: NaturalCoachDraft,
    brief: ApprovedCoachBrief,
    *,
    mode: str = "approval",
) -> ProductVoiceAuditResult:
    """Score product usefulness separately from factual claim audit."""

    text = f"{draft.headline}\n{draft.body}"
    findings: list[ProductVoiceAuditFinding] = []
    mechanical = mechanical_food_action_hits(text)
    backend = backend_food_phrase_hits(text)
    stale = _stale_skeleton_hits(text)
    causal = _bad_causal_logic_hits(text)

    for phrase in mechanical:
        findings.append(
            ProductVoiceAuditFinding(
                finding_type="mechanical_food_action",
                severity="fail" if mode == "approval" else "warn",
                text_span=phrase,
                reason="Food action sounds like manipulating a macro database row instead of eating food.",
                repair_instruction="Use eating language such as 'have oatmeal' or 'eat some canned tuna'.",
                repairable=True,
            )
        )
    for phrase in backend:
        findings.append(
            ProductVoiceAuditFinding(
                finding_type="backend_food_phrase",
                severity="warn",
                text_span=phrase,
                reason="Food language exposes backend/app terminology instead of normal coaching language.",
                repair_instruction="Use user-facing wording such as 'if you still need more protein' or 'eat something simple like canned tuna'.",
                repairable=True,
            )
        )
    for phrase in stale:
        findings.append(
            ProductVoiceAuditFinding(
                finding_type="stale_sentence_skeleton",
                severity="warn",
                text_span=phrase,
                reason="The draft repeats a stale Daily Coach sentence skeleton.",
                repair_instruction="Vary the phrasing while preserving the approved meaning.",
                repairable=True,
            )
        )
    for phrase in causal:
        findings.append(
            ProductVoiceAuditFinding(
                finding_type="bad_nutrition_training_causal_logic",
                severity="fail" if mode == "approval" else "warn",
                text_span=phrase,
                reason="The draft creates an odd or unsupported causal link between nutrition and training intensity.",
                repair_instruction="Keep nutrition and training guidance separate unless the brief approved the causal link.",
                repairable=True,
            )
        )

    if not food_action_language_passes(text, brief):
        # If a more specific finding already exists, this summary finding helps QA see the gate.
        if not any(item.finding_type == "mechanical_food_action" for item in findings):
            findings.append(
                ProductVoiceAuditFinding(
                    finding_type="food_action_language_contract_failed",
                    severity="fail" if mode == "approval" else "warn",
                    text_span="food action language",
                    reason="Food action language did not pass the v2 food action contract.",
                    repair_instruction="Use friendly food names and eating-language actions.",
                    repairable=True,
                )
            )

    scores = _score_dimensions(draft, findings)
    readiness = next(
        score.score for score in scores if score.dimension == "product_readiness"
    )
    hard_failure = any(finding.severity == "fail" for finding in findings)
    blocking_voice_finding = any(
        finding.finding_type
        in {
            "mechanical_food_action",
            "backend_food_phrase",
            "food_action_language_contract_failed",
            "bad_nutrition_training_causal_logic",
        }
        for finding in findings
    )
    passed = (not hard_failure) and (not blocking_voice_finding) and readiness >= 4
    decision = "approve" if passed else "fallback_required"
    if not passed and all(finding.repairable for finding in findings):
        decision = "repair_required"

    return ProductVoiceAuditResult(
        passed=passed,
        mode=mode,  # type: ignore[arg-type]
        decision=decision,  # type: ignore[arg-type]
        scores=tuple(scores),
        findings=tuple(findings),
        mechanical_food_action_count=len(mechanical),
        backend_phrase_count=len(backend),
        stale_skeleton_count=len(stale),
        product_readiness_score=readiness,
    )


def _score_dimensions(
    draft: NaturalCoachDraft, findings: list[ProductVoiceAuditFinding]
) -> tuple[ProductVoiceAuditScore, ...]:
    text = f"{draft.headline}\n{draft.body}".strip()
    word_count = len(re.findall(r"\w+", text))
    finding_types = {finding.finding_type for finding in findings}
    food_penalty = 3 if "mechanical_food_action" in finding_types else 0
    backend_penalty = 2 if "backend_food_phrase" in finding_types else 0
    stale_penalty = 1 if "stale_sentence_skeleton" in finding_types else 0
    causal_penalty = 3 if "bad_nutrition_training_causal_logic" in finding_types else 0
    too_thin_penalty = 1 if word_count < 20 else 0
    generic_penalty = 1 if _looks_generic(text) else 0

    plainspoken = _bounded_score(5 - backend_penalty - stale_penalty)
    scenario_specificity = _bounded_score(5 - generic_penalty - too_thin_penalty)
    action_clarity = _bounded_score(5 - food_penalty - generic_penalty)
    food_naturalness = _bounded_score(5 - food_penalty - backend_penalty)
    training_clarity = _bounded_score(5 - stale_penalty - causal_penalty)
    recovery_clarity = _bounded_score(5 - stale_penalty)
    phrase_variety = _bounded_score(5 - stale_penalty)
    logic_coherence = _bounded_score(5 - causal_penalty)
    product_readiness = min(
        plainspoken,
        scenario_specificity,
        action_clarity,
        food_naturalness,
        training_clarity,
        recovery_clarity,
        logic_coherence,
    )
    if any(
        item in finding_types
        for item in {
            "mechanical_food_action",
            "backend_food_phrase",
            "food_action_language_contract_failed",
            "bad_nutrition_training_causal_logic",
        }
    ):
        product_readiness = min(product_readiness, 3)
    return (
        ProductVoiceAuditScore(
            "plainspoken_voice", plainspoken, "Normal, direct coaching language."
        ),
        ProductVoiceAuditScore(
            "scenario_specificity",
            scenario_specificity,
            "Responds to the scenario instead of generic wellness advice.",
        ),
        ProductVoiceAuditScore("action_clarity", action_clarity, "Says what to do."),
        ProductVoiceAuditScore(
            "food_naturalness", food_naturalness, "Food copy sounds like eating food."
        ),
        ProductVoiceAuditScore(
            "training_clarity",
            training_clarity,
            "Training guidance is direct and not weirdly causal.",
        ),
        ProductVoiceAuditScore(
            "recovery_clarity",
            recovery_clarity,
            "Recovery implication is understandable.",
        ),
        ProductVoiceAuditScore(
            "phrase_variety", phrase_variety, "Avoids stacked stale sentence skeletons."
        ),
        ProductVoiceAuditScore(
            "logic_coherence",
            logic_coherence,
            "Nutrition, training, and recovery logic do not contradict each other.",
        ),
        ProductVoiceAuditScore(
            "product_readiness",
            product_readiness,
            "5 means shippable with no edit; backend-shaped or mechanical wording caps readiness below product-ready.",
        ),
    )


def _stale_skeleton_hits(text: str) -> tuple[str, ...]:
    normalized = _normalize(text)
    hits = tuple(phrase for phrase in STALE_SENTENCE_SKELETONS if phrase in normalized)
    # One familiar phrase can be acceptable; stacked skeletons are the product problem.
    return hits if len(hits) >= 2 else ()


def _bad_causal_logic_hits(text: str) -> tuple[str, ...]:
    normalized = _normalize(text)
    return tuple(phrase for phrase in BAD_CAUSAL_LOGIC if phrase in normalized)


def _looks_generic(text: str) -> bool:
    normalized = _normalize(text)
    generic = (
        "keep going",
        "stay consistent",
        "listen to your body",
        "make healthy choices",
    )
    return any(phrase in normalized for phrase in generic)


def _bounded_score(score: int) -> int:
    return max(1, min(5, score))


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()
