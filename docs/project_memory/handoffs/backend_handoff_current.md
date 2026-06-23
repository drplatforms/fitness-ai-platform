# Backend Handoff — Daily Coach Async Approved Preview Bridge Design v1

Status: `DESIGNED / READY FOR BACKEND / ARCHITECTURE REVIEW`

Branch: `feature/daily-coach-async-approved-preview-bridge-design-v1`

## Backend review focus

Review the design for future implementation feasibility only.

Expected future implementation shape:

- read-only backend bridge service
- feature flag disabled by default
- Today reads only already-approved persisted narratives
- strict eligibility gates
- sanitized Developer Mode diagnostics separate from normal UI
- no provider execution from Today
- no automatic job creation from Today

## Backend non-goals for this milestone

No runtime code changes. No Streamlit Today changes. No provider runtime changes. No persistence schema changes. No app/wapp command changes.

Codex do not use by default.
