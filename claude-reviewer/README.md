# Claude PR Review Agent

CLI agent that reviews a GitHub PR and prints a structured Markdown comment.
It uses Claude when `ANTHROPIC_API_KEY` is set, with a deterministic local fallback for offline testing.

## Setup + usage

1. Install GitHub CLI and authenticate: `gh auth login`.
2. Optional: export `ANTHROPIC_API_KEY` for Claude-powered review.
3. Run:
   ```bash
   ./claude-review --pr https://github.com/owner/repo/pull/123
   ```
4. Copy the Markdown output into the PR comment, or redirect it to a file.

## Output format

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High
