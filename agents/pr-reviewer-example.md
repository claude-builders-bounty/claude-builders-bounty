# PR reviewer sub-agent example

Use this from Claude Code when you want a structured review comment:

```text
Use the pr-reviewer sub-agent to review PR #123. Inspect the diff, run available tests if safe, and return the Markdown comment. Do not post it.
```

Expected response shape:

```markdown
## PR Review

### Summary
- Adds a cache around user profile lookups.
- Updates tests for cache hit/miss behavior.

### Findings
| Severity | File/Line | Issue | Recommendation |
|---|---|---|---|
| medium | `src/profile.ts:42` | Cache key omits tenant id, so users from different tenants can collide. | Include `tenantId` in the cache key and add a cross-tenant regression test. |

### Tests / Verification
- ✅ `npm test -- profile` — passed locally.

### Risk Notes
- Main risk is stale or cross-tenant data if cache keys are incomplete.

### Recommendation
Request changes — fix tenant-safe cache key before merge.
```
