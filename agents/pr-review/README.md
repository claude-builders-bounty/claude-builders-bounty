# Claude PR Review Agent

Automated PR review agent that fetches diffs from GitHub API and produces structured Markdown review comments. Works as CLI or GitHub Action.

## CLI Usage

```bash
# Install
pip install -r requirements.txt  # no external deps — pure Python 3 stdlib

# Set token
export GITHUB_TOKEN=ghp_xxx

# Review a PR
python claude-review.py --pr https://github.com/owner/repo/pull/123
python claude-review.py --pr 123 --repo owner/repo
```

## GitHub Action

Copy `.github/workflows/pr-review.yml` to your repo. The Action auto-reviews every opened/synchronized PR and posts a structured comment.

## Sample Output

```
## 🔍 PR Review

### Summary
PR #42 by @alice: "Add user authentication" — main ← feature/auth

### Stats
| Metric | Value |
|--------|-------|
| Files Changed | 5 |
| Additions | 240 |
| Deletions | 30 |
| Total Changes | 270 |
| Commits | 3 |

### Identified Risks
- 🔐 Security-sensitive: src/auth/middleware.py — verify auth logic
- 🔌 API change: src/api/routes/auth.py — verify backward compat

### Improvement Suggestions
- ✅ Has tests
- ✅ Good PR size for review

### Confidence
**Medium**
```

## What It Checks

- **Risks**: Schema changes, deps, security files, config, API contracts, large files, TODO markers
- **Test coverage**: Detects test files in the PR
- **Commit quality**: Flags unclear commit messages
- **Size analysis**: Recommends splitting large PRs

## Bounty

Part of [Bounty #4 — $150](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4).
