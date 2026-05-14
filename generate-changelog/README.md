# Generate Changelog

A small Claude Code skill plus Bash script that generates a structured `CHANGELOG.md` from git history since the latest tag.

## Setup in 3 steps

1. Copy this folder into your repo or Claude skills directory.
2. From your repo root, run `bash generate-changelog/changelog.sh`.
3. Open `CHANGELOG.md` and review the generated Added / Fixed / Changed / Removed sections.

Optional release name:

```bash
CHANGELOG_VERSION=v1.2.3 bash generate-changelog/changelog.sh
```

## What it does

- Detects the latest git tag and reads commits from that tag to `HEAD`.
- Falls back to the full repo history when no tag exists.
- Ignores merge commits.
- Auto-categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a formatted `CHANGELOG.md`.

## Example

Input commits:

```text
feat: add webhook delivery
fix: repair OAuth callback handling
docs: update installation guide
remove: delete legacy token parser
```

Output:

```markdown
# Changelog

## [Unreleased] - 2026-05-15

Generated from git history since v1.0.0.

### Added

- add webhook delivery

### Fixed

- repair OAuth callback handling

### Changed

- update installation guide

### Removed

- delete legacy token parser
```
