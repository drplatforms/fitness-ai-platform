# Weekly Coach Summary QA Data Context Integration v1 Review

Proposed status: WEEKLY_COACH_SUMMARY_QA_DATA_CONTEXT_INTEGRATION_V1_ACCEPTED

Review summary:

The Developer Mode QA Date Range Debug path now builds deterministic Weekly Coach Summary output from a backend-owned selected-range context seam rather than lightweight debug counts alone.

Acceptance checks:

- User 102 latest seeded week remains the happy path.
- User 105 latest seeded week remains the low-data/fallback path.
- Selected user/date provenance is preserved.
- Context includes safe aggregate facts, data quality, limitations, and reason codes.
- Raw rows, notes, food logs, workout set rows, prompts, scratchpad, secrets, and provider output are excluded.
- Lazy navigation remains intact.
- Runtime / DB Source Verification and QA Seed Data Verification CLI remain preserved.
- No provider runtime, Ollama, CrewAI, qwen, worker, queue, scheduler, polling, or automatic generation was added.
