# Claude PR Reviewer

Claude Code sub-agent that reviews GitHub PRs and posts structured Markdown comments.

## Features

- 📝 **Summary** — 2-3 sentence description of changes
- ⚠️ **Risks** — identified security, logic, or architecture risks
- 💡 **Suggestions** — actionable improvement recommendations
- 📊 **Confidence** — Low / Medium / High assessment

## Usage

### CLI

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Review a PR
bash claude-review.sh https://github.com/owner/repo/pull/123
```

### GitHub Action

1. Add `ANTHROPIC_API_KEY` to your repo's Secrets (Settings → Secrets → Actions)
2. Copy `action.yml` to `.github/workflows/pr-review.yml`
3. Copy `claude-review.sh` to your repo root

PRs are automatically reviewed on open and push.

## Output Example

```markdown
### Summary
This PR adds user authentication with JWT tokens and a login endpoint. It includes
password hashing with bcrypt and session management middleware.

### Risks
- JWT secret is hardcoded in config — should use environment variable
- No rate limiting on login endpoint — vulnerable to brute force
- Password reset flow is missing

### Suggestions
- Add rate limiting middleware to auth routes
- Move JWT_SECRET to environment variable
- Add input validation for email format

### Confidence
High
```

## Requirements

- `gh` CLI (authenticated)
- `curl`
- `jq`
- `ANTHROPIC_API_KEY` environment variable

## How It Works

1. Fetches PR metadata and diff via `gh` CLI
2. Sends diff to Claude API with structured review prompt
3. Returns formatted Markdown with summary, risks, suggestions, and confidence score
