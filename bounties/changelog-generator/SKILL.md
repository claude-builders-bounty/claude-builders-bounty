---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# Generate CHANGELOG

Generate a structured `CHANGELOG.md` from the project's git history.

## Usage

```
/generate-changelog [--since <tag>]
```

Or run the standalone script:

```bash
bash changelog.sh
```

## What it does

1. Reads git history from the last tag to HEAD
2. Categorizes commits into:
   - 🚀 **Added** — `feat:`, `add:`, `feature:`, `implement:`
   - 🔧 **Fixed** — `fix:`, `bugfix:`, `hotfix:`, `patch:`
   - 🔄 **Changed** — `refactor:`, `change:`, `update:`, `improve:`, `perf:`
   - 🗑️ **Removed** — `remove:`, `delete:`, `deprecat:`
   - 📝 **Documentation** — `docs:`, `doc:`, `readme:`
   - 🧪 **Testing** — `test:`, `testing:`, `spec:`
   - 📦 **Other** — any unclassified commits
3. Outputs a clean, markdown-formatted `CHANGELOG.md`

## Example output

```markdown
# Changelog since v1.0.0

## [2026-05-07]

### 🚀 Added
- Add user authentication via OAuth2 (abc1234)
- Implement dark mode toggle (def5678)

### 🔧 Fixed
- Fix login crash on Safari (ghi9012)
- Fix memory leak in WebSocket handler (jkl3456)

### 🔄 Changed
- Refactor API client for better error handling (mno7890)
- Update dependencies to latest versions (pqr1234)

---

_12 commits by Alice, Bob, Charlie_
```
