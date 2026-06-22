# Claude PR Review Agent

This agent generates a structured Markdown review from a GitHub PR diff.

## Setup

1. Copy `bin/claude-review` and `scripts/claude_review.py` into a repository.
2. Run `bin/claude-review --pr https://github.com/owner/repo/pull/123`.
3. Paste the generated Markdown into the PR conversation.

## Output Format

Each review includes:

- Summary of changes in two sentences
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## Claude Code Usage

Ask Claude Code to run:

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
```

Claude should then inspect the generated Markdown, adjust any project-specific nuance, and post the final comment only after the user approves.
