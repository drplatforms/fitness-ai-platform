# Open Questions

## Weekly Coach Summary Persistence Latency Investigation v1

Current status:
Weekly Coach Summary Persistence Latency Investigation v1 is implemented and ready for Architecture review.

Resolved:

- Root cause was strongly narrowed to Streamlit full-app rerun behavior during Developer Mode button interactions.
- A targeted Streamlit fragment-rerun fix was added for the Weekly Coach Summary Developer Mode panel.
- Developer Mode-only timing diagnostics were added.
- A CLI latency probe was added for the deterministic backend path.

Open after acceptance:

- QA should confirm Linux runtime generate/save/load timing is now acceptable.
- If any interaction remains above 5 seconds, Architecture should decide whether to investigate other app-wide rendering costs before preview bridge work.

## Still deferred

- public/default Weekly Coach Summary display
- normal Today integration
- provider runtime
- automatic weekly generation
- worker/queue/scheduler/polling
## Weekly Coach Summary follow-up

- Should the next milestone deepen QA range context into richer deterministic fact summaries?
- Should focused Linux runtime QA come before approved preview bridge design?
- Public/default display, normal Today integration, provider runtime, automatic generation, and worker/queue/scheduler/polling remain deferred.
