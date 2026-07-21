## PR Review: Add OAuth2 authentication flow with refresh token support

**PR:** [#452](https://github.com/example/api-server/pull/452) — **example/api-server**
**Author:** @jdoe  **State:** OPEN
**Total:** +320/-45 across 8 files

---

### Summary

This PR adds OAuth2 authentication with refresh token rotation to the API server. It introduces a new auth middleware, token storage in Redis, and updated login/register endpoints. The changes are well-structured across 8 files with clear separation of concerns.

---

### Changes by File

| File | Changes | Status |
|------|---------|--------|
| `src/middleware/auth.ts` | +120/-5 | ⚠️ Large |
| `src/services/token.ts` | +85/-0 | ✅ |
| `src/routes/auth.ts` | +45/-10 | ✅ |
| `src/models/User.ts` | +30/-15 | ✅ |
| `src/config/index.ts` | +15/-5 | ✅ |
| `src/utils/jwt.ts` | +25/-10 | ✅ |
| `tests/auth.test.ts` | +0/-0 | ✅ |
| `docker-compose.yml` | +0/-0 | ✅ |

---

### Identified Risks

- ⚠️ `src/middleware/auth.ts` has 120 additions — verify the middleware is not over-engineered
- ✅ PR has a clear description explaining the approach

---

### Improvement Suggestions

- 💡 Add test coverage for edge cases (expired tokens, malformed headers)
- 💡 Consider rate-limiting on the token refresh endpoint
- 💡 Document the OAuth2 flow in CONTRIBUTING.md

---

### Confidence Score

**Medium** — Well-structured but auth logic needs careful security review.
