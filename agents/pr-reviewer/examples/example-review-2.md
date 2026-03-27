# PR Review: Add user API key management endpoint

**PR**: https://github.com/example/api-server/pull/234
**Author**: devcontributor42
**Reviewed by**: claude-review (Claude Code PR Reviewer Agent)
**Date**: 2026-03-25

---

## Summary

This PR adds a new REST endpoint (`POST /api/v1/users/:id/api-keys`) that allows authenticated users to generate, list, and revoke their own API keys. The implementation spans 4 files across the routes, middleware, and database layers. The feature works correctly for the happy path, but there are security concerns around key storage and rate limiting that should be addressed before merge.

## Identified Risks

- **Critical -- API keys stored in plaintext**: In `src/models/api_key.js` (line 34), the raw API key is stored directly in the database without hashing. If the database is compromised, all API keys are immediately usable. Keys should be hashed (e.g., SHA-256) with only a prefix stored for display purposes.
- **High -- No rate limiting on key generation**: The `POST /api/v1/users/:id/api-keys` endpoint has no rate limit. A compromised account could generate thousands of keys. Add a per-user rate limit (e.g., 10 keys max, 5 requests per minute).
- **Medium -- Missing authorization check for key revocation**: The `DELETE /api/v1/users/:id/api-keys/:keyId` route checks authentication but does not verify that `:id` matches the authenticated user. User A could revoke User B's keys by guessing the key ID.
- **Low -- No key expiration**: Generated keys never expire. Consider adding an optional `expires_at` field with a default TTL (e.g., 90 days).

## Improvement Suggestions

- `src/models/api_key.js` line 34: Hash the API key before storage. Show the full key only once on creation, then store `sha256(key)`. On validation, hash the incoming key and compare.
  ```js
  const hashedKey = crypto.createHash('sha256').update(rawKey).digest('hex');
  ```
- `src/routes/api_keys.js` line 12: Add ownership verification middleware before the delete handler:
  ```js
  router.delete('/:id/api-keys/:keyId', auth, verifyOwnership, deleteKey);
  ```
- `src/routes/api_keys.js` line 8: Add rate limiting middleware to the POST route. Use `express-rate-limit` or a similar package.
- `src/middleware/auth.js` line 45: The API key lookup queries the database on every request. Consider adding a short TTL cache (e.g., 60 seconds) using `node-cache` or Redis to reduce database load.
- Add integration tests for the authorization edge cases: cross-user key revocation, expired tokens, rate limit exhaustion.

## File-by-File Notes

| File | Status | Notes |
|------|--------|-------|
| src/routes/api_keys.js | Needs Changes | Missing rate limiting and ownership check on DELETE |
| src/models/api_key.js | Critical | API keys stored in plaintext -- must hash before storage |
| src/middleware/auth.js | Needs Changes | API key lookup should be cached; no expiration check |
| migrations/20260324_add_api_keys.sql | OK | Schema is clean, proper indexes on user_id and key columns |

## Confidence Score

**High**

The diff is focused (4 files, ~180 lines) and the domain is well-understood (API key management is a common pattern). The security issues identified are well-established anti-patterns with clear remediation steps.
