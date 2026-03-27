---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag.
---

# Generate CHANGELOG

Use this skill when the user asks to generate or update a `CHANGELOG.md` from git history.

## Command

```bash
bash skills/generate-changelog/generate-changelog.sh
```

## What it does

- Finds the most recent git tag
- Reads commits since that tag
- Categorizes commit subjects into: Added, Fixed, Changed, Removed, Documentation, Performance, Testing, Build, CI/CD, Maintenance
- Writes a formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format
- Adds comparison links between versions

## Categorization rules

| Prefix | Category |
|--------|----------|
| `feat`, `feature`, `add` | Added |
| `fix`, `bugfix`, `hotfix` | Fixed |
| `refactor`, `update`, `change`, `perf`, `docs`, `style`, `chore` | Changed |
| `remove`, `delete`, `drop`, `deprecate` | Removed |
| `docs` | Documentation |
| `perf` | Performance |
| `test` | Testing |
| `build` | Build |
| `ci` | CI/CD |
| `chore` | Maintenance |
| _(anything else)_ | Changed |

## Usage

```bash
# Generate CHANGELOG.md in current directory
./generate-changelog.sh

# Generate to custom file
./generate-changelog.sh --output MY_CHANGELOG.md
```

## Requirements

- bash 4+
- git

## Notes

- If there is no tag yet, uses the full history
- The generated changelog is a starting point; review before publishing
