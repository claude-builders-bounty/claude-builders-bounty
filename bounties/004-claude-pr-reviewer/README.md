# Claude PR Reviewer Agent

Self-contained Claude Code PR reviewer that accepts a GitHub pull request URL, fetches the PR metadata and diff, and returns a structured Markdown review comment.

The reviewer includes:

- `agent/pr-reviewer.md`: Claude Code subagent definition using Markdown frontmatter
- `bin/claude-review`: CLI wrapper that fetches PR data and sends the review prompt to Claude Code
- `examples/github-action.yml`: optional GitHub Action that posts the review as a PR comment
- `samples/`: local-mode review outputs generated from real GitHub PR diffs

## Setup

Install the Claude Code CLI and authenticate it, or provide `ANTHROPIC_API_KEY` in CI.

```bash
npm install -g @anthropic-ai/claude-code
```

Make the CLI executable if your checkout did not preserve file modes:

```bash
chmod +x bin/claude-review
```

## CLI Usage

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Run a deterministic local smoke test without calling Claude:

```bash
bin/claude-review --diff-file tests/sample.diff --mode local
```

Generate a sample from a real PR diff without spending Claude tokens:

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123 --mode local
```

## GitHub Action

Copy `examples/github-action.yml` to `.github/workflows/claude-pr-review.yml`, then add an `ANTHROPIC_API_KEY` repository secret. The workflow runs on pull requests, writes `review.md`, and posts it with `gh pr comment`.

## Output Format

The agent always returns:

- `## Summary` with 2 to 3 sentences
- `## Identified Risks`
- `## Improvement Suggestions`
- `## Confidence Score` with `Low`, `Medium`, or `High`

## Tests

```bash
bash tests/test_claude_review.sh
```
