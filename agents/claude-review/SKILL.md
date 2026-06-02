# SKILL: PR Review Agent

## Description
Claude Code sub-agent that reviews a GitHub pull request and outputs a structured Markdown review comment.

## Invocation
```bash
claude-review --pr https://github.com/owner/repo/pull/123
claude-review --pr https://github.com/owner/repo/pull/123 --post
claude-review --diff ./local.diff --output review.md
```

## Input
- A GitHub PR URL (`--pr`) or a local diff file (`--diff`)
- Environment: `ANTHROPIC_API_KEY` (required), `GITHUB_TOKEN` (optional, for `--post`)

## Output
Structured Markdown review with:
1. **📋 Change Summary** — 2–3 sentence overview of changes
2. **⚠️ Identified Risks** — Bullet list of potential issues
3. **💡 Improvement Suggestions** — Bullet list of actionable improvements
4. **🏆 Code Quality Score** — Integer 1–10 with justification

## Model
`claude-sonnet-4-20250514`

## Dependencies
- Python 3.10+
- `anthropic` Python SDK
- `gh` CLI (for PR diff fetching)

## GitHub Action
Available at `.github/workflows/pr-review.yml` for automatic PR reviews on every pull request event.

## Example Output
See `examples/` directory for real review outputs.
