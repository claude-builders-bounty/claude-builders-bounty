# Claude PR Review Agent

`claude-review` fetches a pull request diff and prints a structured Markdown review comment.

## Setup

```bash
python3 pr-review-agent/claude_review.py --pr https://github.com/owner/repo/pull/123
```

For private repositories, authenticate `gh` first. The script uses `gh pr diff` when available and falls back to GitHub's `.diff` endpoint for public pull requests.

## Output

The generated comment contains:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score

## Samples

Two real-PR sample outputs are included in `samples/`.
