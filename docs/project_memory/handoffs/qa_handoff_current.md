# QA Handoff Current

Current milestone: Daily Coach Async Persistence Design v1

Status: DESIGNED / READY FOR ARCHITECTURE REVIEW

Branch: `feature/daily-coach-async-persistence-design-v1`

## QA focus

QA should review the persistence design and confirm boundary preservation.

PASS if the design defines:

- what should be persisted
- what must never be persisted
- job lifecycle storage model
- approved narrative storage model
- rejected/raw provider output policy
- public-safe metadata policy
- stale/expired/displayable policy
- context hash/versioning strategy
- Developer Mode vs normal Today boundary
- future implementation sequencing

FAIL if the branch implements or authorizes:

- DB schema
- migrations
- tables
- repositories
- services
- API routes
- Streamlit behavior
- provider runtime
- direct_ollama calls
- CrewAI calls
- qwen3 calls or bridge
- qwen3:32b promotion
- worker / queue / scheduler / polling
- normal Today provider calls
- public async narrative display
- raw provider output persistence
- rejected provider output persistence

## QA validation expectation

Automated validation should remain docs-only/project-memory scoped.

Manual runtime restart is not required unless product/runtime files changed unexpectedly.
