# PR Review Agent

CLI agent that takes a GitHub PR URL, reads the diff, and prints a structured Markdown review comment.

## Setup

```bash
chmod +x pr-review-agent/claude-review
```

## Usage

```bash
pr-review-agent/claude-review --pr https://github.com/owner/repo/pull/123
```

The output includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: `Low`, `Medium`, or `High`

## How It Works

The CLI fetches the public `.diff` version of the pull request and applies deterministic review heuristics for common risks:

- Large diffs
- Credential-like additions
- Dynamic execution such as `eval()` or `exec()`
- Accidental focused/skipped tests
- Migration changes without rollback guidance
- GitHub Actions workflow changes

The result is designed to be pasted directly as a GitHub PR review comment.

## Local Test

```bash
python pr-review-agent/test_claude_review.py
```

## Sample Runs

Sample outputs from two real GitHub PR URLs are included in:

- `samples/fastify-pr-6239.md`
- `samples/claude-builders-pr-927.md`
