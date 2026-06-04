---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history. Use when the user wants to create or update a changelog."
---

# Generate Changelog

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

```
/generate-changelog [output_file]
```

## Script

Run the bundled script:

```bash
bash scripts/generate-changelog.sh [CHANGELOG.md]
```

## How It Works

1. Finds the latest git tag (or uses initial commit)
2. Lists all commits since that tag
3. Categorizes by conventional commit prefix:
   - `feat`, `add`, `new` → **Added**
   - `fix`, `bug`, `hotfix` → **Fixed**
   - `change`, `update`, `refactor`, `chore`, `perf`, `style`, `docs` → **Changed**
   - `remove`, `delete`, `deprecat` → **Removed**
4. Formats as CHANGELOG.md

## Files

- `scripts/generate-changelog.sh` - Standalone bash script
- `SKILL.md` - This file
