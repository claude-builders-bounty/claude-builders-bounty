# PR Review Agent

Structured PR review helper for Claude Code and GitHub Actions.

## Setup

```bash
export PATH="$PWD/agents/pr-reviewer/bin:$PATH"
```

## CLI Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Post the generated Markdown as a PR comment:

```bash
GITHUB_TOKEN=ghp_xxx claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

## GitHub Action

The workflow in `.github/workflows/claude-pr-review.yml` can be run manually with a PR URL. It generates the same structured review and posts it as an issue comment.

## Output Format

- Summary of changes in 2-3 sentences.
- Identified risks.
- Improvement suggestions.
- Confidence score: `Low`, `Medium`, or `High`.

## Samples

See `samples/` for outputs generated against two real GitHub PRs.
