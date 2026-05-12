# 📝 Generate Structured CHANGELOG — Claude Code Skill

A Claude Code skill + bash script that automatically generates a structured `CHANGELOG.md` from a project's git history, following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

> Bounty submission for [Issue #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

## ⚡ Setup (3 steps)

### 1. Copy the skill file
```bash
cp skills/generate-changelog/SKILL.md ~/.claude/skills/generate-changelog.md
```

### 2. Copy the bash script (optional, for standalone use)
```bash
cp skills/generate-changelog/changelog.sh /usr/local/bin/changelog.sh
chmod +x /usr/local/bin/changelog.sh
```

### 3. Use it
In Claude Code, just say: **"generate a changelog"** or **"generate changelog from last tag"**

Or run directly:
```bash
bash skills/generate-changelog/changelog.sh
```

## 🎯 Features

- **Auto-categorizes** commits into: `Added`, `Fixed`, `Changed`, `Removed`
- **Conventional Commits** support (`feat:`, `fix:`, `refactor:`, etc.)
- **Keyword fallback** for non-conventional commits
- **Keep a Changelog** format (v1.1.0)
- **Auto-detects** last git tag for range
- **Commit links** to GitHub when remote URL is available
- **Author attribution** on each entry

## 📋 Options

| Option | Description | Default |
|--------|-------------|---------|
| `--all` | Generate from entire history | Since last tag |
| `--since TAG` | Generate from specific tag | Auto-detect |
| `--output FILE` | Custom output file | `CHANGELOG.md` |

## 📄 Sample Output

Generated from this repository:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — 2026-05-13

### Added
- feat: add pre-tool-use hook to block destructive bash commands (`7cc7b61`) — *Viet Anh*

### Changed
- Initial commit (`abc1234`) — *claudebounty*
```

## 🧪 Testing

```bash
# Run on this repo
bash skills/generate-changelog/changelog.sh --all --output SAMPLE_CHANGELOG.md
cat SAMPLE_CHANGELOG.md
```

## 📄 License

MIT
