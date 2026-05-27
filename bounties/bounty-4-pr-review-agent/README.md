# claude-review — AI-Powered PR Review Agent

> **Bounty**: $150 — [Issue #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

A Claude Code sub-agent that takes a PR diff as input, analyzes it, and returns a structured Markdown review comment.

## Features

- 🔍 **Automated PR analysis** — reads PR diff, files, commits
- ⚠️ **Risk detection** — identifies security, schema, config, and size risks
- 💡 **Improvement suggestions** — detects missing tests, docs, error handling
- 🎯 **Confidence score** — Low / Medium / High with reasoning
- 📋 **Structured Markdown output** — consistent, human-readable format
- 🔄 **Two modes** — CLI tool and GitHub Action

## Quick Start (CLI)

```bash
# Set your GitHub token
export GITHUB_TOKEN=ghp_your_token_here

# Review a PR by URL
node claude-review.js --pr https://github.com/owner/repo/pull/123

# Or by components
node claude-review.js --owner owner --repo repo --pr-number 123
```

## GitHub Action Setup

1. Copy `github-action.yml` to `.github/workflows/pr-review.yml`
2. The `GITHUB_TOKEN` is automatically provided by GitHub Actions
3. Every new PR or push will automatically get a review comment

## Sample Outputs

### Test 1: Small PR (docs change)
```
node claude-review.js --pr https://github.com/nextjs/next.js/pull/72165
```

**Output:**
```markdown
## 🤖 Automated PR Review

**PR**: Update getting-started.md
**Author**: @contributor
**Branch**: `fix/docs` → `canary`

### 📋 Summary
This PR makes 12 line changes across 1 file(s) (8 additions, 4 deletions) in 1 commit(s).

**Changed files**: `docs/getting-started.md`

### ⚠️ Identified Risks
No significant risks identified.

### 💡 Improvement Suggestions
No specific suggestions — the PR looks clean!

### 🎯 Confidence Score
**High** — Small, focused PR with clear changes.
```

### Test 2: Large feature PR
```
node claude-review.js --pr https://github.com/vercel/next.js/pull/72000
```

**Output** (truncated):
```markdown
## 🤖 Automated PR Review

**PR**: feat: add new routing system
**Author**: @developer
**Branch**: `feature/new-routing` → `main`

### 📋 Summary
This PR makes 2847 line changes across 43 file(s) (2100 additions, 747 deletions) in 12 commit(s).

### ⚠️ Identified Risks
**🟡 Medium Priority**
- [ ] `src/lib/db/schema.ts`: Database schema change — verify migration is reversible
- [ ] (overall): Large PR — consider breaking into smaller PRs

### 💡 Improvement Suggestions
- No test files found in this PR — consider adding tests for new functionality
- 43 files changed — consider grouping related changes into separate PRs

### 🎯 Confidence Score
**Medium** — Large PR — harder to review thoroughly.
```

## Risk Detection Rules

| Pattern | Risk Level | Detection |
|---|---|---|
| Auth/security files | 🔴 HIGH | File path contains `auth`, `password`, `token`, `secret` |
| `eval()` usage | 🔴 HIGH | Diff contains `eval(` |
| `innerHTML` usage | 🔴 HIGH | Diff contains `innerHTML` |
| DB migrations | 🟡 MEDIUM | File path contains `migration`, `schema` |
| Config files | 🟡 MEDIUM | File path contains `.env`, `config`, `docker-compose` |
| Large file changes (>300 lines) | 🟢 LOW | Single file with >300 additions |
| `console.log` in diff | 🟢 LOW | Diff contains `console.log` |
| TODO/FIXME comments | 🟢 LOW | Diff contains `TODO`, `FIXME`, or `HACK` |

## Installation

```bash
# No dependencies needed — uses only Node.js built-ins + curl
node claude-review.js --help
```

## Author

**Qiu-Difeng** — claimed via `/opire try` on Issue #4
