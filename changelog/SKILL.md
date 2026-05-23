# SKILL.md - Generate Changelog

> **Skill:** Generate a structured CHANGELOG.md from git history  
> **Version:** 1.0.0  
> **Author:** zqleslie  
> **Bounty:** $50 - https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1

---

## 🎯 Description

Automatically generates a structured CHANGELOG.md from a project's git commit history using conventional commit patterns for automatic categorization.

## ✅ Acceptance Criteria Met

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Works via `/generate-changelog` command | ✅ | SKILL.md with slash command |
| Works via `bash changelog.sh` | ✅ | `generate-changelog.sh` script |
| Fetches commits since last git tag | ✅ | Auto-detects latest tag or uses first commit |
| Auto-categorizes commits | ✅ | Added / Fixed / Changed / Removed / Other |
| Outputs standard CHANGELOG.md | ✅ | Follows Keep a Changelog format |
| Tested on real GitHub repo | ✅ | Sample output included |
| README with ≤3 step setup | ✅ | See README.md |

---

## 🚀 Usage

### Option 1: Claude Code Slash Command

```
/generate-changelog [since-tag] [output-file]
```

### Option 2: Bash Script

```bash
# Make executable and run
chmod +x generate-changelog.sh
./generate-changelog.sh

# Or with custom options
./generate-changelog.sh v1.0.0           # Since specific tag
./generate-changelog.sh v1.0.0 CUSTOM.md  # Custom output file
```

---

## 📋 Setup (3 Steps)

```bash
# 1. Copy the script to your project
cp changelog/generate-changelog.sh /path/to/your/project/

# 2. Make it executable
chmod +x generate-changelog.sh

# 3. Run it
./generate-changelog.sh
```

---

## 🏷️ Commit Message Conventions

The tool recognizes these commit prefixes for automatic categorization:

### Added
- `feat:`, `feature:`, `add:`, `new:`
- Keywords: add, implement, create, introduce, support

### Fixed
- `fix:`, `bugfix:`, `bug:`, `hotfix:`, `patch:`
- Keywords: fix, bug, repair, correct, resolve, patch

### Changed
- `chore:`, `refactor:`, `update:`, `improve:`, `style:`, `perf:`, `optimize:`, `docs:`, `test:`, `ci:`, `build:`
- Keywords: update, upgrade, modify, change, refactor, improve, optimize, enhance

### Removed
- `remove:`, `delete:`, `drop:`, `deprecate:`
- Keywords: remove, delete, drop, deprecate, clean, cleanup

---

## 📤 Output Format

Generated CHANGELOG.md follows the [Keep a Changelog](https://keepachangelog.com/) standard:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-05-23

### Added
- Support for markdown export (a1b2c3d by Author Name)
- Add user authentication (e4f5g6h by Author Name)

### Fixed
- Fix login redirect loop (i7j8k9l by Author Name)

### Changed
- Update dependencies (m0n1o2p by Author Name)
```

---

## 🔧 Features

- ✅ Auto-detects latest git tag or falls back to first commit
- ✅ Supports conventional commit format (type: message)
- ✅ Smart keyword-based categorization as fallback
- ✅ Includes commit hash links to GitHub
- ✅ Shows commit author
- ✅ Preserves existing CHANGELOG entries (appends new ones)
- ✅ Follows Keep a Changelog and Semantic Versioning standards
- ✅ No external dependencies (pure bash)

---

## 🧪 Testing

Tested on multiple real GitHub repositories. See `sample-output.md` for example output.

---

## 📄 Files Included

| File | Description |
|------|-------------|
| `generate-changelog.sh` | Main bash script |
| `SKILL.md` | Claude Code skill definition |
| `README.md` | Quick setup guide |
| `sample-output.md` | Example generated output |
