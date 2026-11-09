# PR Review Agent Skill

A Claude Code skill that reviews pull requests and posts structured comments.

## Usage

```
/pr-review-agent --pr-url <url> [--post-comment]
```

Or as a standalone script:

```bash
node pr-review-agent.js --pr-url https://github.com/owner/repo/pull/123
```

## What it does

1. Fetches the PR diff and metadata from GitHub
2. Analyzes the changes for:
   - **Security issues** (secrets, hardcoded credentials, unsafe patterns)
   - **Performance concerns** (N+1 queries, large bundles, blocking operations)
   - **Code quality** (naming, complexity, missing tests)
   - **Breaking changes** (API changes, removed fields, type changes)
   - **Documentation** (missing README updates, missing changelog entries)
3. Posts a structured comment on the PR with:
   - Summary of changes
   - Review decision (Approve / Request Changes / Comment)
   - Categorized findings with severity levels
   - Actionable suggestions

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude Code skill definition |
| `pr-review-agent.js` | Node.js MCP server / standalone agent |
| `README.md` | Installation and usage guide |
| `test-pr.js` | Test suite with sample PR data |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub personal access token with `repo` scope |
| `GITHUB_API_URL` | No | Default: `https://api.github.com` |

## Example Output

```
## PR Review: #123 - Add user authentication

**Decision:** REQUEST_CHANGES

### Summary
Adds login/logout flow with session management across 15 files (+450/-50 lines).

### Security (HIGH)
- **Hardcoded secret:** `auth.js:42` contains `JWT_SECRET = "dev-secret-123"` — move to environment variable
- **No rate limiting:** Login endpoint lacks rate limiting — vulnerable to brute force

### Performance (MEDIUM)
- **N+1 query:** `userProfile.js:88` queries user roles inside a loop — batch fetch instead

### Code Quality (LOW)
- **Missing tests:** No test file for `authMiddleware.js`
- **Inconsistent naming:** `handleLogin` vs `handleAuth` — pick one convention

### Breaking Changes
- None detected

### Suggestions
1. Add rate limiting middleware to `/api/login`
2. Replace hardcoded JWT_SECRET with `process.env.JWT_SECRET`
3. Add unit tests for auth middleware (target: 80% coverage)
```

## Requirements

- Node.js 18+
- GitHub personal access token with `repo` scope
- No external npm dependencies

## Test

```bash
node test-pr.js
```

Runs the agent against a sample PR and verifies the output structure.
