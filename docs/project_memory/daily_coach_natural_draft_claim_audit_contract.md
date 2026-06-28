# Daily Coach Natural Draft + Claim Audit Contract v1

Status: Active Backend implementation contract.

## Purpose

Daily Coach Natural Draft + Claim Audit v1 changes the provider experiment from a constrained writer into a freer writer with a stricter backend reviewer.

The core rule is:

Loosen the writer. Tighten the reviewer.

## Developer-only boundary

This workflow is developer-only. It does not replace normal Today behavior, does not promote OpenAI, and does not persist provider output into product data.

## Flow

ApprovedCoachBrief
→ natural coach draft
→ deterministic claim extraction
→ backend claim audit
→ one targeted repair attempt when safe
→ re-audit
→ final approved copy or deterministic fallback

## Backend authority

Backend remains final authority for facts, interpretations, claim registry, audit rules, repair limits, fallback, and approval.

## Writer authority

The writer may only draft natural copy from the ApprovedCoachBrief. It may not invent facts, foods, serving sizes, timing, targets, causality, medical claims, or user data.

## Claim audit

V1 audits high-risk claims including food identity, macro status, serving amount, timing, training intensity, recovery interpretation, causal language, addressing, medical/body claims, and judgment/motivation claims.

## Repair policy

One repair attempt is allowed. Repair output must be re-extracted and re-audited. Failed repair falls back deterministically.

## Artifacts

Default artifacts are sanitized and developer-only. They must not include raw provider output, secrets, env dumps, chain-of-thought, database rows, runtime feedback JSONL, qa_artifacts, snapshots, patch files, or apply scripts.


---

# V2 Addendum — Product Voice Audit

V2 adds a product-quality reviewer beside the factual claim reviewer. Claim Audit answers whether the copy is true and supported. Product Voice Audit answers whether it is useful, human, scenario-specific, and product-ready.

Required v2 artifacts include first-pass draft before audit, side-by-side comparison, product voice audit summary, repair delta summary, humanized fallback summary, and reviewer conclusion.

Final approval requires factual Claim Audit pass, Product Voice Audit pass, Food Action Language Contract pass, addressing policy pass, artifact safety pass, and humanized fallback quality if fallback is used.
