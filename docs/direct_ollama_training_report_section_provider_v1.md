# Direct Ollama Training Report Section Provider v1

## Status

Promoted as the opt-in provider boundary after Training Evidence Claim Runtime QA v1.

Runtime QA accepted the known-good path as FULL PASS for:

- user_id: 102
- date: 2026-06-06
- model: `ollama/qwen2.5:3b`
- run count: 2
- validation status: approved
- fallback used: false

No parser relaxation, validator relaxation, fallback bypass, or code rollback was required.

## Provider configuration

Deterministic remains the default. Direct Ollama remains opt-in.

```text
TRAINING_REPORT_SECTION_PROVIDER=deterministic|direct_ollama
TRAINING_REPORT_SECTION_MODEL=ollama/qwen2.5:3b
TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=60
```

`ollama/qwen2.5:3b` is the supported Provider Promotion v1 model. Other local models, including qwen3 variants, remain experimental/product-voice probes only and must pass the same parser, validator, exact-anchor, and fallback contract before support is considered.

## Accepted architecture

The accepted provider flow is:

```text
approved workout/training facts
→ TrainingEvidenceContext
→ ApprovedTrainingClaim[]
→ model-facing quote context
→ direct Ollama candidate
→ strict JSON parser
→ exact-anchor validator
→ provider-approved section or deterministic fallback
```

The provider path consumes service-derived `ApprovedTrainingClaim[]`. It does not own bounded claim derivation.

## Authority order

The evidence layer does not replace exact anchors. The accepted authority order is:

```text
1. exact required training details
2. exact key_observation copy gate
3. required anchor count validation
4. approved bounded training claims
5. approved interpretation claims
6. approved coaching moves
```

The prompt must satisfy exact `key_observations` before using bounded claims, interpretation claims, or coaching moves.

## Runtime safety position

The provider remains strict. The backend rejects:

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

Provider output is used only after strict parser and validator approval. Invalid output falls back deterministically.

## Boundaries

This milestone does not wire the training section into full report assembly.

It does not change Streamlit, report persistence, workout generation, nutrition/recovery systems, or CrewAI behavior.

It does not make `direct_ollama` the default.

It does not persist raw provider output.

It does not expose raw provider output publicly.

## Runtime metadata

The service result exposes debug metadata separately from the approved public section, including provider/model selection, parse and validation status, fallback state, raw output diagnostics, matched anchors, and matched approved interpretation claims.

`required_anchor_count` is currently the minimum required threshold. It is possible for `matched_required_fact_anchors` to contain more entries than this threshold. That is not a failure when validation is approved, `missing_required_anchor_count` is zero, and validation errors are empty.

Optional future polish may rename this field to `required_minimum_anchor_count` and add `matched_anchor_count`, with no behavior change.

## Expanded runtime QA matrix

Expanded Training Evidence Runtime QA Matrix v1 is accepted as PASS.

qwen2.5:3b was tested across seeded users 101-105. It approved the scenarios where exact-anchor, validator-compatible provider output was available and fell back safely for scenarios where provider output was not acceptable.

Accepted matrix result:

- User 101: rejected safely, deterministic fallback used
- User 102: provider approved
- User 103: provider approved
- User 104: provider approved
- User 105: rejected safely, deterministic fallback used

This is the desired behavior. The provider does not need to approve every scenario. It must either validate cleanly or fall back safely.

## Product voice compatibility

qwen3:8b remains experimental/product-voice probe only. It showed stronger product-language potential than qwen2.5:3b, but it was not promoted because its output was not consistently validator-compatible.

Training Report Section Product Voice Compatibility v1 adds prompt examples for scope-limited coaching language while preserving strict validation.

qwen2.5:3b remains the supported direct-Ollama training report section model.

qwen3 must not be made supported/default without a separate Architecture approval.

## Next recommended milestone

After Product Voice Compatibility v1, run qwen3 runtime QA again for seeded users 101-105.

Full report integration should remain separate and should not start until the provider boundary continues to validate cleanly or fall back safely across the expanded matrix.
