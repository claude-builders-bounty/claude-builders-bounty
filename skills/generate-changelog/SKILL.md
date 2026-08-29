---
name: generate-changelog
description: Automatically generates a Keep-a-Changelog compatible CHANGELOG.md from git history.
---

# Git Changelog Generator Skill

Automatically parses commit history since the last git tag, categorizes them according to Conventional Commits (`Added`, `Fixed`, `Changed`, `Removed`), and updates `CHANGELOG.md`.

## Usage
Run the following command in any repository root:

```bash
python generate_changelog.py --version "v1.0.0"
```

Or via shell script:
```bash
bash changelog.sh "v1.0.0"
```

## Categorization Rules:
- `feat:`, `add:` -> **Added**
- `fix:`, `bug:` -> **Fixed**
- `refactor:`, `perf:`, `chore:`, `docs:` -> **Changed**
- `remove:`, `deprecate:` -> **Removed**
