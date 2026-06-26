# Claude Review Agent

`claude-review` is a small Claude Code-style review agent that takes a GitHub
pull request URL, reads the PR metadata and diff, and prints a structured
Markdown review comment.

It is intentionally dependency-free: Python 3.10+ and network access to GitHub
are enough.

## Setup

```bash
chmod +x claude-review-agent/bin/claude-review
claude-review-agent/bin/claude-review --pr https://github.com/owner/repo/pull/123
```

Optional:

```bash
export GITHUB_TOKEN=ghp_...
claude-review-agent/bin/claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output format

The generated review includes:

- summary of changes in 2-3 sentences;
- identified risks;
- improvement suggestions;
- confidence score: Low, Medium, or High.

## How it works

1. Parses `owner/repo/pull/<number>` from the PR URL.
2. Fetches PR metadata and the `.diff` from GitHub.
3. Extracts changed files, additions, deletions, and patch hints.
4. Applies deterministic review heuristics for tests, docs, security-sensitive
   files, generated artifacts, and large changes.
5. Prints a Markdown review ready to paste as a GitHub PR comment.

## Examples

Sample outputs generated from real GitHub PRs are included in:

- `samples/review-pr-3046.md`
- `samples/review-pr-3047.md`
