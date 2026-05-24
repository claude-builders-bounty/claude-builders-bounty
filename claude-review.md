# Claude Review — PR Review Agent

A lightweight Python agent that analyzes GitHub PRs and outputs structured Markdown reviews.

## Setup

1. Clone this repo or download `claude-review.py`:
```bash
curl -O https://raw.githubusercontent.com/dagangtj/claude-builders-bounty/main/claude-review.py
chmod +x claude-review.py
```

2. Ensure `gh` CLI is installed and authenticated:
```bash
gh auth login
```

3. Run on any PR:
```bash
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

## What It Does

- Fetches PR metadata and file changes via GitHub API
- Identifies risks (sensitive files, deletions, large additions)
- Suggests improvements (tests, docs, split large PRs)
- Outputs structured Markdown with confidence score

## GitHub Action

The included `.github/workflows/pr-review.yml` automatically runs on every PR.

## Sample Output

```markdown
## PR Review Summary

**Changes:** 3 files (+120 / -45)

### Summary
This PR modifies 3 files with 120 additions and 45 deletions.

### Identified Risks
- ⚠️ High deletion ratio — verify no critical code removed

### Improvement Suggestions
- 💡 Add tests for new functionality
- 💡 Update documentation/README for significant changes

### Confidence Score: Medium
```
