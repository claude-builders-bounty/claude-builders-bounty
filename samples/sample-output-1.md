# PR Review: Add user authentication with JWT tokens

**Repository:** claude-builders-bounty/demo-repo
**PR:** #42
**URL:** https://github.com/claude-builders-bounty/demo-repo/pull/42
**Review generated:** Claude claude-sonnet-4-20250514

---

## Summary

This PR introduces JWT-based authentication with login/register endpoints, middleware for route protection, and token refresh logic. It replaces the existing session-based auth and adds ~350 lines across 8 files. The implementation follows a standard pattern with access + refresh tokens.

## Identified Risks

- **Secret hardcoded in config sample** — the JWT_SECRET in config.example.py should note it must be at least 32 chars in production
- **No token revocation** — refresh tokens are stored in memory only, so a server restart invalidates all active sessions; consider a DB-backed approach
- **Rate limiting missing on /login** — no rate limiting on the login endpoint opens the door to brute force attacks
- **Password validation is too permissive** — passwords shorter than 6 chars are accepted in the current validation

## Improvement Suggestions

- Add `python-jose[cryptography]` to requirements for better JWT handling
- Extract the token expiry constants into environment variables instead of hardcoding 30 min / 7 days
- Use `httponly` cookies for token delivery instead of response body to reduce XSS surface
- Add a `User-Agent` check or CAPTCHA on the login route

## Confidence Score

**Medium** — The core auth flow is well structured, but several security hardening items need attention before production use.
