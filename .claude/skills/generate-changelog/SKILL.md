---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, auto-categorizing commits into Added/Fixed/Changed/Removed sections.
---

## Overview

When the user asks to generate or update a changelog, use the `changelog.sh` script in the project root, or generate one directly from git history using the patterns below.

## When to Use

- "Generate a changelog"
- "What's changed since v1.0?"
- "Write a changelog for the latest release"
- "Create CHANGELOG.md from git history"

## How to Run

### If changelog.sh exists in project root:

```bash
cd <project_root>
chmod +x changelog.sh
./changelog.sh
```

### If changelog.sh doesn't exist yet:

1. Create it with the bash script that:
   - Fetches commits since last tag (or given range)
   - Categorizes by Conventional Commits prefixes
   - Outputs formatted CHANGELOG.md

2. Or generate inline:

```bash
git log --no-merges --oneline HEAD~50..HEAD | grep -iE '^feat|^add|^fix|^bug|^refactor|^remove|^drop|^update'
```

## Categorization Rules

| Prefix Pattern | Category |
|----------------|----------|
| feat, add, new | **Added** |
| fix, bug, patch | **Fixed** |
| refactor, improve, update, change | **Changed** |
| remove, drop, delete, deprecate | **Removed** |
| (anything else) | **Other** |

## Output Format

```markdown
## <version>

### 🆕 Added

- <commit message>

### 🐛 Fixed

- <commit message>

### 🔄 Changed

- <commit message>

### 🗑️ Removed

- <commit message>
```

## Tips

- Skip merge commits and dependabot bumps
- Use `git describe --tags --abbrev=0` to find the last tag
- For range: `git log v1.0.0..v1.1.0 --oneline`
- Group related commits when possible
