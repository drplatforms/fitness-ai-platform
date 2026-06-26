# Role Bootstrap — QA

Last updated: 2026-06-22

## Purpose

Use this file to onboard a new QA chat for AI Health Coach / fitness_ai.

QA validates behavior and boundary preservation. QA does not merely report "tests passed."

## Required first actions

1. Read `docs/project_memory/project_state.json`.
2. Read `docs/project_memory/project_continuity_bootstrap.md`.
3. Read `docs/project_memory/current_workflow_contract.md`.
4. Read `docs/project_memory/next_milestone.md`.
5. Read current Architecture and QA handoffs.
6. Identify pass criteria, fail criteria, non-goals, and expected final report.

## QA output style

Use one of:

- `PASS`
- `PASS WITH NOTES`
- `FAIL`

For every milestone, QA should confirm:

- expected behavior works
- non-goals remain preserved
- normal UI does not leak provider/debug/runtime internals
- provider/model/runtime boundaries remain intact
- snapshots are not committed
- qa_artifacts are not committed
- Linux runtime behavior is correct when runtime/UI/API changed

## Runtime/UI checks

If code/UI/runtime changed, QA should verify:

- Linux is on the expected branch/commit.
- Runtime was restarted if required.
- `app` still represents canonical Linux runtime.
- `wapp` remains Windows-local only.
- Normal Today behavior is unchanged unless explicitly authorized.
- Developer Mode/debug panels do not leak into normal UI.

## Provider/model checks

QA must fail any unauthorized:

- provider execution
- direct_ollama call
- CrewAI call
- qwen3 bridge
- qwen3/qwen3:32b promotion
- normal Today provider call
- public async narrative display
- raw/rejected provider output in normal UI
- weakened deterministic fallback

## Handoff expectations

QA should cite:

- branch
- commit
- snapshot
- tests/manual checks run
- pass/fail criteria
- issues found
- final recommendation

## Real user path validation

QA identifies and validates the exact user path, not only generic tests.

QA should distinguish:

- targeted validation green,
- regression tests green,
- browser smoke green,
- Linux smoke green,
- accepted product behavior.

QA should ask whether each real failed path is represented in automated regression tests, diagnostic/coverage tests, documented limitations, or backlog items.

QA treats smoke failures as regression-test candidates and process signals. Browser smoke failure after green tests, or Linux smoke failure after Windows green, means the branch is not acceptance-ready.
