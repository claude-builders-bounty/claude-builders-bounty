---
name: changelog
description: Generate a structured CHANGELOG.md from a project's git history. Auto-categorizes commits into Added/Fixed/Changed/Removed based on conventional commit prefixes. Use when the user asks to "generate changelog", "make a release", "summarize git history", or "create CHANGELOG.md".
---

# Changelog Skill

Auto-generate a `CHANGELOG.md` from git history. Works in two ways:

1. **Slash command**: `/generate-changelog` (Claude Code)
2. **Bash**: `bash changelog.sh [output_file]`

## What it does

- Fetches commits since the last git tag (or all commits if no tags)
- Categorizes each commit by conventional commit prefix:
  - `feat:` → **Added**
  - `fix:` → **Fixed**
  - `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `chore:`, `build:`, `ci:` → **Changed**
  - `BREAKING:`, `revert:`, "Remove" / "Delete" in subject → **Removed**
- Writes a properly formatted Markdown section with subheadings per category

## Installation (3 steps)

### Step 1: Copy the files

```bash
mkdir -p ~/.claude/skills/changelog
cp changelog.sh ~/.claude/skills/changelog/
chmod +x ~/.claude/skills/changelog/changelog.sh
```

### Step 2: Register the skill

Add to `~/.claude/skills/registry.json` (or just place this `SKILL.md` in your project's `.claude/skills/` folder):

```json
{
  "skills": {
    "changelog": {
      "path": "~/.claude/skills/changelog/SKILL.md"
    }
  }
}
```

### Step 3: Use it

- In Claude Code: type `/generate-changelog`
- From the shell: `bash ~/.claude/skills/changelog/changelog.sh`

Output defaults to `CHANGELOG.md` in the current directory. Pass a different path as the first argument.

## Example output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0 - 2026-06-18]

### Added

- User profile page with avatar upload
- Dark mode toggle in settings

### Fixed

- Login redirect loop on Safari
- Memory leak in image cache

### Changed

- Upgraded React to 18.3
- Refactored authentication module

### Removed

- Deprecated v1 API endpoints
```

## Conventional commit prefixes

This skill expects conventional commit messages for best results. Format: `<type>: <subject>` where `type` is one of:

- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `style` — formatting, no code change
- `refactor` — code change that neither fixes a bug nor adds a feature
- `perf` — performance improvement
- `test` — add/correct tests
- `chore` — tooling, dependencies, build
- `build` — build system changes
- `ci` — CI configuration changes
- `revert` — revert a previous commit
- `BREAKING` — breaking change (anywhere in subject)

Commits without a recognizable prefix are categorized as **Changed**.

## Customization

Edit the `case` statement in `changelog.sh` to add custom category rules or rename categories.

## License

MIT
