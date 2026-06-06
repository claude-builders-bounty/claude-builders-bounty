# PR Reviewer Agent (Bounty #4)

A Claude Code sub-agent and CLI that reviews a GitHub pull request diff and returns a structured Markdown comment.

## What's included

| File | Purpose |
|------|---------|
| `.claude/agents/pr-reviewer.md` | Claude Code sub-agent definition |
| `claude_review.py` | Review engine (CLI entry point) |
| `claude-review` | Shell wrapper for `claude-review --pr <url>` |
| `.github/workflows/claude-review.yml` | GitHub Action that posts review comments |
| `tests/test_claude_review.py` | Regression tests |
| `samples/` | Example outputs from real PRs |

## Quick start

### CLI

```bash
chmod +x agents/pr-reviewer/claude-review
agents/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123
```

Optional: set `ANTHROPIC_API_KEY` for Claude-powered reviews. Without it, the tool uses deterministic static analysis and still returns the required Markdown structure.

### Claude Code sub-agent

Copy the agent into your project:

```bash
mkdir -p .claude/agents
cp agents/pr-reviewer/.claude/agents/pr-reviewer.md .claude/agents/
```

Then invoke it in Claude Code:

```
Review https://github.com/owner/repo/pull/123
```

Claude delegates to the `pr-reviewer` sub-agent, which fetches the diff and returns structured Markdown.

### GitHub Action

Copy the workflow into your repository root:

```bash
mkdir -p .github/workflows
cp agents/pr-reviewer/.github/workflows/claude-review.yml .github/workflows/claude-review.yml
```

Add `ANTHROPIC_API_KEY` to repository secrets for Claude-powered reviews. The action posts a comment on every opened, synchronized, or reopened pull request.

## Output format

Every review includes:

- **Summary of Changes** — 2–3 sentences
- **Identified Risks** — bullet list
- **Improvement Suggestions** — bullet list
- **Confidence Score** — `Low`, `Medium`, or `High`

## Requirements

- Python 3.8+
- `gh` CLI (recommended for private repos and authenticated access)
- Optional: `ANTHROPIC_API_KEY` for Claude API reviews

## Tests

```bash
python3 -m unittest agents/pr-reviewer/tests/test_claude_review.py
```

## Sample runs

See `samples/` for review output captured from real GitHub PRs in this repository.
