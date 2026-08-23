# Skill: Generate Structured Changelog

## Description
Generates a structured `CHANGELOG.md` from a project's git history, auto-categorizing commits into Added, Fixed, Changed, and Removed sections.

## Usage

### As a Claude Code Skill
Invoke with `/generate-changelog` in your project directory.

### As a Bash Script
```bash
bash changelog.sh                     # Uses last git tag as starting point
bash changelog.sh v1.0.0              # Generates from v1.0.0 to HEAD
bash changelog.sh --repo /path/to/repo  # Specify repo path
```

## How It Works
1. Finds the most recent git tag (or uses the one provided)
2. Fetches all commits between that tag and HEAD
3. Categorizes each commit by conventional commit prefixes (feat/add → Added, fix → Fixed, refactor/update → Changed, remove → Removed)
4. Outputs a properly formatted `CHANGELOG.md`

## Categorization Rules
| Prefix | Category |
|--------|----------|
| add, feat, create, implement, introduce, support, new | Added |
| fix, bug, patch, resolve, repair, correct, hotfix | Fixed |
| change, update, modify, refactor, improve, enhance, bump, upgrade, migrate, rename, move | Changed |
| remove, delete, drop, strip, deprecate | Removed |

## Requirements
- Git
- Bash 4+
