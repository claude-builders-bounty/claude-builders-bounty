# generate-changelog

A **Claude Code skill** that auto-generates a structured `CHANGELOG.md` from your git history.

## Setup (3 steps)

1. **Copy** `generate-changelog` into your project and make it executable:
   ```bash
   chmod +x generate-changelog
   ```
2. **Generate** your changelog:
   ```bash
   ./generate-changelog
   ```
3. **Optional:** Enable Claude Code integration by adding to `CLAUDE.md`:
   ```markdown
   ## Changelog
   Run \`./generate-changelog\` before tagging a release.
   ```

## Features

- 🔍 Fetches commits since last tag (or initial commit if no tags)
- 🏷️ Auto-categorizes: **Added**, **Fixed**, **Changed**, **Removed**, **Other**
- 🔗 Generates clickable GitHub commit links
- 🎨 Outputs clean, professional markdown
- 🐚 Works in Bash 3.2+ and zsh

## Sample

```markdown
# Changelog

## [v1.2.0] - 2026-07-08

### ✨ Added
- Dark mode support
- API rate limiting

### 🐛 Fixed
- Login redirect loop
```

## Bounty

This skill was created for **[claude-builders-bounty Issue #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)** ($50 bounty).
