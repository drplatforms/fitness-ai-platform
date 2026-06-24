# Current implementation update - Weekly Coach Summary Provider Runtime Design v1

Weekly Coach Summary Provider Runtime Design v1 is implemented on
`feature/weekly-coach-summary-provider-runtime-design-v1` after accepted commit
`be2f321 Add provider runtime resource lifecycle policy`.

This is a design-only milestone. It defines the future provider runtime path for
Weekly Coach Summary using the accepted backend-owned selected QA date-range
context seam and accepted provider lifecycle policy.

The design defines:

- what qwen2.5:3b may receive
- what JSON schema qwen2.5:3b must return
- parser behavior
- validator behavior
- fallback behavior
- persistence boundary
- Developer Mode-only manual preview behavior
- lifecycle policy integration
- voice/tone contract
- grounding rules
- happy-path user 102 scenario
- low-data user 105 scenario
- out-of-range fallback behavior
- future prototype test plan

No provider runtime execution, qwen call, Ollama call for Weekly Coach Summary,
CrewAI orchestration, public/default display, normal Today display, automatic
generation, worker, queue, scheduler, polling, display of raw provider output, display of raw
context, prompt display, or persistence of rejected provider output is
added.

Known live QA window remains `2026-05-31` through `2026-06-06`.
