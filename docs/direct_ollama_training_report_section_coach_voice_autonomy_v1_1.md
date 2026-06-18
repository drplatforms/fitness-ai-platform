# Direct Ollama Training Report Section Coach Voice Autonomy v1.1

## Status

Coach Voice Autonomy v1.1 is a targeted validator and prompt refinement on top of Coach Voice Autonomy v1.

It does not change the provider boundary, output schema, Streamlit, persistence, or full report integration.

## Why this exists

Runtime QA showed the semantic coaching move design gave qwen3 more expressive room, but qwen3 used that room to make an unsupported quality judgment such as `strong execution`.

That is useful signal:

- the model is no longer just copying finished coaching frames
- the fallback path worked
- the validator needed a tighter quality-claim boundary

## Changes

This milestone adds a narrow product/safety refinement:

1. Reject unsupported quality or execution claims, including:
   - strong execution
   - solid execution
   - good execution
   - clean execution
   - well-executed
   - strong performance
   - quality work

2. Require `section_summary` to synthesize the main training signal instead of restating exact load, rep, set, or RIR data.

3. Strengthen prompt guidance for `fatigue_recovery_interpretation` so it names the required workout and clearly states that the session does not prove a recovery or fatigue pattern.

4. Preserve semantic coaching moves. This milestone does not return to finished coaching frames.

## Intended runtime result

qwen2.5:3b should remain safe and acceptable.

qwen3:8b should have room to sound more natural, but should now be rejected if it drifts into unsupported quality language such as `strong execution` or `strong performance`.

Safe fallback remains the expected behavior for invalid candidates.

## Non-goals

This milestone does not:

- make direct Ollama default
- loosen validation
- require qwen3 to pass
- add full report integration
- change Streamlit
- change persistence
- call live Ollama from tests
- feed finished frontend copy back to the model
