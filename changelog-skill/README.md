# 📋 Generate CHANGELOG

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from your git history.

## ✨ Features

- 🔍 Fetches commits since the last git tag
- 🏷️ Auto-categorizes: **Added** / **Fixed** / **Changed** / **Removed**
- 🎯 Parses conventional commits (`feat:`, `fix:`, `perf:`, etc.)
- 🧹 Skips noise commits (`docs:`, `test:`, `chore:`, etc.)
- 📝 Outputs clean `CHANGELOG.md` in keepachangelog format

## 🚀 Installation

```bash
# 1. Copy the skill to your Claude Code skills directory
cp -r changelog_skill ~/.claude/skills/generate-changelog
```

Done. No other steps needed.

## 📖 Usage

```bash
/generate-changelog
```

Or run directly as a script:

```bash
python3 changelog.py              # Current directory
python3 changelog.py /path/to/repo # Specific repo
```

## 🔧 How It Works

1. Finds the latest git tag (falls back to all commits if none found)
2. Gets all commits since that tag
3. Parses conventional commit prefixes
4. Categorizes and writes `CHANGELOG.md`

## 📄 Sample Output

```markdown
# Changelog

## [v20260516] - 2026-05-16

### 🚀 Added
- Add configuration file
- Add JSON parsing utility
- Implement user authentication

### 🐛 Fixed
- Fix memory leak in websocket handler
- Correct output encoding for special characters

### 🔧 Changed
- Upgrade dependencies to latest versions
- Optimize database query performance

### 🗑️ Removed
- Deprecated v1 API endpoints
```

## 📁 Files

| File | Description |
|------|-------------|
| `changelog.py` | Core Python script |
| `SKILL.md` | Claude Code skill definition |
| `README.md` | This file |
