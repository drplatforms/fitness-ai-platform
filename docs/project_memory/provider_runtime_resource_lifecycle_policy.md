# Provider Runtime Resource Lifecycle Policy

## Policy status

Provider Runtime Resource Lifecycle Design v1 defines the project baseline for
local Ollama lifecycle behavior.

## Official Ollama behavior accounted for

- Ollama `/api/generate` and `/api/chat` support `keep_alive`.
- `keep_alive: 0` requests unload immediately after generation.
- A named model can also be unloaded manually through Ollama's unload behavior.
- The project must not assume memory is free after a provider call unless the
  lifecycle policy requests unload or a diagnostic confirms status.

## Project defaults

Environment settings:

- `FITNESS_AI_OLLAMA_KEEP_ALIVE`
  - default: `0`
  - examples: `0`, `30s`, `1m`, `5m`, `-1`
- `FITNESS_AI_OLLAMA_UNLOAD_AFTER_REQUEST`
  - default: `true`
- `FITNESS_AI_OLLAMA_ALLOW_MANUAL_STOP`
  - reserved for explicit dev workflows
- `FITNESS_AI_PROVIDER_LIFECYCLE_LOGGING`
  - default: `false`

Default local policy is conservative because Windows hosts Ollama and has limited
available resources. Large local models should use `unload_immediately` unless
the user explicitly chooses a short keepalive for repeated manual testing.

## Model size/risk classification

- `qwen2.5:3b`: medium / moderate resource risk
- `qwen3:8b` or other 7B/8B class models: large / high resource risk
- `qwen3:32b`: very_large / extreme resource risk

The default for 32B-class models is `unload_immediately` unless explicitly
overridden.

## Manual diagnostic/helper behavior

Developer-only tool:

```powershell
python tools/dev_ollama_lifecycle_diagnostics.py --policy
python tools/dev_ollama_lifecycle_diagnostics.py --status
python tools/dev_ollama_lifecycle_diagnostics.py --unload qwen2.5:3b
```

Rules:

- `--policy` prints safe lifecycle policy metadata.
- `--status` reads safe Ollama status metadata if `/api/ps` is reachable.
- `--unload <model>` targets only the named model.
- No helper kills arbitrary processes.
- No helper stops the Ollama server globally.
- No helper generates provider text.
- No helper dumps secrets or full environment values.

## Provider path inventory

Known direct Ollama paths before this milestone:

- `services/daily_coach_narrative_provider_service.py`
  - Daily Coach Narrative offline/provider generation path.
  - Now uses lifecycle helper payload construction for `/api/generate`.
- `services/ai_nutrition_explanation_service.py`
  - Nutrition Explanation direct Ollama provider path.
  - Now uses lifecycle helper payload construction for `/api/generate`.
- Training report direct Ollama paths reuse the Nutrition direct Ollama transport
  helper where applicable.

Weekly Coach Summary provider runtime remains not authorized.

## Downstream backlog

### Daily Narrative Provider Quality + Grounding v1

Provider wording still needs better human coach language and stronger factual
"because" grounding. Example desired direction:

- Because there are no nutrition entries for today, 2026-06-23, start with one
  simple meal or snack log.

This should be handled by backend facts, provider wording, strict validation, and
deterministic fallback. It is not implemented in this lifecycle milestone.

### Streamlit Theme Cleanup v1

Developer Mode/theme interactions can leak FSU-like colors into Today, Nutrition,
and Workout cards until hard refresh. This is separate UI cleanup.

### Workout Exercise Variety Rotation v1

Workout generation still repeats common exercises such as EZ bar curl, overhead
wood chop, band Pallof press, bodyweight squat, and RDL. Future work should add
anti-repeat/top-K rotation and exposure tracking.
