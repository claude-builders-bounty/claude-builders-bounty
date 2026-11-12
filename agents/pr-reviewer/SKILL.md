---
name: claude-pr-reviewer
description: Automated sub-agent that reviews GitHub pull requests and generates structured Markdown reviews with risk analysis and recommendations.
---

# Claude Code Sub-Agent: PR Reviewer

Reviews pull request diffs, checks for potential security bugs, breaking changes, missing test coverage, and renders structured Markdown review comments.

## Usage in Claude Code
Ask Claude Code:
> "Review this pull request: https://github.com/owner/repo/pull/123"

Or invoke via CLI:
```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## Structure of Generated Reviews
- **Summary**: Concise 2-3 sentence overview of modified components and intent.
- **Identified Risks**: Critical security patterns, edge cases, regression vectors, and test gaps.
- **Improvement Suggestions**: Actionable recommendations for code quality and maintainability.
- **Confidence Score**: Deterministic confidence indicator (`High`, `Medium`, or `Low`).
