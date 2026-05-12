# PR Reviewer Agent

`claude-review` fetches a GitHub pull request diff and returns a structured Markdown review comment.

## Setup

```bash
python3 -m venv .venv && . .venv/bin/activate
```

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

If the Claude Code CLI is installed, set `CLAUDE_REVIEW_USE_CLAUDE=1` to ask Claude to perform the review. Without that environment variable, the CLI uses a deterministic local analyzer so it remains testable in CI and offline development.

## Output Format

The command always returns Markdown with:

- summary of changes
- identified risks
- improvement suggestions
- confidence score: Low, Medium, or High

## Tested PRs

Sample outputs are included in:

- `samples/pr-1056-review.md`
- `samples/pr-1061-review.md`

Both were generated from real GitHub PR URLs in this bounty repository.
