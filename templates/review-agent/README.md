# 🤖 Claude Code PR Review Agent

Analyze GitHub Pull Requests and generate structured Markdown review reports.

## Usage

### CLI

```bash
# Review a PR by URL
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Save output to file
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 -o review.md

# Review from a diff file
python3 claude-review.py --file /path/to/pr.diff

# Pipe diff
curl -L https://github.com/owner/repo/pull/123.diff | python3 claude-review.py
```

### GitHub Action

Add `.github/workflows/pr-review.yml` to your repository (included).

## Output

```markdown
# PR Review Report

**Fix login redirect loop**
Link: https://github.com/owner/repo/pull/123

## Summary
This PR changes 3 files (+45/-12 lines).

### Changed Files
| File | + | - |
|------|---|---|
| src/auth/login.tsx | +30 | -8 |
| src/lib/auth.ts | +15 | -4 |

## High Risk Issues
- **Hardcoded secret** in `src/config.ts`
  ```
  api_key = "sk-1234567890abcdef"
  ```

## Medium Risk / Concerns
- **Unresolved TODO** in `src/auth/login.tsx`
  ```
  // TODO: add rate limiting
  ```

## Improvement Suggestions
1. Consider adding tests for the new auth flow.

## Review Confidence
**⚠️ Confidence: Medium**
```

## Features

- Fetches PR diff and metadata from GitHub API
- Detects high-risk patterns (hardcoded secrets, destructive commands, unsafe HTML injection)
- Identifies medium concerns (unresolved TODOs, debug output, skipped tests)
- Suggests improvements based on PR size and scope
- Calculates review confidence score
- Standalone CLI + GitHub Action support
- Zero dependencies — pure Python 3

## Requirements

- Python 3.8+
- GitHub API access (unauthenticated for public repos, `GITHUB_TOKEN` for private)
