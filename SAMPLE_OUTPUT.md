# claude-review: Sample Outputs

## Sample 1 — PR from wbobbynmworley/claude-builders-bounty (#722)

**PR Title:** Add pre-tool-use hook to block destructive bash commands

**Review Output:**

```markdown
## Summary
This PR adds a Python-based pre-tool-use hook for Claude Code that intercepts dangerous bash commands before execution. The hook validates command patterns against a blocklist including filesystem-destructive commands (rm -rf /), SQL injection patterns (DROP TABLE), and git force-push. All blocked attempts are logged to `~/.claude/hooks/blocked.log`.

## Risks
- **Incomplete pattern matching**: Regex `DELETE FROM\s+(?!.*WHERE)` uses negative lookahead — test against edge cases like `DELETE FROM table1; DROP TABLE users; -- WHERE id=1`
- **No way to bypass**: Legitimate use cases (e.g., `git push --force` on a personal branch) have no escape hatch — consider adding an allowlist or confirmation prompt
- **Missing `rm -rf /**`: The root deletion pattern exists but `rm -rf /*` and `rm -rf .` patterns are absent

## Improvement Suggestions
- **Add `.gitignore` check**: Before blocking `rm -rf`, check if the target is inside a `.git` directory to allow safe cleanup
- **Add environment variable**: `HOOK_DEBUG=1` to log all (non-blocked) commands for verification without blocking
- **Consider signal-based exit**: Use `sys.exit(0)` on pass, `sys.exit(1)` on block — consistent with Claude Code hook protocol

## Confidence Score
Medium
```

---

## Sample 2 — Hypothetical feature PR

**Review Output:**

```markdown
## Summary
This PR adds user subscription management with three tiers (Free/Pro/Enterprise) and Stripe integration for billing. It introduces a new `subscriptions` table, a `SubscriptionManager` service class, and webhook handlers for Stripe events.

## Risks
- **Stripe webhook replay attack**: The webhook handler lacks a `stripe-webhook-secret` signature verification step — recommend adding `stripe.webhooks.constructEvent()` before processing
- **Missing database migration**: The `subscriptions` table schema is assumed but not included — PR should include `lib/db/migrations/0003_add_subscriptions.sql`
- **No retry logic on Stripe API calls**: If `stripe.subscriptions.create()` fails transiently, the user is left in an inconsistent state

## Improvement Suggestions
- **Add `is_active` guard**: In `SubscriptionManager.create()`, check if the previous subscription was cancelled before creating a new one to prevent duplicate billing
- **Unit tests for tier downgrade**: Test the edge case where a user downgrades mid-cycle — current implementation may not prorate correctly
- **Add rate limiting**: Stripe webhooks are public — add a basic IP allowlist or shared-secret verification

## Confidence Score
Low (significant security concerns — recommend fixing Stripe webhook verification before merge)
```
