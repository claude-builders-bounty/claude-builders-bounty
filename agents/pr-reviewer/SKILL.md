---
name: pr-reviewer
description: Reviews a GitHub PR diff and returns structured Markdown review comments
---

# PR Reviewer Agent

Reviews pull requests via CLI.

## Usage
claude-review --pr https://github.com/owner/repo/pull/123

## What it reviews
- Security vulnerabilities
- Code quality and logic errors
- Performance issues
- Style and consistency

## Output
Structured Markdown with severity levels: Critical / Suggestion / Positive
