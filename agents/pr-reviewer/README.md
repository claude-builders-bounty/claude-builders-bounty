# PR Reviewer Agent

Generate a structured Markdown review comment for a GitHub pull request.

## Setup

```bash
chmod +x agents/pr-reviewer/bin/claude-review
agents/pr-reviewer/bin/claude-review --pr https://github.com/owner/repo/pull/123
```

If the `claude` CLI is available, the command sends the PR title, body, and diff to Claude and prints a structured review. If `claude` is not installed or exits unsuccessfully, the command falls back to deterministic local diff analysis.

For deterministic output:

```bash
agents/pr-reviewer/bin/claude-review --offline --pr https://github.com/owner/repo/pull/123
```

If your local Python certificate store is broken, fix it first. As a last resort on a trusted network, add `--insecure-skip-verify`.

## Output

The review always uses these sections:

- `Summary`
- `Identified risks`
- `Improvement suggestions`
- `Confidence`

## Authentication

Public pull requests work without authentication. For private repositories or higher API limits, set:

```bash
export GITHUB_TOKEN=...
```

## Sample Runs

Two real PR outputs are included:

- `samples/pr-1854-review.md`
- `samples/pr-1855-review.md`

Regenerate them with:

```bash
agents/pr-reviewer/bin/claude-review --offline --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1854 --output agents/pr-reviewer/samples/pr-1854-review.md
agents/pr-reviewer/bin/claude-review --offline --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1855 --output agents/pr-reviewer/samples/pr-1855-review.md
```

## Local Test

```bash
python3 agents/pr-reviewer/tests/test_claude_review.py
```
