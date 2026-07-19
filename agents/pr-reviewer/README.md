# PR Reviewer Agent

A Claude Code sub-agent that reviews GitHub pull requests and outputs structured Markdown reviews.

## Usage

```bash
chmod +x claude-review.sh
./claude-review.sh --pr https://github.com/owner/repo/pull/123
```

## Output

Structured review with:
- Summary of changes (2–3 sentences)
- Identified risks (e.g., secrets, debug code, large diffs)
- Improvement suggestions
- Confidence score: Low / Medium / High

## Requirements

- Bash 4+, curl, python3
- GitHub API (no token needed for public repos)
