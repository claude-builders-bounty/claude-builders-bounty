# Claude PR Review Agent

Small CLI that generates a structured Markdown review comment for a GitHub PR.

## Setup

1. Install/authenticate GitHub CLI: `gh auth login`
2. Put this folder on PATH or run directly: `./claude-review`
3. Run: `./claude-review --pr https://github.com/owner/repo/pull/123`

## Output

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

The agent uses `gh pr view` + `gh pr diff`, then applies deterministic heuristics. It is safe for CI and local usage because it only reads PR metadata/diff.
