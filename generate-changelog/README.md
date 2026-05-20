# Generate Changelog

Generate a structured `CHANGELOG.md` from the current repository's git history.

## Setup

1. Copy `changelog.sh` into the root of a git repository.
2. Run `bash changelog.sh` to generate `CHANGELOG.md`.
3. Optionally pass a custom output path: `bash changelog.sh docs/CHANGELOG.md`.

## Claude Code Entrypoints

This PR includes both Claude Code invocation styles:

- `.claude/commands/generate-changelog.md` exposes `/generate-changelog` as a project slash command.
- `.claude/skills/generate-changelog/SKILL.md` exposes the same workflow as a project skill.

## What It Does

- Reads commits since the most recent git tag, or all commits when no tag exists.
- Skips merge commits.
- Categorizes commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`.

## Validation

Run the included smoke test from this repository root:

```bash
bash generate-changelog/test-changelog.sh ./changelog.sh
```

The test creates a temporary git repository with a tag, generates a changelog from post-tag commits, and verifies all four output categories.

## Sample Output

Tested against this repository on `main`, which has no git tags:

```md
# Changelog

Generated 2026-05-20 for commits from all commits.

### Added

- initial README with bounty board

### Fixed

- None

### Changed

- None

### Removed

- None
```
