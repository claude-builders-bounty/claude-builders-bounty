---
name: generate-changelog
description: Automatically generates a structured, categorized CHANGELOG.md from git commits since the last tag.
---

# Generate Changelog Skill

This skill scans the current git repository's commit history since the most recent release tag (or from repository inception if no tags exist), categorizes the changes, and formats them into a clean `CHANGELOG.md` file following the **Keep a Changelog** standard.

## When to Use
- When the user asks to generate, update, or preview a changelog.
- When preparing a new release or reviewing recent changes since the last tag.
- When invoked via the `/generate-changelog` command.

## How It Works
1. Runs `bash changelog.sh` (or inspects `git describe --tags --abbrev=0` and `git log`).
2. Categorizes commits into four canonical sections:
   - **Added**: New features, capabilities, and additions (`feat:`, `add:`, etc.).
   - **Fixed**: Bug fixes, patches, and error resolutions (`fix:`, `bug:`, etc.).
   - **Changed**: Refactoring, chore, dependency updates, and improvements (`refactor:`, `chore:`, `perf:`, `update:`).
   - **Removed**: Deprecated or deleted functionality (`remove:`, `deprecate:`).
3. Writes the categorized entries to `CHANGELOG.md` under `## [Unreleased] - YYYY-MM-DD`.

## CLI Usage
```bash
# Generate CHANGELOG.md using default settings (since last tag)
bash changelog.sh

# Preview without modifying files
bash changelog.sh --dry-run

# Specify a custom output path
bash changelog.sh -o docs/CHANGELOG.md

# Compare commits from a specific tag
bash changelog.sh -t v1.2.0
```
