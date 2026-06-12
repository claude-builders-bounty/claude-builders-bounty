# Claude PR Review Agent

`claude-review` generates a structured Markdown review from a GitHub PR diff.
The same review contract is also available as a Claude Code sub-agent in
`.claude/agents/pr-reviewer.md`.

## Setup

```bash
install -D -m 755 agents/claude-review ~/.local/bin/claude-review
claude-review --pr https://github.com/owner/repo/pull/123
```

## Output

The review includes:

- 2-3 sentence summary of the PR diff
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## GitHub Action

If you prefer a comment bot, use [.github/workflows/pr-review.yml](../.github/workflows/pr-review.yml).
It fetches the PR diff, runs the agent, and posts the rendered Markdown back to the pull request.

## Examples

Sample outputs are in `agents/samples/`.

## Verified PRs

The bundled samples were generated from two real GitHub PRs:

- `https://github.com/cli/cli/pull/1`
- `https://github.com/fastapi/fastapi/pull/12592`

Use `agents/scripts/verify-real-prs.sh` to re-run both reviews and compare them to the stored outputs.
