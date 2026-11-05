---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag
---

# Generate Changelog

Generates a structured `CHANGELOG.md` from a project's git history.

## Usage

```bash
# In a Claude Code session:
/generate-changelog

# Or run directly:
bash changelog.sh
```

## What It Does

1. Fetches all commits since the last git tag (or all commits if no tags exist)
2. Auto-categorizes commits into: `Added`, `Fixed`, `Changed`, `Removed`
3. Outputs a properly formatted `CHANGELOG.md`

## Categorization Rules

- **Added**: commits starting with `feat`, `add`, `new`, `introduce`
- **Fixed**: commits starting with `fix`, `bug`, `patch`, `correct`
- **Changed**: commits starting with `change`, `update`, `modify`, `refactor`, `improve`, `perf`
- **Removed**: commits starting with `remove`, `delete`, `drop`

## Setup

1. Ensure git is installed
2. Run the script in your project root
3. Output is written to `CHANGELOG.md`
