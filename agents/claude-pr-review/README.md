# Claude PR Review Agent

`claude-review` fetches a GitHub pull request and prints a structured Markdown review comment.

## Usage

```bash
python agents/claude-pr-review/claude-review.py --pr https://github.com/owner/repo/pull/123
```

Set `GITHUB_TOKEN` to raise API limits for private or high-volume review runs.

## Output Format

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## Verification

Sample outputs for two real PRs are included:

- `samples/pr-2479-review.md`
- `samples/pr-2480-review.md`
