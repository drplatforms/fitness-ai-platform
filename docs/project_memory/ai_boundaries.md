# AI Boundaries

Last updated: 2026-06-18

## Current provider status

| Provider/model | Status |
|---|---|
| deterministic | Default and fallback |
| direct_ollama / qwen2.5:3b | Practical supported opt-in for Training only |
| qwen3 | Experimental only |
| CrewAI full-report coordinator | Legacy coordinator path; can fail; not future product voice owner |

## Provider-integrated sections

Current provider-integrated full-report section:

- `training`

No other full-report section should call direct_ollama unless Architecture explicitly approves a new provider boundary.

## Provider output rules

Provider output must be parsed, validated, and converted into approved section content before rendering or persistence.

Provider output must not expose:

- Raw model output.
- Raw prompts.
- Raw provider payloads.
- Parser internals.
- Validator internals.
- Tracebacks or exceptions.
- Debug fields.

## qwen3 rule

qwen3 is promising for future product voice but remains experimental. Do not promote qwen3, make it default, or use it as a truth owner.
