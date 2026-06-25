# Daily Narrative Rich-Day Targeting + Context Differentiation v1

Status: implemented / ready for Architecture review.

Branch: `feature/daily-narrative-rich-day-targeting-context-differentiation-v1`

Purpose: prove Daily Narrative selected-date behavior before voice/model escalation. The app now has a Developer Mode diagnostic path that can scan seeded QA users/days, rank useful Daily Narrative test days, and show why a selected day is rich, low-data, or no-data.

Implemented:

- Daily Narrative rich-day service with safe aggregate candidate summaries.
- Richness score and labels for seeded QA days.
- Data-quality label and reason-code differentiation for selected days.
- Deterministic next-action selection that changes with selected facts.
- Generic meal/snack logging is selected only when selected facts support it.
- CLI scanner: `tools/dev_daily_narrative_rich_day_scan.py`.
- Developer Mode rich-day candidate display in Daily Narrative QA Preview.
- Context summary now exposes public-safe counts, reason codes, next-action reason, and rich-day label.
- Provider input receives selected-date reason codes through approved facts when manual provider preview is used.

Boundary:

- Normal/default Today behavior unchanged.
- No public/default Daily Narrative provider display.
- No automatic generation.
- No worker, queue, scheduler, polling, or background process.
- No CrewAI reintroduction.
- No qwen3:8b, 14B, or 32B promotion.
- No raw rows, food logs, check-in notes, workout set rows, prompts, scratchpad, or secrets exposed.

Validation focus:

- Rich day, low-data day, and no-data day should produce different context, reason codes, and deterministic preview behavior.
- User 102 should have a best available candidate day identified when the active runtime DB contains seeded data.
- User 105 remains cautious/data-quality-limited.
