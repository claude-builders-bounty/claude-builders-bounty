# changelog.sh — Structured CHANGELOG Generator

Generate a clean, categorized `CHANGELOG.md` from your git history.

## Setup

```bash
# 1. Download the script
curl -sSL https://raw.githubusercontent.com/daletyler1737/claude-builders-bounty/main/changelog.sh -o changelog.sh
chmod +x changelog.sh

# 2. Run it in your repo
bash changelog.sh
```

## Usage

```bash
# Generate CHANGELOG.md from the last tag to HEAD
bash changelog.sh

# Specify output file
bash changelog.sh --output Docs/CHANGELOG.md

# Specify a custom tag range
bash changelog.sh --since v1.0.0
```

## Output

The script categorizes commits into:

| Category | Matches |
|----------|---------|
| **Added** | `feat:`, `add:`, `implement:` |
| **Fixed** | `fix:`, `bugfix:`, `hotfix:` |
| **Changed** | `refactor:`, `update:`, `perf:` |
| **Removed** | `remove:`, `delete:`, `drop:` |

Fallback keyword matching handles non-standard commit messages.
