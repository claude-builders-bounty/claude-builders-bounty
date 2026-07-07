# PR Review Agent

A Claude Code agent that reviews pull requests and generates structured feedback.

## Usage

```bash
./review-pr https://github.com/owner/repo/pull/123
# or
REPO=owner/repo ./review-pr "" 123
```

## Features

- Extracts and analyzes PR diffs
- Provides summary (files changed, additions/deletions)
- Checks for common issues (debug statements, TODOs, missing tests)
- Generates actionable recommendations
