---
name: generate-changelog
description: Automatically generates a structured, Keep-a-Changelog-compliant CHANGELOG.md from git history since the latest tag or initial commit.
version: 1.0.0
---

# Generate Changelog Skill

A production-ready skill for Claude Code that extracts commits from git history, auto-categorizes them using Conventional Commits and semantic analysis into standard categories (`Added`, `Fixed`, `Changed`, `Removed`), and generates or prepends to `CHANGELOG.md`.

## When to Use
- Running `/generate-changelog` to document a new release or update project history.
- Pre-release preparation and version bumping.
- Automating release notes in CI/CD workflows.

## Capabilities
- Detects the latest git tag automatically (falls back to initial commit if no tags exist).
- Inspects commit subject and body messages.
- Groups commits by category:
  - **Added**: `feat:`, `add:`, `new:`, `feature:`, `implement:`
  - **Fixed**: `fix:`, `bug:`, `patch:`, `hotfix:`, `resolve:`
  - **Changed**: `refactor:`, `perf:`, `chore:`, `update:`, `change:`, `docs:`, `style:`, `build:`, `ci:`
  - **Removed**: `remove:`, `deprecate:`, `delete:`, `drop:`
- Strips redundant conventional prefixes and links issue/PR references (`#123`).
- Formats dates according to ISO 8601 (`YYYY-MM-DD`).
- Preserves existing `CHANGELOG.md` history by prepending the newly generated release block.

## How to Run

```bash
# Direct CLI execution
bash skills/generate-changelog/scripts/changelog.sh

# Or with Python
python skills/generate-changelog/scripts/generate-changelog.py --version "v1.2.0"
```
