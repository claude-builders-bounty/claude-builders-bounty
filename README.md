# PR Review Agent

AI-powered PR review agent that analyzes GitHub PR diffs and generates structured Markdown review comments.

## Usage

### Via CLI

```bash
python pr_review.py --pr https://github.com/owner/repo/pull/123
```

### Via GitHub Action

Copy `pr_review.yml` to `.github/workflows/` in your repo.

## Features

- **Summary**: 2-3 sentence summary of changes
- **Identified Risks**: Security, performance, and stability concerns
- **Improvement Suggestions**: Actionable recommendations
- **Confidence Score**: Low / Medium / High

## Structured Output

```markdown
# PR Review

## Summary
[2-3 sentences describing the PR]

## Identified Risks
- [Risk 1]
- [Risk 2]

## Improvement Suggestions
- [Suggestion 1]
- [Suggestion 2]

## Confidence Score
**Medium**
```

## Requirements

- Python 3.7+
- GitHub CLI (`gh`) authenticated, or `GITHUB_TOKEN` environment variable
