# Generate Structured CHANGELOG Skill for Claude Code 📝

> Automatically scans git history since the last tag, categorizes commits, and generates release notes.

[![Bounty](https://img.shields.io/badge/bounty-%2450-success)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

---

## ⚡ Setup (3 Steps or Fewer)

1. **Install Skill**:
   ```bash
   cp -r skills/generate-changelog ~/.claude/skills/
   ```
2. **Make Executable**:
   ```bash
   chmod +x ~/.claude/skills/generate-changelog/changelog.sh
   ```
3. **Run**:
   ```bash
   bash ~/.claude/skills/generate-changelog/changelog.sh --version "v1.0.0"
   ```

---

## 📋 Features

- 🏷️ **Tag-Aware**: Automatically calculates commits between `<latest-tag>..HEAD`.
- 🗂️ **Smart Categorization**: Sorts into `Added` (`feat`), `Fixed` (`fix`), `Changed` (`refactor`, `chore`), and `Removed` (`deprecate`).
- 🔄 **Safe Insertion**: Prepends new versions directly into existing `CHANGELOG.md` without overwriting prior history.

---

## 📄 Sample Output

```markdown
# Changelog

## [v1.0.0] - 2026-10-18

### Added
- initial README with bounty board (`1aeae2a`)

### Changed
- Initial commit (`a80a580`)
```
