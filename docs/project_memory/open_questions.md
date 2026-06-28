# Open Questions — Daily Coach Natural Draft + Product Voice Audit v2

## Active

1. Is the first-pass GPT-5.5 natural draft better than deterministic fallback when given a richer approved brief?
2. If first-pass draft is weak, is the cause model behavior, brief thinness, prompt framing, or missing approved context?
3. If first-pass draft is decent but final copy is worse, is quality lost during claim audit, repair, fallback, or final approval?
4. Does Product Voice Audit catch factually safe but poor coaching copy?
5. Does Food Action Language Contract prevent mechanical food actions such as "add dry oats" or "use canned tuna"?
6. Does humanized fallback stay factual while avoiding old deterministic sludge?
7. Does reviewer_conclusion make the next bottleneck clear enough for Architecture/QA to route the next milestone?

## Closed/unchanged boundaries

- Natural Draft + Product Voice Audit is developer-only.
- Normal Today behavior is unchanged.
- Existing provider endpoint behavior is unchanged unless explicitly scoped later.
- Deterministic remains default.
- OpenAI/direct_ollama remain explicit opt-in/evaluation-only.
- Backend remains final authority for facts, claim audit, product voice audit, repair limits, fallback, and approval.
- Raw provider output is not written by default.
- No public UI, Streamlit provider controls, RAG, embeddings, meal planning, workout generation, recovery score changes, worker, scheduler, or queue are included.
