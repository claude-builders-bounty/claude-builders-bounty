# pr-reviewer — Claude Code agent for structured PR reviews

A Claude Code sub-agent that takes a PR diff and returns a structured Markdown
review comment: summary, risks, suggestions, confidence.

## Files

```
agents/pr-reviewer.md      # the Claude Code sub-agent definition
bin/claude-review          # CLI: claude-review --pr <github-pr-url>
workflows/pr-review.yml    # GitHub Action: review every opened PR
examples/                  # real reviews generated against real PRs
```

## Setup

```bash
# copy the agent into your project (or ~/.claude/agents for global use)
cp agents/pr-reviewer.md your-repo/.claude/agents/

# make the CLI runnable
chmod +x bin/claude-review
```

Requires the `claude` CLI (Claude Code) on PATH. For private repos or higher
rate limits, set `GITHUB_TOKEN`.

## Usage — CLI

```bash
claude-review --pr https://github.com/owner/repo/pull/123
# or review a local diff:
claude-review --diff examples/httpx-3699.diff
```

## Usage — GitHub Action

Copy `workflows/pr-review.yml` into `.github/workflows/` and add an
`ANTHROPIC_API_KEY` repository secret. Every opened/synchronized non-draft PR
gets a structured review comment.

## Usage — as a sub-agent in Claude Code

Once installed in `.claude/agents/`, ask Claude Code:

> "Use the pr-reviewer agent to review PR #123"

## Output format

```markdown
## Summary
2–3 sentences on what the PR does.

## Risks
- concrete, diff-grounded risks ("None identified." if genuinely none)

## Suggestions
- actionable improvements with file/line references

## Confidence: Low | Medium | High
```

## Sample outputs (real PRs)

- [encode/httpx#3699 — expose `FunctionAuth`](examples/review-httpx-3699.md)
  (diff: `examples/httpx-3699.diff`)
- [encode/httpx#3690 — `.wait_ready` parser for clean disconnects](examples/review-httpx-3690.md)
  (diff: `examples/httpx-3690.diff`)
