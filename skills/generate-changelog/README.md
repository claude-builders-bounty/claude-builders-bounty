# Generate Changelog Skill

Automatically generates a structured `CHANGELOG.md` from a project's git commit history.

## Quick Start (3 Steps)

### Option A: Bash Script

```bash
# 1. Copy into your project
curl -sO https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.sh
chmod +x changelog.sh

# 2. Run — generates CHANGELOG.md from all commits
bash changelog.sh

# 3. Commit the result
git add CHANGELOG.md && git commit -m "docs: update changelog"
```

### Option B: Claude Code Skill

1. Copy `skills/generate-changelog/SKILL.md` to your project's `.claude/skills/` directory
2. Run `/generate-changelog` in Claude Code
3. Review and commit the generated `CHANGELOG.md`

## Features

- 📦 Auto-detects last git tag as starting point
- 🏷️ Categorizes commits into: **Added / Fixed / Changed / Removed**
- 🔍 Smart keyword detection from commit messages
- 📝 Keep-a-Changelog compliant output format
- 🔄 Deduplicates identical commit messages
- ⚡ Zero dependencies (only `git`, `bash`, `sort`, `uniq`)

## Commit Message Conventions

The script uses these keywords to categorize commits:

| Category | Keywords |
|----------|----------|
| Added | `add`, `feat`, `new`, `create`, `init`, `introduce`, `implement` |
| Fixed | `fix`, `bug`, `patch`, `repair`, `correct`, `hotfix`, `resolve` |
| Changed | `change`, `update`, `modify`, `refactor`, `improve`, `optimize`, `upgrade` |
| Removed | `remove`, `delete`, `drop`, `deprecate`, `uninstall`, `cleanup` |

## Options

```bash
# Generate from a specific tag
bash changelog.sh --from-tag v1.0.0

# Output to a different file
bash changelog.sh --output HISTORY.md
```

## Example Output

See `SAMPLE-CHANGELOG.md` for a full example of the generated output.
