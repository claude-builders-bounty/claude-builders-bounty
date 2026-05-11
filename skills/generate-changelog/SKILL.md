---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history, auto-categorizing commits by type since the last tag.
trigger: /generate-changelog
---

# Changelog Generator

Auto-generate a structured `CHANGELOG.md` from git history by running:

```
/generate-changelog
```

Or from the command line:

```bash
bash skills/generate-changelog/scripts/generate-changelog.sh
```

## How It Works

1. Finds the most recent git tag (or falls back to the first commit)
2. Fetches all commits since that point
3. Categorizes each commit by its Conventional Commits prefix:
   - **Added**: `feat:`, `feature:`, `add:`, `implement:`
   - **Fixed**: `fix:`, `bug:`, `hotfix:`, `patch:`
   - **Changed**: `refactor:`, `chore:`, `update:`, `improve:`, `perf:`
   - **Removed**: `remove:`, `deprecate:`, `delete:`, `drop:`
4. Writes a clean `CHANGELOG.md` to the project root

## Output Format

The generated `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com) conventions:

```markdown
# Changelog

## [1.2.0] - 2026-05-11

### Added
- User authentication with OAuth2
- Dark mode support

### Fixed
- Login crash on iOS 18
- Memory leak in image cache

### Changed
- Bumped minimum deployment target to iOS 17
- Refactored network layer for testability

### Removed
- Deprecated v1 API support
- Legacy cookie-based sessions
```

## Requirements

- Git (`>= 2.0`)
- Bash (`>= 3.2`)

## Usage

### As a Claude Code Skill

1. Place the `skills/generate-changelog` folder in your project
2. Tell Claude Code: `/generate-changelog`
3. Claude will run the script and apply the result

### As a standalone script

```bash
bash skills/generate-changelog/scripts/generate-changelog.sh
```

The script is non-destructive — it prints the output to stdout by default. To write to `CHANGELOG.md`:

```bash
bash skills/generate-changelog/scripts/generate-changelog.sh --write
```

## Configuration

The script respects a `CHANGELOG_CONFIG` environment variable pointing to a JSON file with custom category keywords:

```json
{
  "added": ["feat", "feature", "add"],
  "fixed": ["fix", "bug", "hotfix", "patch"],
  "changed": ["refactor", "chore", "update", "improve", "perf"],
  "removed": ["remove", "deprecate", "delete", "drop"]
}
```
