# Claude PR Review Agent

`bin/claude-review` generates a structured Markdown review from a GitHub pull
request URL. It is designed for Claude Code workflows: Claude can run it as a
sub-agent style CLI, inspect the output, and optionally post it back to the PR.

## Setup

```bash
chmod +x bin/claude-review
gh auth status
```

## Usage

Print a review:

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
```

Post the generated review as a PR comment:

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

The output always includes:

- summary of changes
- identified risks
- improvement suggestions
- confidence score: Low, Medium, or High

## Validation

```bash
python3 -m unittest tests/test_claude_review.py
bin/claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/908
bin/claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/909
```
