# Generate Changelog

A dependency-free changelog generator that works as a Python script or Claude Code skill.

## Setup in 3 steps

1. Copy the `generate-changelog` folder into your repo.
2. From your repo root, run `bash generate-changelog/changelog.sh`.
3. Open `CHANGELOG.md` — done.

Optional: set a version name with `CHANGELOG_VERSION=v1.2.3`.

## What it does

- Detects the latest git tag and reads commits since that tag.
- Falls back to the full repo history when no tag exists.
- Skips merge commits.
- Auto-categorizes into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a formatted `CHANGELOG.md`.

## Example

Input commits:

```
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
