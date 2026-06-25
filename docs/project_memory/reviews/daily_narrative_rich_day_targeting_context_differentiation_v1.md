# Review — Daily Narrative Rich-Day Targeting + Context Differentiation v1

Review status: ready for Architecture review.

The milestone adds diagnostic tooling and Developer Mode UI support to stop guessing Daily Narrative dates. It ranks seeded QA days by safe aggregate data richness and proves that selected date/range can alter Daily Narrative context, reason codes, next-action selection, deterministic preview, and provider input.

Key acceptance notes:

- Rich-day scan is read-only and provider-free.
- Selected-date context is backend-owned and typed.
- Context summary includes public-safe fact inventory only.
- Next-action logic now avoids defaulting to generic meal logging when nutrition and training facts are present.
- The provider path, when manually used, receives selected-date facts and reason codes through approved facts.
- Normal Today behavior remains unchanged.

Known environment note:

- If the local/sandbox database has no seeded rows, rich-day scan correctly reports no-data days. On the Linux runtime DB with seeded QA data, the scan should identify the best available user/date candidates.

Recommended next milestone:

Daily Narrative Voice + Grounding v1 after Architecture confirms context differentiation is working against the seeded runtime DB.
