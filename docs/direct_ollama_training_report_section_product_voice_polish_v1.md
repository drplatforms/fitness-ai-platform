# Direct Ollama Training Report Section Product Voice Polish v1

## Status

Spike/provider-focused copy-polish pass after `Direct Ollama Training Report Section Provider v1`.

## Intent

Provider v1 proved the opt-in direct Ollama training section provider can pass strict grounding with `qwen2.5:3b`, but the accepted copy was still too stiff. This pass improves the approved coach-language frames while keeping the existing safety contract intact.

## Preserved constraints

- Deterministic remains default.
- `direct_ollama` remains opt-in.
- `qwen2.5:3b` remains the supported baseline model for this path.
- Quote-only model-facing context remains in place.
- Required fact anchors remain in place.
- Anchor-first key observations remain in place.
- Approved interpretation claims remain in place.
- Strict parser and validator remain in place.
- Deterministic fallback remains in place.
- No full report integration is added.
- No Streamlit changes are added.
- No report persistence changes are added.

## Product voice changes

The model-facing coaching frames now prefer more natural user-facing language such as:

- using the clearest training signal from named lifts
- using named lifts as reference lifts before increasing intensity
- keeping the next session measured
- continuing to log load, reps, and RIR so future changes are based on a clearer pattern

The validator now rejects additional safe-but-stiff user-facing phrases such as:

- concrete checkpoint
- logged session
- centered on the logged lifts
- concrete load and rep detail

These phrases are safe but too close to internal diagnostic copy for the target product voice.

## Product standard

Backend still owns facts, numbers, names, allowed claims, style boundaries, validation, and fallback.

The model may still provide phrasing, tone, synthesis, and transitions, but it must stay inside approved facts and approved coaching frames.

This pass does not mark product voice as complete. It moves the provider output closer to a true coach voice without weakening safety.
