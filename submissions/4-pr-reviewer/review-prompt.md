# PR Reviewer Agent for Claude Code

## Setup (2 steps)

```bash
cp claude-review ~/.claude/agents/pr-reviewer.py
chmod +x ~/.claude/agents/pr-reviewer.py
```

## Usage

In Claude Code:

```
> Review this PR: https://github.com/owner/repo/pull/123
```

Or as a CLI:

```bash
python3 claude-review --pr https://github.com/owner/repo/pull/123 | claude -
```

Set `GITHUB_TOKEN` env var to avoid API rate limits on the PR diff fetch.

## Sample Output

```markdown
### Summary
This PR adds JWT-based authentication with refresh token rotation. It introduces
two new API routes and a middleware that validates tokens on protected routes.

### Risks
- Refresh token is stored in localStorage — XSS-vulnerable. Prefer httpOnly cookie.
- No rate limiting on /api/auth/refresh — could be abused for token generation.

### Suggestions
- Move refresh token to httpOnly cookie with SameSite=Strict.
- Add a 5-request-per-minute rate limit on the refresh endpoint.
- Consider using the `jose` library instead of `jsonwebtoken` for Edge Runtime compatibility.

### Confidence
Medium — auth logic looks sound, but the token storage pattern is a known weakness.
```
