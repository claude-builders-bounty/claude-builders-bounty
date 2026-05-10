# 🔍 PR Reviewer Agent for Claude Code

Analyzes GitHub PRs and posts structured review comments.

## Usage

```bash
# Review a PR
bash claude-review.sh --pr https://github.com/owner/repo/pull/123

# Pipe to Claude for analysis
bash claude-review.sh --pr https://github.com/owner/repo/pull/123 | claude
```

## Output Format

```markdown
## Summary
2-3 sentences describing the changes.

## Risks
- Risk 1: Description
- Risk 2: Description

## Suggestions
- Suggestion 1: Description
- Suggestion 2: Description

## Confidence
Medium

## Verdict
APPROVE / REQUEST_CHANGES / COMMENT
```

## How It Works

1. Fetches PR diff and metadata from GitHub API
2. Analyzes changes for risks and improvements
3. Generates structured Markdown review
4. Can be piped to Claude for AI-powered analysis

## Requirements

- curl
- bash 4.0+
- GitHub API access (no token needed for public repos)
