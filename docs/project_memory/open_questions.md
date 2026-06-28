# Open Questions — Daily Coach Product Voice Audit Calibration + Final Approval Gate Fix v1

## Active

1. Does the focused patch block final approval when fallback fails Product Voice Audit?
2. Does `reviewer_conclusion=fallback_failure` prevent final approved copy from being emitted?
3. Does Product Voice Audit stop assigning product readiness 5 to backend-shaped but factually safe copy?
4. Does repair handle product-voice-only problems before fallback?
5. Does stable_comparison repair food/display wording while preserving valid first-pass specificity?
6. Do side-by-side artifacts clearly show `fallback_blocked` and `no_approved_copy` states?
7. Does the patch avoid turning Product Voice Audit into a pre-generation writer cage?

## Closed/unchanged boundaries

- Natural Draft + Product Voice Audit remains developer-only.
- Normal Today behavior is unchanged.
- Existing provider endpoint behavior is unchanged unless explicitly scoped later.
- Deterministic remains default.
- OpenAI/direct_ollama remain explicit opt-in/evaluation-only.
- Backend remains final authority for facts, claim audit, product voice audit, repair limits, fallback, and approval.
- Raw provider output is not written by default.
- No public UI, Streamlit provider controls, RAG, embeddings, meal planning, workout generation, recovery score changes, worker, scheduler, or queue are included.
