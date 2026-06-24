# Provider Runtime Resource Lifecycle Design v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW
Branch: `feature/provider-runtime-resource-lifecycle-design-v1`

## Purpose

Define the project-level provider lifecycle policy before any additional qwen or
Weekly Coach Summary provider runtime work. The user observed that Ollama models
can remain loaded after Daily Coach Narrative generation and continue consuming
limited Windows resources. This milestone adds a conservative lifecycle policy,
small developer-only diagnostics, and a safe named-model unload helper.

## Scope completed

- Added `services/provider_lifecycle_service.py`.
- Added `tools/dev_ollama_lifecycle_diagnostics.py`.
- Added tests for policy defaults, keep_alive payload injection, safe unload, safe
  unreachable handling, and secret-free summaries.
- Updated direct Ollama Daily Coach Narrative payload construction to include the
  central lifecycle `keep_alive` policy.
- Updated direct Ollama Nutrition Explanation payload construction to include the
  central lifecycle `keep_alive` policy.
- Documented provider lifecycle policy and current provider path inventory.
- Captured downstream backlog for Daily Narrative quality/grounding, Streamlit
  FSU theme cleanup, and Workout exercise variety.

## Boundary

This milestone does not add Weekly Coach Summary provider runtime, qwen calls,
CrewAI orchestration, automatic generation, workers, queues, schedulers,
polling, or public/default UI display.

## Default policy

Default local Ollama policy is conservative: `FITNESS_AI_OLLAMA_KEEP_ALIVE`
defaults to `0`, which asks Ollama to unload the model after generation for
direct `/api/generate` calls that use the lifecycle helper.

Manual unload is explicit and targets only a named model through Ollama API. No
process killing, broad server termination, or environment dump behavior is added.
