---
name: generate-changelog
description: "Automatically generate or update a structured CHANGELOG.md from git commit history following Keep a Changelog standards."
author: Claude Builders Community
version: 1.0.0
---

# Generate Changelog Skill

Automatically inspects the repository's git commit history since the last release tag (or initial commit) and structures them into a standard `CHANGELOG.md`.

## Trigger & Usage

Whenever the user or agent requests to generate, update, or preview a changelog, run these commands from inside this skill's folder (or adjust paths accordingly):

```bash
# Generate / update CHANGELOG.md for unreleased changes
cd skills/generate-changelog && python generate_changelog.py

# Specify release version and tag
cd skills/generate-changelog && python generate_changelog.py --version "v1.2.0" --tag "v1.1.0" --date "2026-09-15"

# Output preview to stdout without writing file
cd skills/generate-changelog && python generate_changelog.py --stdout
```

Or execute via bash wrapper:
```bash
bash changelog.sh --version "v1.0.0"
```

## Categorization Logic

Categorizes commits into:
- **`Added`**: New features (`feat:`, `feature:`, `add:`)
- **`Fixed`**: Bug fixes (`fix:`, `bugfix:`, `hotfix:`, `patch:`)
- **`Changed`**: Refactoring, performance, chore, documentation (`refactor:`, `perf:`, `chore:`, `docs:`)
- **`Removed`**: Deprecated or deleted functionality (`remove:`, `revert:`, `deprecate:`)
- **`Security`**: Vulnerability patches and security hardening (`sec:`, `security:`)
