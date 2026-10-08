# Git Structured Changelog Generator

A turnkey Claude Code Skill & CLI tool that generates a structured, Keepachangelog-compliant `CHANGELOG.md` from git history.

## 3-Step Quickstart

1. **Clone or drop folder into your repo:**
   ```bash
   cp -r git_changelog_skill /path/to/your/project
   ```

2. **Generate Changelog:**
   ```bash
   bash git_changelog_skill/changelog.sh v1.0.0
   ```
   *(or `python git_changelog_skill/generate_changelog.py v1.0.0`)*

3. **View output:**
   Check generated `CHANGELOG.md` at repo root.

## Features
- **Tag-aware:** Automatically scopes changes since the latest git tag (`git describe --tags --abbrev=0`).
- **Semantic grouping:** Intelligently maps Conventional Commits into:
  - `Added` (`feat:`, `add:`, `new:`)
  - `Fixed` (`fix:`, `bug:`, `patch:`)
  - `Changed` (`refactor:`, `perf:`, `chore:`, `update:`)
  - `Removed` (`revert:`, `remove:`, `delete:`)
- **Non-destructive:** Appends new releases to the top of existing `CHANGELOG.md`.
