# Claude Review Agent

This repository includes a dependency-light Claude Code PR review agent for the bounty in #4.

## Setup

1. Ensure Python 3.10+ is available.
2. Optional: set `GITHUB_TOKEN` to avoid unauthenticated GitHub API rate limits.
3. Run `bin/claude-review --pr https://github.com/owner/repo/pull/123`.

## Usage

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
bin/claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
bin/claude-review --pr https://github.com/owner/repo/pull/123 --comment
```

The generated Markdown always includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## GitHub Action

`.github/workflows/claude-review.yml` shows how to run the agent automatically on pull requests and post the structured review as a comment.

## Claude Code Sub-Agent

`.claude/agents/pr-reviewer.md` defines a reusable Claude Code agent that calls the CLI, then asks Claude to sanity-check and refine the review before posting.

## Validation

Run:

```bash
python -m unittest tests/test_claude_review.py
```

Sample outputs from real public PRs are in `examples/`.
