# Milestone — Daily Coach Note Recovery-Aware Language v1

Requested status:

```text
DAILY_COACH_NOTE_RECOVERY_AWARE_LANGUAGE_V1_IMPLEMENTATION_COMPLETE
```

Baseline:

```text
c940ff4 Merge recovery-aware coach copy contract v1
```

Source snapshot:

```text
fitness_ai_snapshot_2026-07-01_c940ff4_main_merge-recovery-aware-coach-copy-contract-v1.zip
```

## Purpose

This milestone adds the first bounded user-facing Daily Coach Note recovery-aware language to the deterministic Today card path.

The Today card may now use an approved `RecoveryAwareCoachCopyContract` when one is supplied by the caller. The copy remains deterministic, contract-bound, public-safe, and short.

## Implemented behavior

- `build_daily_coach_today_card()` remains backward compatible when no recovery copy contract is provided.
- The Today card accepts an optional `RecoveryAwareCoachCopyContract` object.
- The Today card accepts an optional serialized recovery copy contract dictionary.
- The existing deterministic Daily Next Action selection remains unchanged.
- The base deterministic Today card note remains unchanged when no recovery contract is supplied.
- When a usable contract is supplied, the service may append one short recovery-aware sentence.
- Recovery-aware sentence selection is bounded by contract fields:
  - `recovery_v2_available`
  - `recovery_pressure`
  - `confidence`
  - `data_quality_status`
  - `allowed_recovery_claims`
  - `required_caveats`
  - `copy_tone_guidance`
  - `limitations`
- Limited, missing, unavailable, partial, Low-confidence, or Limited-confidence recovery context uses limited-context wording instead of stronger recovery-pressure copy.
- Public Today card text does not display raw internal contract labels such as `reason_codes`, `source_services`, `contract_version`, or `data_quality_status`.
- Public Today card text does not display provider/debug terminology.
- Public Today card text does not display forbidden recovery-copy categories.
- `coach_note` remains capped at 520 characters.

## Explicit non-goals preserved

This milestone does not add or change:

- provider-generated Daily Coach Note copy
- OpenAI/Ollama/CrewAI behavior
- Daily Next Action selection behavior
- Streamlit UI layout
- API routes
- database schema or migrations
- persistence behavior
- report behavior
- recommendation behavior
- workout plan behavior
- nutrition target behavior
- automatic deload logic
- automatic progression logic
- wearable/HRV integration
- medical interpretation

## Validation focus

Focused tests cover:

- no-contract backward compatibility
- object contract support
- serialized dictionary contract support
- bounded recovery-aware sentence rendering
- limited/unavailable recovery-context wording
- internal contract-term non-exposure
- forbidden recovery-language rejection
- provider-call absence
- unchanged Daily Next Action fields
- existing Recovery-Aware Coach Copy Contract tests
- existing Daily Coach Note Recovery v2 context tests
