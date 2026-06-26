# AI Health Coach

AI Health Coach is a validation-first health coaching platform built with Python, FastAPI, Streamlit, SQLite, and local LLM provider integration through Ollama.

The system combines deterministic backend health, nutrition, recovery, and training logic with provider-integrated AI report sections. AI output is not rendered directly. Provider responses are parsed, validated, and either approved for user-facing display or replaced with deterministic fallback content.

Core principle:

> Backend owns the facts. AI writes only within approved context. Validators decide what reaches the user.

> **Disclaimer:** This project is for software engineering, experimentation, and personal productivity purposes. It is not medical advice, nutrition counseling, or a replacement for a qualified healthcare professional, registered dietitian, or certified coach.

---

## Project Overview

AI Health Coach is designed around the idea that useful AI coaching should be grounded in structured data, deterministic calculations, and backend validation rather than unrestricted model output.

The backend owns:

- logged nutrition values
- recovery check-ins
- workout and training data
- health-state construction
- macro target calculations and display permissions
- training constraints
- approved evidence claims
- parser and validator rules
- deterministic fallback behavior
- public-safe persistence and status boundaries

AI providers may generate bounded report language only from backend-approved context. Provider output must pass strict parsing and validation before anything becomes user-facing.

The goal is not to build a generic fitness chatbot. The goal is to build a serious backend-driven coaching platform where AI can improve explanation quality without bypassing deterministic safety and correctness rules.

---

## Current Status

The current accepted project baseline is a local-first, validation-first AI Health Coach with deterministic backend truth, provider-gated report sections, and increasingly complete daily/product workflow surfaces.

Current accepted capabilities include:

- deterministic Daily Next Action
- deterministic Today Coach Note
- deterministic Coach's Read / Daily Coach Synthesis
- Developer Mode-only Daily Coach Narrative preview diagnostics
- provider-integrated Training Report Section under strict validation/fallback
- provider-integrated Nutrition Report Section under strict validation/fallback
- workout substitution UX
- workout exercise count preference
- workout daily state lifecycle cleanup
- catalog import/source evaluation foundations
- initial reviewed food and exercise catalog batches
- Supercharger/session-brief tooling
- project memory and stale-doc checks

Current AI/provider boundaries:

- deterministic behavior remains the default
- provider preview lanes remain manual/developer-gated unless explicitly promoted later
- qwen3 models are not production-promoted
- qwen3:32b is a future premium coach candidate only
- no Daily Coach provider narrative persistence is approved
- no same-session approval bridge is accepted

Honest coverage note:

The app is not a production healthcare system. It is a local-first engineering project demonstrating backend-owned truth, deterministic fallbacks, strict provider validation, and controlled local LLM experimentation.
## What It Does

AI Health Coach currently supports:

- recovery check-ins
- nutrition logging
- canonical food search and logging
- formula-derived macro target display
- target-vs-actual nutrition tracking
- nutrition food suggestions
- workout logging
- exercise catalog search and filtering
- workout plan preview
- workout substitution flow
- workout size preference for Quick / Standard / Full sessions
- workout daily state lifecycle cleanup
- workout execution tracking
- health-state display
- Daily Next Action
- Today Coach Note
- Coach's Read / Daily Coach Synthesis
- Daily Grounded Recommendation
- AI health report generation
- latest report and report history views
- provider-integrated Training Report Section
- provider-integrated Nutrition Report Section
- Developer Mode diagnostics for provider preview/runtime inspection

The app is local-first and currently designed for controlled development, QA, and portfolio demonstration rather than production healthcare use.
## Architecture


## Complex Feature Development Workflow

For complex backend or user-visible behavior, the canonical workflow is:

```text
diagnostic
→ failing/coverage test
→ narrow implementation
→ targeted validation
→ prior-regression validation
→ original smoke reproduction
→ project memory update
→ Architecture acceptance
```

Do not treat generic green tests as sufficient if the product-critical path is not represented.

Use the risk-based process model from `docs/project_memory/milestones/test_first_quality_gate_development_plan_v1.md`:

- Low-risk: normal patch and focused validation.
- Medium-risk: light diagnostic, focused test, narrow patch, regression validation, smoke if user-visible.
- High-risk: diagnostic first, failing/coverage test, narrow patch, regression validation, original smoke reproduction, Linux/browser smoke when runtime-relevant, project memory update, Architecture acceptance.

Bigger milestone is okay. Bigger single patch is not okay.

Repeated patch loops must be tied to newly understood failures, diagnostics, failing tests, lint/pre-commit failures, or smoke regressions. If a stop condition triggers, pause and return a diagnostic handoff to Architecture instead of continuing blind patching.

The project follows a validation-first pipeline:

```text
User data
→ backend-derived health state
→ deterministic targets and constraints
→ approved provider context
→ local LLM candidate output
→ strict parser
→ backend validator
→ approved report section or deterministic fallback
→ public-safe rendering

## Project memory and north-star docs

The long-term technical north star is preserved in `docs/project_memory/future_architecture_ledger.md`.

The premium product/backend blueprint is preserved in `docs/project_memory/premium_platform_blueprint.md`.

These documents record direction only. They do not authorize RAG, vector search, MoE/model routing, MCP/tool interfaces, frontend rewrite, deployment rewrite, provider persistence, or model promotion without scoped milestones and Architecture acceptance.
