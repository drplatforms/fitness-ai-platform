# Daily Coach Async Provider Runtime QA Hardening v1

Status: AUTHORIZED FOR BACKEND / QA IMPLEMENTATION

Branch: `feature/daily-coach-async-provider-runtime-qa-hardening-v1`

Source baseline: `ea3f93f Fix provider runtime config default isolation`

Purpose: harden the Developer Mode-only Daily Coach async provider runtime prototype before any provider-enabled QA or Today preview bridge design.

Approved scope:

- deterministic failure result objects
- disabled config handling
- missing provider/model config handling
- missing job handling
- stale/expired job handling
- provider unavailable handling
- timeout handling
- malformed/prose/markdown-wrapped output handling
- schema mismatch and validation rejection handling
- bounded persistence failure handling
- Developer Mode-only sanitized status/error clarity

Boundary:

- Developer Mode-only runtime remains gated
- manual trigger only remains preserved
- provider disabled by default
- no provider call on normal Today render
- no provider call on page load
- no normal Today provider call
- no public async narrative display
- no automatic async job creation outside Developer Mode
- no worker/queue/scheduler/polling
- no qwen3 bridge
- no qwen3 promotion
- no qwen3:32b promotion
- raw provider output is not persisted or displayed
- rejected provider output is not persisted or displayed
- full prompt/raw context/scratchpad is not persisted or displayed
- deterministic fallback remains mandatory

Codex do not use by default.
