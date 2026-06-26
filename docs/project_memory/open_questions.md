# Open Questions

## Rolling multi-refresh novelty

Workout Preview Full-Slot Rotation v1 accepted immediate previous-preview anti-repeat only.

Rolling multi-refresh novelty is deferred to Workout Preview Rolling Exposure Rotation v2.

Open question: should long-window exercise exposure tracking be session-only, persisted, or derived from selected workout history?

## Full exercise eligibility

Exercise Catalog Utilization / Specialized Movement Coverage v1 improved deterministic catalog breadth and specialized movement reachability, but it did not complete the full eligibility model.

Future work remains:

- Exercise Eligibility Matrix v1.
- Catalog Reachability Audit v2.
- complete catalog reachability.
- deeper movement-family de-duplication.
- clearer equipment/movement-pattern compatibility rules.

## Provider strategy roadmap

Provider strategy remains pending.

Possible future planning should compare local-first `qwen` / `direct_ollama` paths with higher-tier OpenAI/provider adapter options, but no provider strategy implementation is authorized by the current docs-only process milestone.

Provider may propose. Backend validates. User sees only approved output.

## Complex milestone process tuning

The current process doctrine is now: bite by bite, just bigger bites.

Open questions for future process/tooling work:

- Should dev assistant generate complexity scores for proposed milestones?
- Should dev assistant generate expected file-change budgets automatically?
- Should stop-condition handoffs get a repo-owned template?
- Should feature branch validation check whether the original smoke failure has a corresponding regression or diagnostic test?

## Daily Narrative feedback hardening

The first feedback-driven deterministic copy hardening pass is implemented. A future milestone may decide whether to continue provider-facing examples and validation prompt guidance, or pause Daily Narrative while workout/catalog/nutrition systems continue maturing.

## Feedback storage lifecycle

The v1 feedback store is local JSONL and should not be committed by default. A future milestone may decide whether selected approved examples should be manually promoted from runtime feedback into project-memory docs. Raw runtime JSONL should not be committed.

## Model selection

Do not treat bad copy or strict-schema failures as a model-size issue by default. The current priority is better approved context, stricter contracts, deterministic fallback, diagnostics, and well-scoped provider experiments.
