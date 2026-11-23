---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history, categorized into Added, Fixed, Changed, and Removed.
---

# Generate Changelog Skill

Automatically parses git commits and tags to produce a structured, release-ready `CHANGELOG.md` adhering to the [Keep a Changelog](https://keepachangelog.com/) standard.

## When to Use
- Triggered by `/generate-changelog` command.
- When creating a release, tag, or summarizing recent git changes.
- When generating or updating `CHANGELOG.md`.

## Execution Workflow

1. Execute the changelog generator script:
   ```bash
   bash changelog.sh
   ```

2. Optional configurations:
   - **Preview in terminal**:
     ```bash
     bash changelog.sh --stdout
     ```
   - **Prepend to existing CHANGELOG**:
     ```bash
     bash changelog.sh --prepend
     ```
   - **Custom release title**:
     ```bash
     bash changelog.sh --version-title "v1.0.0"
     ```
   - **Custom tag range**:
     ```bash
     bash changelog.sh --since-tag "v0.9.0"
     ```
   - **Include all commits**:
     ```bash
     bash changelog.sh --all
     ```

## Output Format
Commits are categorized automatically based on conventional commit prefixes:
- **Added**: `feat:`, `feature:`, `add:`, `create:`
- **Fixed**: `fix:`, `bug:`, `patch:`, `resolve:`
- **Changed**: `refactor:`, `perf:`, `update:`, `docs:`, `chore:`
- **Removed**: `remove:`, `delete:`, `deprecate:`
