
# Next Async Job Candidate Selection v1 + lstop Tooling Hotfix Review

Final review status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status:
NEXT_ASYNC_JOB_CANDIDATE_SELECTION_V1_ACCEPTED

## Summary recommendation

Selected next async job candidate:
Weekly Coach Summary Async Job

Recommended first implementation milestone:
Weekly Coach Summary Async Contracts + Data Model v1

Why this candidate is best now:

- It is a clean async use case with high product value.
- It can start deterministic-first without provider runtime.
- It is naturally separate from normal Today page load behavior.
- It reuses the accepted Async Job Delivery Pattern / Playbook without trying to promote the Daily Coach provider path too quickly.
- It has strong portfolio/demo value because it turns approved backend facts into a useful weekly artifact.
- It can be scoped with clear contracts before persistence, provider runtime, preview bridge, or public/default behavior are considered.

This milestone also completed the bounded lstop CRLF tooling hotfix.

## lstop tooling hotfix

Issue addressed:

`lstop` could fail from Windows PowerShell with Bash seeing `true\r` instead of `true`.

Fix:

`scripts/fitness_commands.ps1` now LF-normalizes Linux command script content before SSH execution and transports the script as UTF-8/base64 into remote `bash -s`.

Why shared helper was touched:

`lstop`, `lrestart`, `lstatus`, `lpull`, and other Linux helper commands share `Invoke-FitnessLinux`. Fixing the transport boundary centrally is the smallest root-cause fix that prevents PowerShell CRLF conversion from reaching Bash.

Expected validation:

- `lstop` works from Windows PowerShell.
- `app` behavior is preserved because it still calls `lrestart`.
- `lrestart` behavior is preserved.
- No product/runtime behavior changes.

## Decision matrix

Scoring: 1 = weak, 5 = strong / favorable.

| Candidate | Product value | Pattern reuse | Implementation complexity | QA complexity | Provider/runtime risk | Normal UI risk | Portfolio/demo value | Dependency risk | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A. Daily Coach Approved Narrative Generation v2 | 4 | 5 | 3 | 3 | 2 | 2 | 4 | 4 | 27 |
| B. Weekly Coach Summary Async Job | 5 | 5 | 4 | 4 | 5 | 5 | 5 | 4 | 37 |
| C. Async Nutrition Explanation / Food Suggestion Enrichment | 4 | 3 | 3 | 3 | 3 | 4 | 3 | 2 | 25 |
| D. Async Workout Review / Training Execution Summary Narrative | 4 | 4 | 3 | 3 | 4 | 4 | 4 | 3 | 29 |

Interpretation:

- Higher Provider/runtime risk score means lower risk.
- Higher Normal UI risk score means lower risk.
- Higher Dependency risk score means fewer blocking dependencies.

## Candidate A — Daily Coach Approved Narrative Generation v2

Recommendation:
Defer.

Why deferred:

- It is closest to the current accepted provider path, but that is also the risk.
- It may tempt normal Today provider execution too early.
- It could blur the line between Developer Mode provider QA and user-facing Daily Coach behavior.
- It is better saved until the approved preview bridge has more soak time.

Potential future first milestone:
Daily Coach Approved Narrative Generation v2 Contracts + Data Model v1

## Candidate B — Weekly Coach Summary Async Job

Recommendation:
Select.

Why selected:

- Naturally async and weekly, not page-load driven.
- Can start deterministic-first using approved backend facts.
- Can avoid provider runtime in v1.
- Clean separation from normal Today behavior.
- Strong portfolio/demo value: weekly training/nutrition/recovery/adherence summary.
- Good fit for the new playbook because it needs contracts, service shell, persistence, inspection, and only later optional provider enhancement.

Recommended first milestone:
Weekly Coach Summary Async Contracts + Data Model v1

Minimum useful v1:

- define weekly summary target/context
- define input fact contract from approved backend sources
- define deterministic summary candidate structure
- define validator expectations
- define approved/public-safe weekly summary output contract
- define lifecycle/status concepts without implementing worker/queue/provider runtime

Provider requirement:
Not required for v1.

Preview bridge requirement:
Not required for first milestone. A preview bridge can be designed later after contracts, persistence, Developer Mode inspection, and QA exist.

## Candidate C — Async Nutrition Explanation / Food Suggestion Enrichment

Recommendation:
Defer.

Why deferred:

- Nutrition already has provider-related history and exact-schema experimentation that should be reviewed before adding another async path.
- It may collide with existing nutrition explanation/provider architecture.
- It is valuable but less clean as the first post-playbook async job.

Potential future first milestone:
Nutrition Async Explanation Source Review + Contract Alignment v1

## Candidate D — Async Workout Review / Training Execution Summary Narrative

Recommendation:
Defer, but keep as second-best candidate.

Why deferred:

- Good async shape and product value.
- Depends more heavily on workout execution maturity and planned-vs-actual data readiness.
- Could require product copy/behavior choices around adherence, missed reps, fatigue, and overtraining tone.

Potential future first milestone:
Workout Review Async Contracts + Data Model v1

## Selected candidate mapping to async playbook

Selected candidate:
Weekly Coach Summary Async Job

Required playbook stages for first path:

1. Weekly Coach Summary Async Contracts + Data Model v1
2. Weekly Coach Summary Service Shell / No Worker v1
3. Weekly Coach Summary Persistence Design v1
4. Weekly Coach Summary Persistence Contracts + Schema v1
5. Weekly Coach Summary Persistence Service Shell v1
6. Weekly Coach Summary Developer Mode Inspection v1
7. Weekly Coach Summary QA Hardening v1

Stages deferred:

- Provider Runtime Design
- Provider Runtime Prototype
- Provider Runtime QA Hardening
- Approved Preview Bridge Design
- Approved Preview Bridge Implementation
- Approved Preview Bridge QA
- Provider Live QA
- Public/default enablement decision

## Recommended v1 scope for selected candidate

Goal:
Define a weekly async summary contract that can later produce an approved weekly summary from backend-owned facts.

Owner:
Architecture / Backend Development

Required data concepts:

- weekly_summary_job_id
- user_id
- week_start_date
- week_end_date
- target_context or week_context_hash
- context_version
- summary_status
- generated_at timestamps, later
- approved_weekly_summary output contract, later
- deterministic fallback summary availability

Required input concepts:

- approved workout facts
- approved training execution facts
- approved nutrition actual/target facts, where available
- approved recovery/adherence facts, where available
- current plan context, if already backend-approved
- forbidden claims list
- safe summary tone constraints

Provider needs:
None for first milestone.

Developer Mode inspection needs:
Required before normal UI exposure.

Preview bridge needs:
Deferred.

QA gates:

- no provider call
- no page-load generation
- no automatic job creation unless explicitly authorized later
- deterministic summary/fallback remains available
- raw facts are not leaked into normal UI
- no debug/provider metadata in normal UI
- no qwen3/qwen3:32b promotion

## Explicit non-goals

This candidate selection milestone does not authorize:

- implementing Weekly Coach Summary Async Job
- provider runtime changes
- worker / queue / scheduler / polling
- normal Today provider execution
- provider execution on page load
- automatic async job generation
- public/default async display
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- raw provider output persistence
- rejected provider output persistence
- debug/provider metadata in normal UI

## Proposed next handoff

Recommended Architecture handoff:
Weekly Coach Summary Async Contracts + Data Model v1

Purpose:
Define contracts and data model concepts only for a deterministic-first weekly summary async job. Do not implement provider runtime, persistence schema, worker/queue/scheduler, preview bridge, or normal UI behavior in that first milestone.

## Boundary confirmation

- lstop tooling hotfix only: CONFIRMED
- app behavior preserved: CONFIRMED BY DESIGN / VALIDATE LOCALLY
- lrestart behavior preserved: CONFIRMED BY DESIGN / VALIDATE LOCALLY
- candidate selection only: CONFIRMED
- no selected async job implementation: CONFIRMED
- no runtime product behavior changed: CONFIRMED
- no provider behavior changed: CONFIRMED
- no Streamlit behavior changed: CONFIRMED
- no normal Today behavior changed: CONFIRMED
- no worker added: CONFIRMED
- no queue added: CONFIRMED
- no scheduler added: CONFIRMED
- no polling added: CONFIRMED
- no qwen3/qwen3:32b promotion: CONFIRMED
- no Codex used: CONFIRMED
