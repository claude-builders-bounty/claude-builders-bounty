# Claude PR Review Agent

A CLI tool that reviews GitHub PRs using Claude and posts structured review comments.

## Features

- Fetches PR diff and metadata from GitHub
- Analyzes changes using Claude AI
- Outputs structured Markdown review with:
  - Summary of changes (2-3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High
- Optionally posts review as a PR comment

## Installation

```bash
# Copy script to PATH
cp claude-review /usr/local/bin/
chmod +x /usr/local/bin/claude-review
```

## Prerequisites

- [GitHub CLI](https://cli.github.com/) authenticated (`gh auth login`)
- [Claude Code](https://docs.anthropic.com/claude-code) CLI installed

## Usage

```bash
# Review a PR (output to terminal)
claude-review --pr https://github.com/owner/repo/pull/123

# Review and post as comment
claude-review --pr https://github.com/owner/repo/pull/123 --post
```

## Example Output

```
📋 Fetching PR diff for owner/repo#123...

## Summary
Adds user authentication middleware with JWT validation and role-based access control. Includes error handling for expired tokens.

## Risks
- JWT secret stored in environment variable without rotation mechanism
- No rate limiting on auth endpoints

## Suggestions
- Add token refresh logic
- Include unit tests for edge cases
- Add logging for failed auth attempts

## Confidence: High

✅ Review posted to https://github.com/owner/repo/pull/123
```
