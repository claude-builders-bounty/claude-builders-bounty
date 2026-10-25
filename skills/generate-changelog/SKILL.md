---
name: generate-changelog
description: Automatically generates a structured, categorized CHANGELOG.md from the repository git history.
---

# Generate Changelog Skill

Generates or updates `CHANGELOG.md` following Keep a Changelog conventions by analyzing conventional commits since the last tag.

## Usage

In Claude Code, invoke:
```bash
/generate-changelog
```
Or run directly via script:
```bash
python scripts/generate_changelog.py
```
Or via bash:
```bash
bash scripts/changelog.sh
```

## How It Works
1. Identifies the latest git tag using `git describe --tags --abbrev=0`.
2. Collects all commits since the tag (or from repository root if no tags exist).
3. Parses conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `perf:`, `chore:`, `docs:`, `revert:`).
4. Categorizes into:
   - **Added**: `feat`
   - **Fixed**: `fix`
   - **Changed**: `refactor`, `perf`, `chore`, `docs`, `style`
   - **Removed**: `revert`, `remove`, `deprecate`
5. Prepend or generates a clean, structured `CHANGELOG.md`.
