# PR Review Agent — Claude Code sub-agent
> **Bounty $150**
## Overview

`claude-review` is a CLI tool and Claude Code sub-agent that takes a PR diff,
performs static analysis (secrets, console logs, TODO detection), and generates
a structured Markdown review. When Claude Code is available, it also pipes the
diff for AI-powered analysis.

## Installation

```bash
cp claude-review /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review
```

Or install as a Claude Code skill:
```bash
mkdir -p ~/.claude/skills/pr-review
cp claude-review ~/.claude/skills/pr-review/
```

## Usage

```bash
# Review a GitHub PR
claude-review --pr https://github.com/owner/repo/pull/123

# Review from a local diff file
claude-review --diff my-feature.patch

# Review from git diff via stdin
git diff main...feature-branch | claude-review --stdin

# JSON output for CI integration
claude-review --pr https://github.com/owner/repo/pull/123 --format json > review.json

# Concise status (for GitHub Actions)
claude-review --pr https://github.com/owner/repo/pull/123 --format concise

# Skip AI analysis (static checks only)
claude-review --diff changes.patch --no-ai
```

## GitHub Actions Integration

```yaml
name: PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Claude PR Review
        run: |
          git diff origin/${{ github.base_ref }}...HEAD | \
            claude-review --stdin --format concise
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Output Format

### Markdown (default)
```
# PR Review: Add user authentication
**Author**: @dev | main ← feature/auth
**Stats**: 5 files, +342 -89

## 📊 Static Analysis
| Metric | Value |
|--------|-------|
| Files changed | 5 |
...

### 🚨 Secrets Detected
...

## 🤖 AI Review
### Summary
...

### Issues Found
| Severity | Category | File | Issue | Suggestion |
...
```

## Static Checks

- 🔒 **Secrets detection**: API keys, tokens, private keys
- 📝 **Console.log leftovers**: Debug logging in production code
- 📋 **TODOs/FIXMEs**: Unresolved code markers
- 📦 **Large files**: Files with >500 line changes
- 🗄️ **Migration detection**: Database schema changes flagged for review
- 🧪 **Test files**: Identifies test coverage in the PR

## 🧪 Verified Test Output

### Sample 1 — Feature PR with Security Issues

```
# Code Review

## 📊 Static Analysis

| Metric | Value |
|--------|-------|
| Files changed | 3 |
| +16 / -2 | 16 additions, 2 deletions |
| Test files | 0 |
| Large files (>500 lines) | 0 |
| Database migrations | ⚠️ Yes |

### Files Changed

| File | +Additions | -Deletions |
|------|-----------|------------|
| src/auth/login.ts | +6 | -1 |
| src/db/migrations/003_add_roles.sql | +8 | -0 |
| src/components/Dashboard.tsx | +2 | -1 |

### 🚨 Secrets Detected

- **Hardcoded secret** in `src/auth/login.ts`

### 📝 Console Logs (debugging leftovers)

- `src/auth/login.ts`: console.log('Login attempt:', email)

### 📋 TODOs / FIXMEs

- `src/auth/login.ts`: FIXME: handle case-insensitive email lookup
- `src/components/Dashboard.tsx`: TODO: add error boundary
```

> Detected: hardcoded API key, leftover console.log, 2 unresolved markers, and a database migration — all before any AI analysis.

### Sample 2 — Bug Fix with Validation Tests

```
[✅ OK] 3 files, +18 -4, 0 issues found
```

> Clean PR: payment amount sanitization fix with new unit tests. Static analysis passes — no secrets, no debug logs, no markers.

## Dependencies

- Python 3.8+ (stdlib only — no pip installs needed)
- Optional: Claude Code CLI for AI-powered review enhancement
- Optional: `GITHUB_TOKEN` env var for private repos
