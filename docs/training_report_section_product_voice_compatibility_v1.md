# Training Report Section Product Voice Compatibility v1

## Status

Implemented as a narrow prompt/context compatibility patch after Expanded Training Evidence Runtime QA Matrix v1.

qwen2.5:3b remains the supported direct-Ollama training report section model.

qwen3:8b remains experimental/product-voice probe only.

## Background

Expanded Training Evidence Runtime QA Matrix v1 validated the service-backed provider boundary beyond the original known-good user 102 scenario.

Runtime matrix result for qwen2.5:3b:

- User 101: rejected safely, deterministic fallback used
- User 102: provider approved
- User 103: provider approved
- User 104: provider approved
- User 105: rejected safely, deterministic fallback used

This is accepted behavior. The provider does not need to approve every scenario. It needs to either validate cleanly or fall back safely.

qwen3:8b showed better product-language potential but failed validation because `fatigue_recovery_interpretation` did not satisfy the required `scope_limit` coaching move.

## Decision

Do not promote qwen3.

Do not loosen validation.

Improve prompt/context examples for validator-compatible scope-limit phrasing while preserving qwen2.5 as the supported baseline.

## Prompt compatibility update

The prompt now provides example shapes for scope-limited product voice:

```text
fatigue_recovery_interpretation:
"<Approved workout or exercise name> shows high-effort work from logged RIR, but it does not prove a broader fatigue or recovery pattern."

limitations_context:
"<Approved workout or exercise name> can guide the next training choice, but one workout should not be read as a trend."
```

These are examples only. They are not new approved claims, and they do not weaken the validator.

## Safety boundaries preserved

The provider path still rejects:

- paraphrased required anchors
- unsupported progression claims
- broad effort claims
- form/control claims
- recovery/fatigue claims outside approved context
- planned-work alignment claims without approved anchors
- single-session facts converted into broad trends
- wrapper objects
- extra keys
- raw/unbounded provider output

Exact required fact anchors remain mandatory.

Deterministic fallback remains mandatory.

## Model position

Supported:

- `ollama/qwen2.5:3b`

Experimental/product-voice probe only:

- `ollama/qwen3:8b`

qwen3 should not be made supported/default from this milestone alone.

## Acceptance criteria

This milestone passes if:

1. qwen2.5 baseline remains unchanged.
2. qwen3 remains experimental.
3. qwen3 either validates cleanly or falls back safely during manual runtime QA.
4. scope-limit prompt examples improve validator compatibility.
5. exact anchors remain mandatory.
6. broad progression, recovery, fatigue, form, adherence, or trend claims are still rejected.
7. deterministic fallback remains public-safe.
8. pytest does not call live Ollama.
9. full pytest passes.

## Non-goals

Do not:

- make qwen3 supported/default
- make direct_ollama default
- loosen parser behavior
- loosen validator behavior
- accept paraphrased anchors
- accept unsupported progression claims
- accept unsupported form/control claims
- accept unsupported recovery/fatigue claims
- accept broad trend claims from single-session evidence
- integrate into full AI Health Report
- persist raw model output
- expose raw provider output
- add Streamlit provider controls
- change workout generation
- change nutrition/recovery/report systems

## Recommended follow-up

Run qwen3 runtime QA again for seeded users 101-105.

If qwen3 becomes validator-compatible, Architecture can consider Training Report Section Premium Provider Trial v1.

Full report integration should remain separate.
