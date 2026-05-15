# SHA Changelog Generator

Conventional cause parser: reads git log, groups by type, and exports a formatted CHANGELOG.md.

## 💰 Bounty: $50 (Issue #1)

Part of [claude-builders-bounty/claude-builders-bounty#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).

---

## 🚀 Usage

```bash
# Working directory: git repo with conventional commits
./changelog.sh

# Only commits since a tag
./changelog.sh --since v1.0.0

# Write to file instead of stdout
./changelog.sh --output CHANGELOG.md

# Preview without writing
./changelog.sh --dry-run
```

## ✅ Acceptance Criteria

- [x] Converts conventional commit history to structured `CHANGELOG.md`
- [x] Sectioned output: Feat, Fix, Docs, Style, Refactor, Perf, Test, Chore, Build
- [x] Works via CLI on any git repo
- [x] Tested on real repo (`git log --format:%h %s` output matches expected format)
- [x] Works on next.js projects

## 🧪 Test

```bash
cd /path/to/git-repo
./changelog.sh --dry-run   # preview
./changelog.sh --output CHANGELOG.md   # write
```

Expected output (excerpt):

```
# Changelog

## Feat

* feat: add user authentication  (a1b2c3d)
* feat: add dashboard page  (e4f5g6h)

---
*Generated on N commits via changelog.sh*
```
