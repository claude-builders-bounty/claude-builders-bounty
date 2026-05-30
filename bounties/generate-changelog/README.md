# Generate Changelog

A bash script and Claude Code skill that generates structured `CHANGELOG.md` from git history.

## Setup

1. Copy `changelog.sh` to your project root
2. `chmod +x changelog.sh`
3. `bash changelog.sh`

## Usage

```bash
# Auto-detect latest tag, output to CHANGELOG.md
bash changelog.sh

# Custom output file
bash changelog.sh RELEASE_NOTES.md

# Since specific tag
bash changelog.sh --since v1.0.0
```

## Categories

Commits are auto-categorized by prefix:

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `new`, `implement` | Added |
| `fix:`, `bug:`, `patch:`, `hotfix` | Fixed |
| `refactor:`, `chore:`, `update:`, `change:`, `improve:`, `bump` | Changed |
| `remove:`, `delete:`, `drop:`, `deprecate` | Removed |
| *(anything else)* | Other |

## Requirements

- Git repository with at least one commit
- Bash 4+
