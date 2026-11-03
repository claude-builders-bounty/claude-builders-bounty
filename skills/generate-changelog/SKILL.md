---
name: generate-changelog
description: Automatically generates and updates a structured, Keep-a-Changelog compliant CHANGELOG.md from git commit history.
triggers:
  - "/generate-changelog"
  - "generate changelog"
  - "update changelog"
---

# Generate Changelog Skill

Analyzes git history since the last git tag, categorizes commits into standard sections (`Added`, `Fixed`, `Changed`, `Removed`, `Security`, `Documentation`), and prepends or generates a clean `CHANGELOG.md`.

## Execution

Run the bundled CLI tool:

```bash
bash changelog.sh
```

Or invoke the Python generator directly:

```bash
python3 skills/generate-changelog/generate_changelog.py
```

## Features
- **Git Tag Aware**: Discovers the latest tag automatically using `git describe --tags --abbrev=0`.
- **Keep a Changelog Format**: Follows semantic versioning standards and clean Markdown categorization.
- **Commit Categorization**: Uses conventional commit parsing (`feat:`, `fix:`, `refactor:`, `docs:`, etc.).
- **Zero Dependencies**: Pure Python standard library with no external pip packages required.
