---
name: claude-review
description: AI-powered PR review agent. Fetches a GitHub PR diff and produces a structured Markdown review with summary, risks, suggestions, and security analysis.
argument-hint: "--pr owner/repo#123"
---

# Claude PR Reviewer

AI agent that reviews GitHub pull requests and outputs structured Markdown reviews. Uses Claude API to analyze diffs.

## Requirements

```bash
# Must be authenticated
gh auth login

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Usage

```bash
# Full URL
claude-review --pr https://github.com/owner/repo/pull/123

# Short form
claude-review --pr owner/repo#123

# Save to file
claude-review --pr owner/repo#123 --output review.md

# Dry run (fetch diff only, no API call)
claude-review --pr owner/repo#123 --dry-run

# Custom model
claude-review --pr owner/repo#123 --model claude-opus-4-20250514
```

## Output Format

```markdown
## Summary
2-3 sentences summarizing the changes.

## Identified Risks
- Risk: description and impact

## Improvement Suggestions
- Suggestion: actionable fix

## Security Concerns
- Concern or "None identified"

## Overall Assessment
✅ Approve / ⚠️ Changes Requested / 💬 Comment
```

## How It Works

1. Parses PR reference (URL or `owner/repo#number`)
2. Fetches diff via `gh pr diff`
3. Sends diff + structured review prompt to Claude API
4. Returns Markdown review ready to post as a PR comment
