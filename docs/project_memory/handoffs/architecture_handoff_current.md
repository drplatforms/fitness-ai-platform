# Architecture Handoff — Daily Coach Async Approved Preview Bridge Design v1

Status: `DESIGNED / READY FOR ARCHITECTURE REVIEW`

Proposed final status: `DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_DESIGN_V1_ACCEPTED`

Branch: `feature/daily-coach-async-approved-preview-bridge-design-v1`

Source baseline: `3765314 Merge feature/daily-coach-async-provider-runtime-qa-hardening-v1`

## Summary

Designed a future controlled bridge from Developer Mode-only approved Daily Coach async narratives into a possible Today preview path.

The design defines preview eligibility gates, Today preview boundary, provider execution boundary, fallback behavior, normal UI vs Developer Mode metadata boundary, feature flag strategy, QA gates, and future implementation sequencing.

## Boundary

Design only. No Today preview bridge implemented. No normal Today behavior changed. No provider call added to Today. No public async narrative display added. No worker/queue/scheduler/polling added. qwen3 and qwen3:32b remain unauthorized.

## Review request

Please review `docs/project_memory/designs/daily_coach_async_approved_preview_bridge_design_v1.md` and accept as:

`DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_DESIGN_V1_ACCEPTED`
