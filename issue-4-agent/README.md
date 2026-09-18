# Claude PR Review Agent

A Claude Code sub-agent that takes a GitHub PR URL as input, extracts the diff, sends it to the Claude 3.5 Sonnet API for analysis, and outputs a structured Markdown review. It can also post the review directly to the PR using the `gh` CLI.

## Requirements
- Python 3
- `requests` library (`pip install requests`)
- Anthropic API Key
- GitHub CLI (`gh`) if you want it to post the comment automatically

## Setup

1. Export your Anthropic API Key:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

2. Make the script executable:
```bash
chmod +x claude-review.py
```

## Usage

**Dry run (print to console only):**
```bash
./claude-review.py --pr https://github.com/owner/repo/pull/123
```

**Post directly to GitHub PR:**
```bash
./claude-review.py --pr https://github.com/owner/repo/pull/123 --post
```

## Sample Output

```markdown
### Summary of Changes
This PR refactors the authentication module to use JWT tokens instead of session cookies. It introduces a new middleware for validating tokens and removes the old session storage logic.

### Identified Risks
- Storing JWTs in local storage makes them vulnerable to XSS attacks. Consider using httpOnly cookies instead.
- The token expiration time is currently set to 30 days, which might be too long for sensitive actions.

### Improvement Suggestions
- Consider adding token rotation or a refresh token mechanism.
- Ensure that the JWT secret is properly loaded from the environment variables and not hardcoded in development.

### Confidence Score
High
```
