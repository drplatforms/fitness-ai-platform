from __future__ import annotations

from models.daily_coach_recovery_copy_models import RecoveryAwareCoachCopyContract
from models.daily_next_action_models import (
    DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN,
    DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
    DAILY_NEXT_ACTION_LOG_FOOD,
    DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS,
    DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE,
    DAILY_NEXT_ACTION_REVIEW_WORKOUT,
    DailyNextAction,
)
from services.daily_coach_today_card_service import (
    DAILY_COACH_TODAY_CARD_TITLE,
    DailyCoachTodayCardValidationError,
    build_daily_coach_today_card,
    validate_daily_coach_today_card,
)

FORBIDDEN_NORMAL_TERMS = [
    "provider",
    "model",
    "qwen",
    "ollama",
    "direct_ollama",
    "fallback_reason",
    "parse_success",
    "validation_success",
    "raw_response",
    "prompt",
    "stack trace",
    "traceback",
    "json",
]


def _action(
    *,
    action_id: str = DAILY_NEXT_ACTION_LOG_FOOD,
    title: str = "Log a meal or snack",
    summary: str = "Add today's food intake so nutrition guidance has enough data.",
    reason: str = "Today's nutrition state is limited until more food data is logged.",
    workflow_target: str = "nutrition_quick_log",
    priority: int = 3,
    severity: str = "info",
    evidence: dict[str, object] | None = None,
) -> DailyNextAction:
    return DailyNextAction(
        action_id=action_id,
        title=title,
        summary=summary,
        reason=reason,
        priority=priority,
        workflow_target=workflow_target,
        severity=severity,
        evidence=evidence or {"scenario": "aligned_managed"},
    )


def test_today_card_builds_from_daily_next_action_without_provider_call(monkeypatch):
    def provider_should_not_run(*args, **kwargs):
        raise AssertionError("Normal Today card must not call provider generation.")

    monkeypatch.setattr(
        "services.daily_coach_narrative_provider_service.call_ollama_generate",
        provider_should_not_run,
    )

    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=_action(),
    )

    assert card.card_title == DAILY_COACH_TODAY_CARD_TITLE
    assert card.next_action_id == DAILY_NEXT_ACTION_LOG_FOOD
    assert card.next_action_title == "Log a meal or snack"
    assert card.workflow_target == "nutrition_quick_log"
    assert card.cta_label == "Next action: Log a meal or snack"
    assert card.is_provider_generated is False
    assert card.user_visible is True
    assert validate_daily_coach_today_card(card) == []


def test_today_card_public_payload_is_short_safe_and_no_leak():
    rejected_phrase = "raw_response qwen provider model prompt rejected output"
    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=_action(evidence={"raw_response": rejected_phrase}),
    )

    public_payload = card.to_public_dict()
    public_text = str(public_payload).lower()

    assert "today_card" not in public_payload
    assert "developer_metadata" not in public_payload
    assert "display_source" not in public_payload
    assert "is_provider_generated" not in public_payload
    assert "is_fallback" not in public_payload
    assert rejected_phrase not in public_text
    for term in FORBIDDEN_NORMAL_TERMS:
        assert term not in public_text
    assert len(public_payload["coach_note"]) <= 520


def test_today_card_supports_all_approved_next_action_classes():
    actions = [
        _action(
            action_id=DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN,
            title="Complete recovery check-in",
            summary="Update sleep, energy, soreness, and body weight first.",
            reason="Today's training and coaching read are limited until recovery data is updated.",
            workflow_target="today_recovery_checkin",
            priority=2,
        ),
        _action(
            action_id=DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
            title="Keep training conservative",
            summary="Use a controlled training stance before pushing intensity.",
            reason="Current recovery state supports keeping today's training lower-risk and controlled.",
            workflow_target="today_recovery_aware_workout",
            priority=1,
            severity="warning",
        ),
        _action(),
        _action(
            action_id=DAILY_NEXT_ACTION_REVIEW_WORKOUT,
            title="Review today's workout",
            summary="Check the approved workout before starting or logging sets.",
            reason="Recovery and available workout context support reviewing the structured plan for today.",
            workflow_target="workout_preview",
            priority=4,
            severity="success",
        ),
        _action(
            action_id=DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE,
            title="Review today's report guidance",
            summary="Use validated report sections to understand today's direction.",
            reason="Logged data is complete enough to review validated report guidance.",
            workflow_target="reports_guidance",
            priority=5,
            severity="success",
        ),
        _action(
            action_id=DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS,
            title="Review nutrition target progress",
            summary="Check what nutrition target-vs-actual can safely show today.",
            reason="Some daily evidence is still limited, so review approved progress before drawing stronger conclusions.",
            workflow_target="nutrition_target_vs_actual",
            priority=6,
        ),
    ]

    for action in actions:
        card = build_daily_coach_today_card(
            102,
            target_date="2026-06-20",
            action=action,
        )
        public_payload = card.to_public_dict()
        assert public_payload["card_title"] == "Today’s Coach Note"
        assert public_payload["next_action_title"] == action.title
        assert public_payload["cta_label"] == f"Next action: {action.title}"
        assert action.title in public_payload["cta_label"]
        assert validate_daily_coach_today_card(card) == []


def test_today_card_validation_rejects_debug_terms_in_normal_text():
    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=_action(),
    )
    unsafe_card = type(card)(
        **{
            **card.to_dict(),
            "coach_note": "provider model prompt raw_response should never show",
        }
    )

    violations = validate_daily_coach_today_card(unsafe_card)

    assert violations == [
        "DailyCoachTodayCard public text exposes provider/debug terminology."
    ]


def test_today_card_raises_when_validation_fails():
    unsafe_action = _action(
        summary="provider model prompt raw_response should never show",
    )

    try:
        build_daily_coach_today_card(102, action=unsafe_action)
    except DailyCoachTodayCardValidationError as exc:
        assert "provider/debug" in str(exc)
    else:
        raise AssertionError("Expected card validation to reject unsafe normal text.")


def _recovery_contract(
    *,
    recovery_v2_available: bool = True,
    recovery_pressure: str = "moderate",
    confidence: str = "Moderate",
    data_quality_status: str = "usable",
    allowed_recovery_claims: list[str] | None = None,
    required_caveats: list[str] | None = None,
    copy_tone_guidance: list[str] | None = None,
) -> RecoveryAwareCoachCopyContract:
    if allowed_recovery_claims is None:
        allowed_recovery_claims = [
            f"Recent recovery pressure appears {recovery_pressure} based on available check-in data."
        ]
    if required_caveats is None:
        required_caveats = []
    if copy_tone_guidance is None:
        copy_tone_guidance = [
            "Use bounded wording such as appears, suggests, and based on available check-ins."
        ]
    return RecoveryAwareCoachCopyContract(
        user_id=102,
        target_date="2026-06-20",
        recovery_v2_available=recovery_v2_available,
        recovery_classification="manageable" if recovery_v2_available else "unknown",
        recovery_pressure=recovery_pressure,
        confidence=confidence,
        data_quality_status=data_quality_status,
        allowed_recovery_claims=allowed_recovery_claims,
        required_caveats=required_caveats,
        forbidden_claims=[
            "medical or diagnostic claims",
            "forced training-load changes",
            "automatic training-progression changes",
        ],
        copy_tone_guidance=copy_tone_guidance,
        reason_codes=["recovery_v2_available"],
        limitations=[],
        source_services=["recovery_intelligence_v2_service"],
    )


def test_today_card_remains_unchanged_when_no_recovery_contract_is_provided():
    action = _action(action_id=DAILY_NEXT_ACTION_REVIEW_WORKOUT)

    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=action,
    )

    assert card.coach_note == (
        "Today is a good day to review the approved workout before you start. "
        "Check the plan first so the session stays tied to the current training "
        "and recovery context."
    )
    assert card.next_action_id == DAILY_NEXT_ACTION_REVIEW_WORKOUT
    assert validate_daily_coach_today_card(card) == []


def test_today_card_accepts_recovery_copy_contract_object():
    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=_action(action_id=DAILY_NEXT_ACTION_REVIEW_WORKOUT),
        recovery_copy_contract=_recovery_contract(recovery_pressure="moderate"),
    )

    public_note = card.to_public_dict()["coach_note"]
    assert (
        "Available check-in data suggests recovery pressure is moderate, so keep "
        "today’s next step controlled."
    ) in public_note
    assert len(public_note) <= 520
    assert card.next_action_id == DAILY_NEXT_ACTION_REVIEW_WORKOUT
    assert validate_daily_coach_today_card(card) == []


def test_today_card_accepts_serialized_recovery_copy_contract_dict():
    contract_payload = _recovery_contract(recovery_pressure="low").to_dict()

    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=_action(),
        recovery_copy_contract=contract_payload,
    )

    public_note = card.to_public_dict()["coach_note"]
    assert (
        "Recent check-ins suggest recovery pressure is low, so use the next "
        "action without forcing extra intensity."
    ) in public_note
    assert validate_daily_coach_today_card(card) == []


def test_today_card_uses_limited_wording_when_contract_is_unavailable():
    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=_action(),
        recovery_copy_contract=_recovery_contract(
            recovery_v2_available=False,
            recovery_pressure="unknown",
            confidence="Limited",
            data_quality_status="missing",
            allowed_recovery_claims=[
                "Recovery v2 is unavailable, so recovery-aware copy should not make specific recovery claims."
            ],
            required_caveats=[
                "Recovery v2 is unavailable for this Daily Coach Note context."
            ],
        ),
    )

    public_note = card.to_public_dict()["coach_note"]
    assert (
        "Recovery context is limited today, so keep the note grounded in the "
        "next action above."
    ) in public_note
    assert "unknown" not in public_note.lower()
    assert validate_daily_coach_today_card(card) == []


def test_today_card_uses_limited_wording_when_contract_confidence_is_limited():
    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=_action(),
        recovery_copy_contract=_recovery_contract(
            confidence="Low",
            data_quality_status="partial",
            required_caveats=[
                "Mention that available check-in data is limited, partial, or missing."
            ],
        ),
    )

    public_note = card.to_public_dict()["coach_note"]
    assert "Recovery context is limited today" in public_note
    assert validate_daily_coach_today_card(card) == []


def test_today_card_does_not_display_internal_contract_terms_or_forbidden_claims():
    contract = _recovery_contract(recovery_pressure="high")

    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=_action(),
        recovery_copy_contract=contract,
    )

    public_text = str(card.to_public_dict()).lower()
    for term in [
        "recovery_intelligence_v2_service",
        "recovery_aware_coach_copy_contract_v1",
        "reason_codes",
        "source_services",
        "contract_version",
        "data_quality_status",
        "medical or diagnostic claims",
        "automatic training-progression changes",
    ]:
        assert term not in public_text
    assert validate_daily_coach_today_card(card) == []


def test_today_card_recovery_contract_does_not_call_providers(monkeypatch):
    def provider_should_not_run(*args, **kwargs):
        raise AssertionError("Recovery-aware Today card must not call providers.")

    monkeypatch.setattr(
        "services.daily_coach_narrative_provider_service.call_ollama_generate",
        provider_should_not_run,
    )

    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=_action(),
        recovery_copy_contract=_recovery_contract(),
    )

    assert card.is_provider_generated is False
    assert validate_daily_coach_today_card(card) == []


def test_today_card_validation_rejects_unsafe_recovery_language():
    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=_action(),
    )
    unsafe_card = type(card)(
        **{
            **card.to_dict(),
            "coach_note": "Recovery says overtraining means you must deload.",
        }
    )

    violations = validate_daily_coach_today_card(unsafe_card)

    assert violations == [
        "DailyCoachTodayCard public text includes unsafe medical/claim language."
    ]
