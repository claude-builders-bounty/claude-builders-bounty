# claude-review

> A CLI tool that takes a GitHub PR URL, fetches the diff, and returns a structured Markdown review from Claude.

## Why

Reviewing PRs is time-consuming. `claude-review` automates the first pass: it fetches the diff, sends it to Claude, and returns a structured review with summary, risks, suggestions, and a confidence score.

## Setup (3 steps)

```bash
# 1. Install dependencies (none beyond Python 3.8+ stdlib!)
# 2. Get an Anthropic API key: https://console.anthropic.com/
export ANTHROPIC_API_KEY=sk-ant-...

# 3. (Optional) GitHub token for private repos / higher rate limits
export GITHUB_TOKEN=ghp_...

# 4. Make it executable and run
chmod +x claude-review.py
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

That's it. The review prints to stdout as Markdown.

## Usage

```bash
# Full URL
python claude-review.py --pr https://github.com/owner/repo/pull/123

# Short form
python claude-review.py --pr owner/repo#123

# Different model
python claude-review.py --pr https://github.com/owner/repo/pull/123 --model claude-3-5-haiku-20241022

# JSON output (for piping to other tools)
python claude-review.py --pr https://github.com/owner/repo/pull/123 --output json

# Save to file
python claude-review.py --pr https://github.com/owner/repo/pull/123 > review.md
```

## Example output

```markdown
## Summary
This PR adds a "forgot password" flow to the auth module using a one-time token emailed to the user. The implementation follows the existing auth patterns and reuses the email service for delivery.

## Risks
- The reset token is compared using `==` which is safe in Python (constant-time) but the comparison is not wrapped in a try/except for DB errors
- Tokens are never explicitly expired; only deleted on use. Stale tokens accumulate in the DB.
- The 1-hour expiry is hardcoded; should be configurable

## Suggestions
- Add a periodic cleanup job to delete expired tokens
- Move the token expiry to an env var or DB config
- Add rate limiting on the `/forgot-password` endpoint to prevent abuse
- Consider adding a "token used" flag instead of deleting, for audit logs

## Confidence
**Medium** — I can see the overall structure but the auth module has additional helpers I haven't fully traced. The risks are concrete but might miss some context-specific details.
```

## GitHub Action

You can also use this as a GitHub Action. See [`github-action.yml`](./github-action.yml).

## Files

| File | Purpose |
|---|---|
| `claude-review.py` | The CLI tool (zero external dependencies) |
| `github-action.yml` | Reusable GitHub Action workflow |
| `test_sample.py` | Unit tests for URL parsing |
| `examples/` | Sample outputs from real PRs |

## Testing

The tool is tested against:

- ✅ `https://github.com/TriggerXZ/generate-changelog/pull/1` (real PR in our own repo)
- ✅ `https://github.com/TriggerXZ/block-destructive-commands/pull/1` (real PR)

See [`examples/`](./examples/) for the actual outputs.

## Compatibility

- ✅ Linux, macOS
- ✅ Windows (Git Bash, WSL, native Python)
- ✅ Python 3.8+ (uses urllib + json, no requests/pydantic)
- ✅ Any public or private GitHub PR (with token)

## How it works

1. Parse the PR URL → extract owner/repo/number
2. Fetch PR metadata + raw diff via GitHub API
3. Truncate the diff to 100k chars (avoids API limits)
4. Build a structured prompt with PR title, description, and diff
5. Call Claude 3.5 Sonnet with the prompt
6. Print the review to stdout (or JSON)

## License

MIT
