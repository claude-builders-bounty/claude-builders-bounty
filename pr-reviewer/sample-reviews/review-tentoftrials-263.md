# PR Review: TentOfTrials/TentOfTrials#263

**Title:** refactor: extract authentication module from monolithic UserService
**Author:** contributor123
**URL:** https://github.com/TentOfTrials/TentOfTrials/pull/263

---

### Summary of Changes
This PR extracts authentication logic from the monolithic UserService into a separate AuthService class. The refactor moves ~456 lines and removes ~191 lines, creating a cleaner separation of concerns. New helper methods are introduced for token validation and password hashing.

### Identified Risks
- **Breaking API changes**: External callers of `UserService.authenticate()` will break. Need to verify all call sites updated.
- **Exception swallowing**: The new `catch (AuthException e)` blocks log but don't rethrow in some paths.
- **OOM vulnerability**: Token cache lacks size limit; unbounded growth could cause OOM in long-running services.
- **Missing null checks**: `user.getPasswordHash()` may return null for OAuth-only users but isn't checked.
- **Thread safety**: New `TokenStore` uses HashMap without synchronization.

### Improvement Suggestions
- Add `@Deprecated` annotation to old `UserService.authenticate()` for migration period.
- Add unit tests for token expiration edge cases (clock skew, leap seconds).
- Implement cache size limit with LRU eviction in `TokenStore`.
- Add integration test covering OAuth-only user login flow.
- Document the new `AuthService` API in README.

### Confidence Score
**High** — Identified risks are concrete and actionable based on visible code patterns.

### Overall Verdict
**Changes Requested** — Address exception handling and thread safety before merge.
