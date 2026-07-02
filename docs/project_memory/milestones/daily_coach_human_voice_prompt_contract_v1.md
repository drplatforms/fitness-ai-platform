# Daily Coach Human Voice Prompt Contract v1

Status:

```text
DAILY_COACH_HUMAN_VOICE_PROMPT_CONTRACT_V1_IMPLEMENTATION_COMPLETE
```

Baseline:

```text
d5bfd29 Merge daily coach provider preview raw data payload v1
```

Rejected predecessor context:

```text
Daily Coach Provider Preview Runtime Spike v1 was rejected for voice failure.
```

Reason for this milestone:

The rejected runtime spike proved that provider plumbing can work, but the prompt path was not fit for purpose. The model behaved like a backend JSON/payload summarizer instead of a health and fitness coach.

This milestone moves Daily Coach voice iteration out of Python strings and into a human-editable prompt markdown file.

Implemented files:

```text
models/daily_coach_human_voice_prompt_preview_models.py
services/daily_coach_human_voice_prompt_preview_service.py
tools/dev_daily_coach_human_voice_prompt_preview.py
tests/test_daily_coach_human_voice_prompt_preview_service.py
tests/test_dev_daily_coach_human_voice_prompt_preview_tool.py
docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md
```

Project-memory files updated:

```text
docs/project_memory/current_state.md
docs/project_memory/next_milestone.md
docs/project_memory/project_state.json
docs/project_memory/milestones/daily_coach_human_voice_prompt_contract_v1.md
```

Accepted behavior:

- The user owns final prompt wording.
- The Daily Coach voice prompt lives in `docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md`.
- The prompt file is human-editable.
- The prompt can be edited and rerun without Python patching.
- The developer tool loads the prompt file and appends the raw provider-preview payload JSON.
- Provider input shape is:

```text
<human prompt file text>

---

RAW_BACKEND_PAYLOAD_JSON:
<pretty JSON from DailyCoachProviderPreviewRawDataPayload>
```

- The developer tool prints prompt/input metadata and raw model output to terminal.
- `--mock-output` supports deterministic smoke testing without Ollama.
- `--print-provider-input` prints the complete prompt-plus-payload input for inspection.
- Provider output is preserved raw.
- Provider output is not parsed.
- Provider output is not validated.
- Provider output is not scored.
- Provider output is not rejected or approved.
- Provider output is not persisted.

Anti-cage boundaries:

The code must not inject:

```text
GOOD_STYLE_EXAMPLES
BAD_STYLE_EXAMPLES
EXAMPLE SHAPE ONLY
FOCUS_TO_COPY_EXACTLY
FACT_STRINGS_FOR_USED_FACTS
DAILY_COACH_NARRATIVE_JSON_SCHEMA
Sentence 1:
Sentence 2:
Final sentence:
Return exactly these six keys
```

Product/runtime boundaries:

- No Today UI changes.
- No Streamlit UI layout changes.
- No API route changes.
- No database schema changes.
- No migrations.
- No persistence behavior changes.
- No report behavior changes.
- No recommendation behavior changes.
- No Daily Next Action behavior changes.
- No Daily Coach Note public copy changes.
- No workout plan changes.
- No nutrition target changes.
- No automatic deload behavior.
- No automatic progression behavior.
- No wearable/HRV integration.
- No medical interpretation.
- No provider promotion.
- No model approval.
- No RAG/vector/agent behavior.
- No CrewAI behavior.
- No OpenAI behavior.

Developer workflow:

```text
python tools/dev_daily_coach_human_voice_prompt_preview.py --user-id 102 --target-date 2026-06-14 --model qwen2.5:3b --prompt-file docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md
```

Fake-provider smoke:

```text
python tools/dev_daily_coach_human_voice_prompt_preview.py --user-id 102 --target-date 2026-06-14 --model fake-model --prompt-file docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md --mock-output --print-provider-input
```

Architecture review request:

Confirm whether this implementation is accepted as the developer-only human-editable Daily Coach prompt iteration baseline.
