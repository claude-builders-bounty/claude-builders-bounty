---
name: pr-review
description: Fetch a GitHub PR diff and produce a structured code review with risks, improvements, and confidence scoring.
trigger: claude-review
---

# PR Review Agent

Analyzes a GitHub pull request and returns a structured Markdown review.

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Or with just the PR number if `GITHUB_REPOSITORY` is set:

```bash
claude-review --pr 123
```

## Output Format

The agent returns a structured review:

```markdown
## Review: owner/repo#123

**Summary:** 2-3 sentences describing what the PR does.

### Identified Risks
- Risk description with file/line reference

### Improvement Suggestions
- Suggestion with rationale

### Confidence Score
High / Medium / Low
```

## How It Works

1. Fetches PR metadata via `gh pr view`
2. Fetches the full diff via `gh pr diff`
3. Passes the diff to Claude Code for intelligent analysis
4. Outputs structured Markdown with summary, risks, suggestions, and confidence

## Requirements

- GitHub CLI (`gh`) installed and authenticated
- `jq` for JSON parsing
