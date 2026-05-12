# Sample Review 1: Small PR Adding a New API Endpoint

> This is a sample output from `claude-review` reviewing a PR that adds a new `/api/users/search` endpoint.

---

## PR Review: Add user search API endpoint

**PR**: #247 | **Author**: jdoe | **Branch**: `feat/user-search` -> `main`
**Changes**: +142/-3 across 4 files

### Summary

This PR adds a new `GET /api/users/search` endpoint that allows searching users by name or email with pagination support. The implementation introduces a new route handler in `src/app/api/users/search/route.ts`, adds a `searchUsers` function to the user service layer, and includes a corresponding database query with full-text search using PostgreSQL `ILIKE`. A new integration test file covers the primary success path and basic validation.

### Risk Assessment

| Risk | Severity | Details |
|------|----------|---------|
| SQL Injection via search parameter | High | `src/services/userService.ts:34` — The search term is interpolated into the SQL query string using template literals rather than parameterized queries. An attacker could craft a search term like `%'; DROP TABLE users; --` to execute arbitrary SQL. Use parameterized queries (`$1` placeholders) instead. |
| Missing rate limiting | Medium | `src/app/api/users/search/route.ts` — The search endpoint has no rate limiting. Since search queries can be expensive (full table scan with `ILIKE`), this could be abused for DoS. Consider adding rate limiting middleware. |
| Unbounded result set | Medium | `src/services/userService.ts:38` — The `limit` parameter accepts any positive integer from the query string. A request with `?limit=1000000` would attempt to load all users into memory. Cap the maximum limit (e.g., 100). |
| No authentication check | Medium | `src/app/api/users/search/route.ts:8` — The endpoint does not verify the user's session or API key. User email addresses are PII that should not be publicly searchable. Add authentication middleware. |

### Suggestions

1. **Use parameterized queries** (`src/services/userService.ts:34`)
   Replace the template literal SQL with parameterized query:
   ```ts
   // Before (vulnerable):
   const result = await db.query(`SELECT * FROM users WHERE name ILIKE '%${term}%'`);
   // After (safe):
   const result = await db.query('SELECT * FROM users WHERE name ILIKE $1', [`%${term}%`]);
   ```

2. **Cap the pagination limit** (`src/app/api/users/search/route.ts:15`)
   Add a maximum limit to prevent memory issues:
   ```ts
   const limit = Math.min(parseInt(searchParams.get('limit') || '20'), 100);
   ```

3. **Add authentication middleware** (`src/app/api/users/search/route.ts`)
   Wrap the handler with your existing auth middleware to prevent unauthorized access to user data.

4. **Add database index for search performance** (missing migration)
   The `ILIKE` query on `name` and `email` columns will perform a full table scan. Consider adding a GIN trigram index:
   ```sql
   CREATE INDEX idx_users_name_trgm ON users USING gin (name gin_trgm_ops);
   ```

5. **Test edge cases** (`src/__tests__/api/users/search.test.ts`)
   The test file only covers the happy path. Add tests for: empty search term, special characters in search, pagination boundary (page beyond results), unauthenticated requests, and SQL injection attempts.

### What Looks Good

- Clean separation between the route handler and service layer — the handler focuses on request/response, the service handles business logic.
- Pagination implementation follows the existing patterns in the codebase (`offset`/`limit` with total count in response headers).
- TypeScript types are well-defined for the search response schema.
- The integration test uses the existing test database factory helpers consistently.

### Confidence

**High**

The diff is small and self-contained (142 lines across 4 files), the endpoint follows standard REST patterns, and the risks identified (SQL injection, missing auth) are clearly visible in the diff without needing broader codebase context.

---
