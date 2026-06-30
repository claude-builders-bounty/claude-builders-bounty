# PR Reviewer Agent

Automated PR analysis and structured code review via CLI.  
**Bounty: $150** — [#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

## Setup (3 steps)

```bash
# 1. Install gh CLI and authenticate
brew install gh       # macOS
gh auth login

# 2. Copy the script
cp claude-review.py /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review

# 3. Review any PR
claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
# Full URL
claude-review --pr https://github.com/vercel/next.js/pull/70000

# Shorthand (when --repo is set)
claude-review --pr 70000 --repo vercel/next.js

# Save to file
claude-review --pr https://github.com/owner/repo/pull/1 --output review.md
```

## Sample Output

```markdown
# PR Review: vercel/next.js#70000

**Title:** feat: add streaming support to route handlers
**Author:** @contributor
**Files:** 8 (+342 / -89)

## Summary
This PR modifies 8 files with +342 additions and -89 deletions. Test files are included.

## Identified Risks
- ⚠️ No test files detected in changeset
- ⚠️ High line count: 342 additions — review carefully

## Improvement Suggestions
- 💡 Add unit tests for new/modified logic

**Confidence Score:** 🟡 Medium
```

## Features
- Fetches PR metadata and diff via `gh` CLI
- Analyzes file count, additions/deletions, test coverage
- Detects common risk patterns (large PRs, missing tests, TODO markers)
- Generates structured Markdown output with confidence score
- Works with any public or private GitHub repo accessible via gh