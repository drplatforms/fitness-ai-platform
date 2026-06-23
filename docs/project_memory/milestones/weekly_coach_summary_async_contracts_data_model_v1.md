# Weekly Coach Summary Async Contracts + Data Model v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: WEEKLY_COACH_SUMMARY_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED

Branch: feature/weekly-coach-summary-async-contracts-data-model-v1

## Goal

Define the safe backend-owned contracts, lifecycle vocabulary, fact boundary, candidate summary shape, approved summary shape, validation expectations, fallback expectations, and future persistence concepts for the selected Weekly Coach Summary async job.

This milestone follows the accepted Async Job Delivery Pattern / Playbook v1 and starts deterministic-first.

Explicit boundary phrases for project memory checks:

- contracts/data model only
- no provider runtime
- no persistence schema

## Scope

Implemented contracts only:

- WeeklyCoachSummaryJobStatus
- WeeklyCoachSummarySource
- WeeklyCoachSummaryConfidence
- WeeklyCoachSummaryPeriod
- WeeklyCoachSummaryFactBoundary
- WeeklyCoachSummaryContext
- CandidateWeeklyCoachSummary
- ApprovedWeeklyCoachSummary
- WeeklyCoachSummaryRuntimeMetadata
- WeeklyCoachSummaryJobRecord

## Boundary

This milestone does not implement Weekly Coach Summary generation, persistence, API routes, Streamlit UI, Developer Mode UI, provider runtime, worker, queue, scheduler, polling, automatic generation, normal Today display, or public/default weekly summary display.

Provider runtime is explicitly deferred.

## Safety rules

Approved summary contracts do not include raw provider output, rejected provider output, full prompt, raw context, raw database rows, raw notes, scratchpad, chain-of-thought, secrets, environment values, stack traces, or tracebacks.

Approved displayable output requires public_safe consistency.

Candidate output is not automatically approved.

## Validation

Focused model tests cover bounded weekly period construction, invalid period rejection, candidate/approved summary construction, public_safe/displayable consistency, enum constraints, required section validation, forbidden language rejection, sanitized runtime metadata, and contract-only job records.
