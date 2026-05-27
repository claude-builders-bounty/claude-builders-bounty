# changelog.sh — Git Changelog Generator

Generate a structured `CHANGELOG.md` from your git history, categorized by type.

## Setup

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/CHY9213/claude-builders-bounty/main/templates/changelog/changelog.sh

# 2. Make executable
chmod +x changelog.sh

# 3. Run
bash changelog.sh
```

## Output Example

```markdown
# Changelog

## [v1.2.0] — 2026-05-28

### ✨ Added
- feat: add user profile page (abc123)
- feat: implement dark mode toggle (def456)

### 🐛 Fixed
- fix: login redirect loop (ghi789)

### 🔄 Changed
- refactor: extract payment service (jkl012)
- chore: update dependencies (mno345)
```

## Options

| Flag | Description |
|------|-------------|
| `--tag <ref>` | Start from a specific tag/commit |
| `--output <file>` | Output file (default: CHANGELOG.md) |
| `--help` | Show help |

## Requirements

- Git
- Bash 4+
- Conventional commits (optional — falls back to all commits)
