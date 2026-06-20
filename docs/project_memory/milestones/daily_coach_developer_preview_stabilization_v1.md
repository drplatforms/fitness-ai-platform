# Daily Coach Developer Preview Stabilization v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW.

This milestone stabilizes the existing Daily Coach / Developer Preview surface before any same-session approval work is retried. It starts from accepted `main` and intentionally excludes same-session approval.

Implemented scope:

- kept `Coach’s Read for Today` / Daily Coach Synthesis visible in the Today flow
- verified the deterministic `/daily-coach/{user_id}/synthesis` route contract with route tests
- kept the existing Developer Mode-only `Developer Preview: Daily Coach Narrative` manual panel
- fixed mixed-type Developer Mode preview diagnostics rendering by coercing dataframe values to strings before Streamlit/PyArrow rendering
- added sanitized `developer_diagnostics` to Daily Coach narrative preview responses
- documented the preview debug route wrapper shape
- added tests proving normal Today card source does not call provider preview
- added tests proving no same-session approval controls exist in this milestone

Boundaries preserved:

- no same-session approval
- no `Approve for this session` button
- no provider narrative display in normal Today UI
- no provider call on normal Today load
- no persistence or schema changes
- no model/provider promotion
- no Daily Next Action, workout, nutrition, catalog, or report behavior changes

Preview debug route shape:

```text
GET /daily-coach/{user_id}/narrative-preview/debug

{
  "success": true,
  "daily_coach_narrative_preview": {
    "user_id": 102,
    "date": "YYYY-MM-DD",
    "next_action_id": "...",
    "next_action_title": "...",
    "workflow_target": "...",
    "provider_enabled": true|false,
    "provider_attempted": true|false,
    "selected_provider": "deterministic|direct_ollama",
    "selected_model": "...",
    "parse_success": true|false,
    "validation_success": true|false,
    "fallback_used": true|false,
    "fallback_reason": "...",
    "approved_narrative": null|object,
    "deterministic_fallback_note": "...",
    "approved_focus": "...",
    "context_summary": {},
    "latency_ms": 0,
    "developer_diagnostics": {
      "provider_enabled": true|false,
      "provider_attempted": true|false,
      "selected_provider": "...",
      "selected_model": "...",
      "parse_success": true|false,
      "validation_success": true|false,
      "fallback_used": true|false,
      "fallback_reason": "...",
      "approved_narrative_returned": true|false
    }
  }
}
```

`developer_diagnostics` is sanitized and excludes raw provider output, prompts, stack traces, and rejected text.
