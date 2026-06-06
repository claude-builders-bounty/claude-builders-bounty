# claude-review — AI PR Code Review Agent

Automated PR analysis with structured output: risk detection, improvement suggestions, test coverage assessment, and merge verdict.

## Setup (3 steps)

```bash
# 1. Install
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/claude-review
chmod +x claude-review
sudo mv claude-review /usr/local/bin/

# 2. Set your API key
export ANTHROPIC_API_KEY='sk-ant-...'

# 3. Review any PR
claude-review --pr https://github.com/owner/repo/pull/123
```

## CLI Usage

```bash
# Basic review
claude-review --pr https://github.com/owner/repo/pull/123

# Use a specific model
claude-review --pr https://github.com/owner/repo/pull/123 --model claude-opus-4-20250514

# Save to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## GitHub Action

Copy `pr-review.yml` to `.github/workflows/` and add `ANTHROPIC_API_KEY` to your repo secrets.

The bot will automatically review every PR and post a comment.

## Example Output

```markdown
### Summary
This PR adds JWT-based authentication with refresh token rotation across 12 files. The implementation follows best practices for token storage and introduces a new middleware layer.

### Identified Risks
- **Risk**: Refresh token stored in localStorage (XSS vulnerable)
- **Risk**: Missing rate limiting on /api/auth/refresh endpoint

### Improvement Suggestions
- **Suggestion**: Use httpOnly cookies for refresh tokens (line 47, auth.ts)
- **Suggestion**: Add Zod validation schema for login payload (line 23, login.ts)

### Test Coverage Assessment
- What's tested: Token generation, expiry, user lookup
- What's NOT tested: Token refresh flow, invalid token handling
- Assessment: Needs Improvement

### Final Verdict
❌ **Changes Requested** — Address the XSS risk before merging.
```

## Bounty

[claude-builders-bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) — $150
