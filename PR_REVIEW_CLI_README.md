# claude-review PR review CLI

`claude-review` is a Claude Code-friendly CLI/agent that fetches a public GitHub PR diff and returns a structured Markdown review comment.

## Setup

```bash
chmod +x bin/claude-review
```

## Usage

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
```

Output includes a summary, identified risks, improvement suggestions, and a Low/Medium/High confidence score.

## Tested PRs

Sample outputs are included in `examples/review-pr-731.md` and `examples/review-pr-734.md`.
