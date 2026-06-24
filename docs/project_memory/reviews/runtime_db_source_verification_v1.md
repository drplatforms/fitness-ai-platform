# Runtime / DB Source Verification v1 Review

Proposed status: RUNTIME_DB_SOURCE_VERIFICATION_V1_ACCEPTED

## Review focus

Confirm the app can safely report active runtime identity, database source, and QA seed presence/date bounds in Developer Mode only.

## Acceptance checks

- Developer Mode panel exists.
- Normal/default UI does not show diagnostics.
- Runtime identity is safe and sanitized.
- Database path/existence/connectability is visible.
- QA users 101-105 aggregate counts/date bounds are visible without raw rows.
- CLI can run on Windows and Linux.
- No provider runtime is called.
