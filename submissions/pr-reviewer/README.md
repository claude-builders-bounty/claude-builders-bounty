# Claude Review — PR Reviewer Agent 🤖

**Bounty #4 — $150**

A Claude Code sub-agent that takes a PR diff as input, analyzes it, and returns a structured Markdown review comment.

## What's Included

| File | Purpose |
|------|---------|
| `claude-review` | Main Python script (zero dependencies) |
| `SKILL.md` | Claude Code skill definition |
| `README.md` | This file |

## Usage

```bash
# Review a GitHub PR
python claude-review --pr https://github.com/owner/repo/pull/123

# Post review as PR comment (requires GITHUB_TOKEN)
GITHUB_TOKEN=ghp_xxx python claude-review --pr <url> --post

# Review a local diff file
python claude-review --diff-file changes.diff

# Pipe from git
git diff main..feature | python claude-review --stdin

# JSON output for programmatic use
python claude-review --pr <url> --json

# Save to file
python claude-review --pr <url> -o review.md
```

## Acceptance Criteria ✅

| Requirement | Status |
|-------------|--------|
| Takes PR URL as input | ✅ `--pr <url>` |
| Fetches and parses diff | ✅ GitHub API |
| Structured Markdown output | ✅ Summary + Findings + Assessment |
| Posts as PR comment | ✅ `--post` flag |
| Security analysis | ✅ 11 patterns detected |
| Bug detection | ✅ 7 patterns detected |
| Performance analysis | ✅ 5 patterns detected |
| Works as Claude Code agent | ✅ SKILL.md included |

## Detection Capabilities

### 🔒 Security (11 patterns)
- eval(), exec() — code injection
- innerHTML — XSS
- Hardcoded passwords, API keys, secrets, tokens
- SQL DELETE/DROP without safeguards
- Disabled SSL verification
- Wildcard CORS

### 🐛 Bugs (7 patterns)
- console.log / debugger left in
- TODO/FIXME/HACK comments
- Empty catch blocks
- TypeScript `any` type
- @ts-ignore usage

### ⚡ Performance (5 patterns)
- SELECT * queries
- await inside forEach
- N+1 query patterns
- Unnecessary JSON deep clones

### 🎨 Style (3 patterns)
- var declarations
- == / != comparisons

### 🧪 Testing
- Missing test coverage detection
- Minimal test file warnings

### 📝 Documentation
- Missing documentation updates

## Output Example

```markdown
# 🔍 Automated PR Review

**PR:** #123 — Add user authentication
**Author:** @developer
**Branch:** `feature/auth` → `main`
**Reviewed:** 2026-04-16 04:00 UTC

## 📊 Summary
| Metric | Value |
|--------|-------|
| Files changed | 8 |
| Additions | +245 |
| Deletions | -12 |
| Net change | +233 lines |

## 📁 Files Changed
- 🆕 `src/auth/login.ts` (+89/-0)
- ✏️ `src/routes.ts` (+12/-3)
...

## 🔎 Findings
### 🔒 Security Issues
- SQL DELETE — ensure WHERE clause is correct

### 🐛 Potential Bugs
- console.log left in code — remove for production

## 📋 Assessment
**💡 SUGGESTIONS** — 2 minor suggestion(s)
```

## Requirements

- Python 3.8+
- No pip packages needed (stdlib only)
- GITHUB_TOKEN for private repos / posting

## License

MIT
