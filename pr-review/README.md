# claude-review.sh — PR Review Agent

A CLI tool and GitHub Action that analyzes PR diffs and produces structured reviews.

## CLI Usage

```bash
# Review a GitHub PR
bash pr-review/claude-review.sh --pr https://github.com/owner/repo/pull/123

# Review a local diff file
bash pr-review/claude-review.sh --diff changes.diff

# Save output to file
bash pr-review/claude-review.sh --pr https://github.com/owner/repo/pull/123 --output review.md
```

## GitHub Action

Include `.github/workflows/pr-review.yml` in your repo to auto-review every PR.

## Output

- Summary of changes
- Files changed, additions/deletions
- Security risk detection
- Improvement suggestions
- Confidence score
