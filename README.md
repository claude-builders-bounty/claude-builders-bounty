# claude-review

A structured PR review CLI agent — part of the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) (#4).

## Features

- Takes any GitHub PR URL and produces a structured Markdown review
- Analyzes diff size, risk patterns, and code quality heuristics
- Output includes: summary, identified risks, improvement suggestions, and confidence score
- Outputs to stdout or a file (`--output`)

## Setup

```bash
# 1. Make sure you have a GitHub personal access token
export GH_TOKEN=ghp_your_token_here

# 2. Make the script executable (already done in repo)
chmod +x claude-review
```

The token needs `repo` scope for private repos, or just `public_repo` for public ones.

## Usage

```bash
# Review a PR — output to terminal
./claude-review --pr https://github.com/owner/repo/pull/123

# Review a PR — save to file
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Sample Output Preview

```
# PR Review: https://github.com/psf/black/pull/4675

---

## 📋 Summary

This PR fixes issues with **16 additions and 2 deletions** across **2 files** (CHANGES.md, autoload/black.vim).

---

## ⚠️ Identified Risks

- **Debug logging/print statements** — Found debug artifact(s) in the diff

---

## 💡 Improvement Suggestions

- The code looks clean. No immediate improvement suggestions.

---

## ✅ Confidence Score: **High**
```

See the [`test/`](test/) directory for full sample outputs against real GitHub PRs.

## How It Works

1. Parses the PR URL to extract owner, repo, and PR number
2. Fetches PR metadata and raw diff via the GitHub REST API
3. Analyzes the diff using heuristics:
   - Diff size and scope
   - Debug logging / print statements
   - FIXME/TODO/HACK markers
   - Dependency lock changes
   - Missing tests
   - Potential credential exposure
   - Long lines and magic numbers
   - Error handling coverage
   - Documentation completeness
4. Produces structured Markdown with a confidence score (Low/Medium/High)

## Requirements

- Python 3.7+
- `GH_TOKEN` environment variable (GitHub personal access token)

## License

MIT