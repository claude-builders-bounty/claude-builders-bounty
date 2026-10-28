# PR Reviewer Agent

A Claude Code sub-agent that reviews GitHub PR diffs and generates structured markdown review comments.

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## Capabilities
- Fetches PR diff from GitHub API
- Analyzes code changes
- Generates structured review with summary, risks, suggestions, confidence score
