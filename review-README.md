# claude-review — PR Review Agent

A CLI tool that reviews GitHub PRs and produces structured Markdown output.

## Setup

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/USERNAME/claude-builders-bounty/main/claude-review
chmod +x claude-review

# 2. Review any PR
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Output

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score (Low/Medium/High)

## Sample

See `sample-review.md` for example output.

## Requirements

- Python 3.8+
- Internet access (fetches PR from GitHub API)
