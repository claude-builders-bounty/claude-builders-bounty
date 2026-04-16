---
name: pr-reviewer
description: Review GitHub PRs with structured Markdown feedback
triggers:
  - "/review-pr"
  - "review this PR"
  - "review pull request"
---

# PR Reviewer Skill

Analyze a GitHub PR diff and produce a structured Markdown review with security, bug, performance, and style findings.

## Quick Start

```bash
# Review a PR
python claude-review --pr https://github.com/owner/repo/pull/123

# Review and post as comment
python claude-review --pr https://github.com/owner/repo/pull/123 --post

# Review local diff
git diff main..feature | python claude-review --stdin
```

## What It Does

1. Fetches PR diff from GitHub API (or reads from stdin/file)
2. Parses unified diff format into per-file hunks
3. Runs static analysis for:
   - **Security**: eval(), hardcoded secrets, SQL injection, XSS
   - **Bugs**: empty catches, console.log, TODO/FIXME, `any` types
   - **Performance**: SELECT *, await in forEach, N+1 patterns
   - **Style**: var usage, == vs ===
   - **Testing**: missing test coverage
   - **Documentation**: no doc updates
4. Generates structured Markdown report
5. Optionally posts as GitHub PR comment

## Output Format

```markdown
# 🔍 Automated PR Review
## 📊 Summary
| Metric | Value |
| Files changed | 5 |
| Additions | +120 |
## 📁 Files Changed
## 🔎 Findings
### 🔒 Security Issues
### 🐛 Potential Bugs
## 📋 Assessment
```

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)
- GITHUB_TOKEN env var for private repos or posting comments

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| GITHUB_TOKEN | For private repos / posting | GitHub personal access token |
| GH_TOKEN | Alternative | Same as GITHUB_TOKEN |
