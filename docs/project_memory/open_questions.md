# Open Questions

Last updated: 2026-06-22

## Current milestone

Daily Coach Async Approved Preview Bridge Design v1

## Open questions for Architecture review

1. Should the first future implementation use only `DAILY_COACH_ASYNC_APPROVED_PREVIEW_ENABLED=false`, or should it also require a test-user allowlist?
2. Should the preview label be `AI-assisted coach preview` or `Daily Coach Narrative Preview`?
3. Should the preview be hidden entirely when gates fail, or show a safe no-preview fallback message?
4. Which validator_version and prompt_contract_version compatibility policy should be used for the first implementation?
5. Should Developer Mode expose gate failure reasons from the bridge service in the same persistence inspection panel or a separate bridge diagnostics panel?

## Explicitly parked

- normal Today provider call
- provider execution on page load
- automatic async job generation
- public/default async narrative display
- worker / queue / scheduler / polling
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- raw provider output display/persistence
- rejected provider output display/persistence
- debug/provider metadata in normal UI

## Portfolio / LinkedIn / GitHub reminder

Portfolio update remains deferred for now. This design is portfolio-relevant, but the better update point is likely after a stable feature-flagged approved preview bridge implementation or a stable end-to-end persisted async workflow.
