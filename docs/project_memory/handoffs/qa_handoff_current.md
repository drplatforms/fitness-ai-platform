# QA Handoff Current — Weekly Coach Summary Date-Range QA Data Debug v1

QA should smoke Developer Mode only:

- normal/default UI hides Weekly Coach Summary QA data controls
- Developer Mode shows QA user/date-range controls
- user 102 latest seeded week can inspect, generate, save, and load
- user 105 latest seeded week falls back or limits confidence safely
- selected user/date range is honored by persistence
- raw rows, raw notes, raw food logs, raw workout set rows, provider output, prompts, raw context, scratchpad, and chain-of-thought are not displayed
- latency remains acceptable after the prior fragment-rerun fix
