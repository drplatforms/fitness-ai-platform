# Product Vision

Last updated: 2026-06-18

AI Health Coach is a sectionized, backend-truth-first personal coaching platform.

The coach should speak colloquially and clearly while using strong technical coaching knowledge. It should feel personal and useful, get better as the user logs more data, and avoid vague generic coaching.

Core phrase:

> Sound right and be right.

## Long-term direction

The long-term flow is:

```text
raw user logs
→ backend-owned evidence
→ approved claims
→ sectionized report modules
→ deterministic fallback
→ optional provider voice
→ eventually qwen3 premium coach voice
→ future curated KB/RAG coaching support
```

## What quality means

A good report should:

- Explain what the backend can prove.
- Avoid unsupported extrapolation.
- Give a clear next step.
- Use plain, human language.
- Avoid robotic repetition.
- Avoid vague “wellness app” filler.
- Be useful even when data quality is limited.

## Future qwen/RAG position

qwen3 may eventually become the premium user-facing report voice, section by section. Curated knowledge bases and RAG may later support richer coaching. Neither qwen3 nor RAG should own truth. They should explain approved truth within section boundaries.
