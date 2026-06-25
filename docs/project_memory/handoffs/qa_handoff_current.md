# QA Handoff Current

QA focus: Weekly Coach Summary Provider Runtime Prototype v1

Required checks:

- provider preview is Developer Mode-only
- no provider call on page open
- no provider call while only building context
- qwen2.5:3b only
- parser/validator/fallback behavior works
- rejected output is not approved/persisted
- deterministic fallback remains visible
- lifecycle unload status is visible after generation
- normal/default UI unchanged
