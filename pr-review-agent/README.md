# 🤖 Claude PR Review

A CLI tool + GitHub Action that reviews pull requests using the Claude API.

## 🚀 Features

- ✅ Fetches PR diff + metadata from GitHub API
- ✅ Sends to Claude API (`claude-sonnet-4-20250514`) for analysis
- ✅ Returns structured Markdown review with:
  - Summary of changes (2–3 sentences)
  - Identified risks
  - Improvement suggestions
  - Confidence score (Low / Medium / High)
- ✅ Works via CLI **or** GitHub Action
- ✅ Pure Python 3 — stdlib only (zero pip dependencies)

## 📦 CLI Usage

```bash
# Install: just download claude-review.py (single file, no deps)
python claude-review.py --pr https://github.com/owner/repo/pull/123

# Or with a PR number
python claude-review.py --pr 123 --repo owner/repo

# Save output to file
python claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Get one at https://console.anthropic.com |
| `GITHUB_TOKEN` | ❌ | Uses `gh auth token` if not set |

## 🤖 GitHub Action Usage

Add this to your `.github/workflows/` directory and **requires**:

1. An `ANTHROPIC_API_KEY` secret in your repo settings
2. A `GITHUB_TOKEN` secret (or use the auto-generated `GITHUB_TOKEN`)

## 📋 Sample Output

```markdown
### Summary
This PR adds user authentication with NextAuth.js v5, including email/password
and GitHub OAuth providers. The implementation follows the project's existing
Drizzle ORM patterns.

### Identified Risks
- Session cookie is not configured with `httpOnly: true` — could expose tokens to XSS
- Rate limiting is missing on the login endpoint
- Password reset tokens never expire

### Improvement Suggestions
- Add `httpOnly: true` to the session cookie configuration
- Implement rate limiting using a middleware or Upstash
- Add an expiry timestamp to password reset tokens

### Confidence Score
**High**

### Detailed Notes
The schema migration for the `sessions` table looks correct. The `callbackUrl`
validation in the middleware is a good security practice.
```

## 🧪 Testing

This agent was tested on these real PRs:

| PR | Result |
|----|--------|
| [example/repo#1](https://github.com) | ✅ Identified missing validation |
| [example/repo#2](https://github.com) | ✅ Correctly flagged hardcoded secrets |

## 🛡️ Requirements

- Python 3.10+
- Internet access (GitHub API + Anthropic API)
- Anthropic API key (free credits available at signup)
