# Section Registry Summary

Last updated: 2026-06-20

## Purpose

This file summarizes the current maturity of major report/product sections and clarifies which areas are deterministic, provider-integrated, developer-preview only, or future-only.

## Current maturity table

| Surface / section | Current status | Provider status |
|---|---|---|
| Training Report Section | Full-report section with opt-in validated provider path | Provider-integrated with deterministic fallback |
| Nutrition Report Section | Level 5 provider-integrated on approved opt-in provider output | Provider-integrated with deterministic fallback |
| Nutrition Target Display | Backend-owned target display contract | Not provider-authored truth |
| Daily Next Action | Deterministic daily decision service | No provider decision authority |
| Today Coach Note | Deterministic normal Today card | No provider call on normal load |
| Coach's Read / Daily Coach Synthesis | Deterministic synthesis surface | No provider narrative display yet |
| Daily Coach Narrative Developer Preview | Developer Mode-only manual preview/debug lane | Manual/developer-gated only |
| Daily Coach Same-Session Approval | Reference-only failed branch | Not accepted |
| Workout Plan / Substitution / Count / Daily State | Deterministic workout experience | No provider programming |
| Food and Exercise Catalogs | Curated/imported deterministic canonical data | No AI-generated truth |
| Grounded Recommendation | Backend-approved recommendation contract | Not current provider voice section |

## Daily Coach distinction

Daily Coach surfaces are not report sections unless a future milestone explicitly designs them as report sections.

Keep these names distinct:

- Daily Next Action: what to do next, deterministic.
- Today Coach Note: short deterministic Today note.
- Coach's Read / Daily Coach Synthesis: deterministic synthesis.
- Developer Preview: Daily Coach Narrative: manual provider-preview diagnostics.
- Same-session approval bridge: not accepted, future retry only.

## Provider-integrated report sections

Only Training Report Section and Nutrition Report Section are currently provider-integrated report areas.

Provider integration means provider use is gated, output is parsed, output is validated, deterministic fallback remains available, raw/rejected output is not rendered, and persistence/status boundaries are explicit.

## Future candidates

Future candidates are not automatically approved:

- Daily Coach same-session approved display
- Daily Coach async narrative generation
- Unified Health State Snapshot
- RAG/vector memory
- MoE model routing
- MCP/tool architecture
- production frontend/deployment
