# Claude Code PR Review Agent

## Description
A Claude Code sub-agent that reviews GitHub PR diffs and posts structured Markdown review comments.

## Usage
```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## Features
- Fetches PR diff from GitHub API
- Analyzes code changes for:
  - Security vulnerabilities
  - Performance issues
  - Code style violations
  - Logic errors
  - Missing edge cases
- Produces structured Markdown report

## GitHub Action Support
Includes `.github/workflows/pr-review.yml` for automated review on every PR.

## Output Format
Each review includes:
1. Summary of changes (2-3 sentences)
2. Risks identified (numbered list)
3. Improvement suggestions (with code examples)
4. Strengths (what was done well)
5. Score out of 10

## Wallet (for payouts)
216Awm73cAhrw6HLQcNndHXcvvwNL9P6ymN3pgqu1Rh1
