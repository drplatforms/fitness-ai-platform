# Daily Coach GPT Family Human Voice Trial v1

Status:

```text
DAILY_COACH_GPT_FAMILY_HUMAN_VOICE_TRIAL_V1_IMPLEMENTATION_COMPLETE
```

Baseline:

```text
05313fd Merge daily coach human voice prompt contract v1
```

Reason for this milestone:

Daily Coach Human Voice Prompt Contract v1 made the provider-preview prompt human-editable and rerunnable without Python patching. This milestone adds a developer-only GPT-family/OpenAI trial lane so the same user-owned prompt and raw backend payload can be tested against configurable GPT-family model IDs.

Implemented files:

```text
services/openai_human_voice_prompt_preview_service.py
tools/dev_daily_coach_gpt_family_human_voice_trial.py
tools/dev_daily_coach_human_voice_prompt_preview.py
tests/test_openai_human_voice_prompt_preview_service.py
tests/test_dev_daily_coach_gpt_family_human_voice_trial_tool.py
tests/test_dev_daily_coach_human_voice_prompt_preview_tool.py
models/daily_coach_human_voice_prompt_preview_models.py
services/daily_coach_human_voice_prompt_preview_service.py
```

Project-memory files updated:

```text
docs/project_memory/current_state.md
docs/project_memory/next_milestone.md
docs/project_memory/project_state.json
docs/project_memory/milestones/daily_coach_gpt_family_human_voice_trial_v1.md
```

Accepted behavior:

- Daily Coach Human Voice Prompt Contract v1 remains the accepted baseline.
- The human-editable prompt remains user-owned.
- The raw provider-preview payload remains the data source.
- GPT-family model IDs are configurable through CLI arguments.
- `OPENAI_API_KEY` is read from the environment and must not be printed.
- OpenAI/GPT-family output is raw trial evidence only.
- The single-preview tool supports `--provider openai`.
- The multi-model trial tool supports comma-separated `--models`.
- One unavailable/failing model does not stop the whole comparison.
- Optional artifacts are written only behind `--output-dir`.
- OpenAI Responses API requests use `model` and `input` only.
- No JSON schema, tools, web search, file search, code interpreter, function calling, structured output, or product parsing is enabled.

Raw output boundaries:

- Provider output is preserved raw.
- Provider output is not parsed.
- Provider output is not validated.
- Provider output is not scored.
- Provider output is not rejected or approved.
- Provider output is not persisted by default.
- Provider output is not converted into Daily Coach Note public copy.

Anti-cage boundaries:

The code must not inject:

```text
GOOD_STYLE_EXAMPLES
BAD_STYLE_EXAMPLES
DAILY_COACH_NARRATIVE_JSON_SCHEMA
Sentence 1:
Sentence 2:
Final sentence:
Return exactly these six keys
```

Developer workflow:

```text
python tools/dev_daily_coach_human_voice_prompt_preview.py --provider openai --model gpt-5.5 --user-id 102 --target-date 2026-06-14 --prompt-file docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md
```

Multi-model workflow:

```text
python tools/dev_daily_coach_gpt_family_human_voice_trial.py --models gpt-5.4-mini,gpt-5.4,gpt-5.5 --user-id 102 --target-date 2026-06-14 --prompt-file docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md
```

Fake-provider smoke:

```text
python tools/dev_daily_coach_gpt_family_human_voice_trial.py --models fake-gpt-a,fake-gpt-b --user-id 102 --target-date 2026-06-14 --prompt-file docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md --mock-output
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
- No OpenAI behavior outside explicit developer CLI.

Architecture review request:

Confirm whether this implementation is accepted as the developer-only GPT-family/OpenAI human voice trial lane.
