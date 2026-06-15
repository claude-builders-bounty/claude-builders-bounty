## PR Review

### Summary
This PR adds a user authentication system with JWT-based login/register endpoints and middleware for protected routes. The implementation uses bcrypt for password hashing and follows RESTful conventions.

### Files Changed
| File | Lines | Type |
|------|-------|------|
| src/auth/login.ts | +65/-0 | new |
| src/auth/register.ts | +72/-0 | new |
| src/auth/middleware.ts | +38/-0 | new |
| src/auth/types.ts | +22/-0 | new |
| src/routes/auth.ts | +15/-0 | new |
| package.json | +3/-0 | dependency |

### Identified Risks
- **Risk**: JWT secret is hardcoded in the source code
  **Severity**: HIGH
  **File**: `src/auth/middleware.ts:5`
  **Suggestion**: Use `process.env.JWT_SECRET` with a validation check at startup.
- **Risk**: No rate limiting on login endpoint
  **Severity**: MEDIUM
  **File**: `src/routes/auth.ts:12`
  **Suggestion**: Add `express-rate-limit` middleware (e.g., 5 attempts per 15 min per IP).
- **Risk**: Passwords truncated by bcrypt at 72 bytes — no check for this
  **Severity**: LOW
  **File**: `src/auth/register.ts:28`
  **Suggestion**: Add a password length validation hint in the API docs.

### Improvement Suggestions
- **Suggestion**: Add refresh token rotation
  **File**: `src/auth/login.ts`
  **Why**: Long-lived JWTs without rotation are vulnerable to token theft.
  **How**: Issue a short-lived access token (15 min) + long-lived refresh token (7 days) with rotation.
- **Suggestion**: Add request validation schemas
  **File**: `src/routes/auth.ts`
  **Why**: Currently no validation for email format or password strength.
  **How**: Use `zod` schemas to validate request bodies before processing.

### Strengths
- Proper HTTP status codes used (201 for creation, 401 for unauthorized)
- Password hashing with bcrypt instead of plaintext storage
- Middleware architecture is clean and reusable
- Type definitions are separate from implementation

### Confidence Score
**Confidence: Medium**
The core logic is sound, but the hardcoded secret and missing rate limiting are significant concerns that should be addressed before production deployment.
