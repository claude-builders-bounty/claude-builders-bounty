---
name: generate-changelog
description: Auto-generate a structured CHANGELOG.md from git commit history.
command: |
  bash ${SCRIPT_DIR}/changelog.sh --repo "${CLAUDE_CODE_PROJECT_DIR:-.}" --output "${CLAUDE_CODE_PROJECT_DIR:-.}/CHANGELOG.md"
trigger_events:
  - slash_command: /generate-changelog
---

# Generate Changelog

Creates or updates `CHANGELOG.md` in the current project by scanning git commits
since the last tag and categorizing them into:

- **Added** — new features (`feat:`, `feature:`, `add:`, `create:`, `implement:`)
- **Fixed** — bug fixes (`fix:`, `bugfix:`, `patch:`, `correct:`)
- **Changed** — refactors, updates, improvements (`refactor:`, `chore:`, `update:`, `perf:`)
- **Removed** — deprecated or deleted code (`remove:`, `delete:`, `deprecate:`, `drop:`)

## Usage

1. **Via slash command (Claude Code):**
   ```
   /generate-changelog
   ```

2. **Via terminal:**
   ```bash
   bash changelog.sh
   bash changelog.sh --since v1.0.0
   bash changelog.sh --repo /path/to/project --output docs/CHANGELOG.md
   ```

3. **Via Python directly:**
   ```bash
   python3 changelog.py -o ../CHANGELOG.md
   ```

## Requirements

- Python 3.8+
- Git CLI

## How it works

1. Finds the most recent git tag with `git describe --tags --abbrev=0`
2. Runs `git log <tag>..HEAD` to fetch new commits (no merge commits)
3. Parses each commit message using Conventional Commit prefixes
4. Groups by category and writes a clean `CHANGELOG.md`
