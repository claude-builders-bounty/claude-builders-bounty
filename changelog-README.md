# changelog.sh — Structured CHANGELOG Generator

Generate a professional `CHANGELOG.md` from git history in one command.

## Setup (3 steps)

```bash
# 1. Clone or copy the script
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run in any git repo
bash changelog.sh
```

## Quick Start

```bash
# Generate from last tag
bash changelog.sh

# From a specific version
bash changelog.sh --since v1.0.0

# Preview without writing (dry run)
bash changelog.sh --dry-run

# Custom output path
bash changelog.sh --output RELEASE_NOTES.md
```

## How It Works

1. Finds the latest git tag
2. Collects all commits since that tag
3. Categorizes by commit prefix (feat→Added, fix→Fixed, etc.)
4. Outputs a KeepAChangelog-compatible markdown file

---

**Bounty**: [claude-builders-bounty #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)
