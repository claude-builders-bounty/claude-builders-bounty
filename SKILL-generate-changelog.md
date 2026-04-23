---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history
---

# Generate Changelog Skill

Automatically generates a structured `CHANGELOG.md` file from your git commit history since the last tag.

## Usage

In Claude Code, run:

```
/generate-changelog
```

## What It Does

1. **Finds the last git tag** (or uses initial commit if no tags exist)
2. **Fetches commits** since that tag
3. **Auto-categorizes commits** into:
   - **Added**: `feat:`, `add:`, or commits starting with "Add"
   - **Fixed**: `fix:`, `bug:`, or commits starting with "Fix"
   - **Changed**: `refactor:`, `update:`, `change:`, `chore:`, or commits starting with "Change"/"Update"
   - **Removed**: `remove:`, `delete:`, or commits starting with "Remove"/"Delete"
4. **Generates CHANGELOG.md** in Keep a Changelog format
5. **Preserves existing changelog** (appends new entries to the top)

## Requirements

- Git repository with at least one commit
- Works best with conventional commit messages, but handles any format

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-04-23

### Added

- User authentication with Clerk
- Dashboard layout with sidebar navigation
- SQLite database integration

### Fixed

- Hydration mismatch on dashboard page
- Mobile responsive menu not closing

### Changed

- Updated Next.js to 15.1.2
- Refactored auth middleware for edge runtime

### Removed

- Deprecated API routes in favor of Server Actions

## [1.0.0] - 2026-04-15

...
```

## Commit Message Tips

For best auto-categorization, use conventional commits:

- `feat: add user dashboard` → **Added**
- `fix: hydration mismatch` → **Fixed**
- `refactor: auth middleware` → **Changed**
- `remove: deprecated routes` → **Removed**

Or start with action verbs:

- `Add user dashboard` → **Added**
- `Fix hydration mismatch` → **Fixed**
- `Update Next.js version` → **Changed**
- `Remove deprecated routes` → **Removed**

## Script

This skill runs the `changelog.sh` script. You can also run it directly:

```bash
bash changelog.sh
```

## License

MIT
