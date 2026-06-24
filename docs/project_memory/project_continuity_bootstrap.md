# Current implementation update - Provider Runtime Resource Lifecycle Design v1

Provider Runtime Resource Lifecycle Design v1 is implemented on
`feature/provider-runtime-resource-lifecycle-design-v1` after accepted commit
`0fd327d Restore weekly QA selected-range persistence controls`.

This milestone defines the project-level Ollama lifecycle policy and adds a
small developer-only diagnostic/helper layer. Direct Ollama payload construction
for Daily Coach Narrative and Nutrition Explanation now uses the central lifecycle
helper so `keep_alive` is explicit instead of relying on Ollama default residency
behavior.

Current default:

- `FITNESS_AI_OLLAMA_KEEP_ALIVE=0` when unset
- `FITNESS_AI_OLLAMA_UNLOAD_AFTER_REQUEST=true` when unset
- manual unload helper targets only a named model
- diagnostics do not generate provider output or dump secrets

Backlog captured:

- Daily Narrative Provider Quality + Grounding v1
- Streamlit Theme Cleanup v1
- Workout Exercise Variety Rotation v1

Weekly Coach Summary provider runtime remains not authorized until a separate
Provider Runtime Design milestone is accepted.
