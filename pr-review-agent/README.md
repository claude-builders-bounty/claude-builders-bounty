# Claude PR Review Agent

`claude-review` is a small CLI that turns a GitHub pull request diff into a structured Markdown review comment. It is designed to run from Claude Code or any shell with access to a public PR.

## Setup

```bash
chmod +x pr-review-agent/claude-review
ln -sf "$PWD/pr-review-agent/claude-review" /usr/local/bin/claude-review
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The command first tries `gh pr diff`. If `gh` is unavailable, it falls back to GitHub's public `.diff` URL. For offline review, pass a local unified diff:

```bash
claude-review --diff-file ./example.diff --output review.md
```

## Output Format

The generated comment always includes:

- Summary of changes in two or three sentences
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## Sample Outputs

Two real pull request runs are included:

- [`samples/claude-builders-bounty-1382.md`](samples/claude-builders-bounty-1382.md)
- [`samples/claude-builders-bounty-1395.md`](samples/claude-builders-bounty-1395.md)
