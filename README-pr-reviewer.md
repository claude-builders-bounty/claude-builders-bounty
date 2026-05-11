# Claude Review PR Agent

`claude-review` is a Claude Code-friendly CLI agent that reviews a GitHub pull request and returns a structured Markdown review comment.

It works without paid API credentials by using deterministic review heuristics over PR metadata, changed files, and the diff. Claude Code can run it, inspect the output, and post or refine the review.

## Setup

```bash
chmod +x claude-review
```

Optional when `gh` is not on PATH:

```bash
export GH_BIN=/path/to/gh
```

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Write output to a file:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output format

The review includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## Requirements

Preferred:

- GitHub CLI authenticated with `gh auth login`

Fallback:

- `GH_TOKEN` or `GITHUB_TOKEN` for direct GitHub API requests

## Notes

This agent does not post comments by itself. That is intentional: it keeps review publication human-approved and avoids noisy bot spam.
