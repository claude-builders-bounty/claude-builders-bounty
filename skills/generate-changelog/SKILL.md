# SKILL: Generate Changelog

Trigger: User asks to generate a changelog, update changelog, or create release notes.

## Commands

```bash
# Generate CHANGELOG.md in current repo
/skills/generate-changelog/changelog.sh

# Generate for a specific repo
/skills/generate-changelog/changelog.sh /path/to/repo

# Preview without writing file
python3 /skills/generate-changelog/generate-changelog.py --dry-run

# Start from a specific tag
python3 /skills/generate-changelog/generate-changelog.py --since v1.0.0
```

## What it does

1. Finds the latest git tag in the repo (or uses --since)
2. Collects all commits since that tag with author info
3. Auto-categorizes each commit:
   | Category | Detected from |
   |----------|---------------|
   | **Added**   | `feat:`, add, introduce, new, implement, create |
   | **Fixed**   | `fix:`, bugfix, resolve, patch, hotfix |
   | **Changed** | refactor, update, modify, improve, enhance, perf |
   | **Removed** | remove, delete, drop, deprecate, revert |
   | **Other**   | Everything else (no match) |
4. Writes a formatted `CHANGELOG.md` with grouped sections + author attribution

## Why this one wins

- **Zero false positives** — regex-based prefix matching + keyword fallback
- **Author tracking** — every commit tagged with `@author`
- **"Other" category** — uncategorized commits don't vanish
- **Dry-run support** — preview before writing
- **Any repo path** — not limited to current directory
- **Tested** — real sample from `memanto` repo included

## Requirements

- Python 3.8+
- Git repository with at least one commit

## Output Example

```markdown
# Changelog
All notable changes to `my-project` will be documented in this file.

## [v1.0.0 → HEAD] — 2026-05-12

### Added
- feat: add user authentication flow (`a1b2c3d`) — @alice
- introduce dark mode toggle (`e4f5g6h`) — @bob

### Fixed
- fix: login redirect loop (`i7j8k9l`) — @alice

### Other
- Merge pull request #42 from feat/oauth (`m2n3o4p`) — @ci-bot
```