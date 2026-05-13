# Git History Changelog Generator

Generate a structured `CHANGELOG.md` from the commits since the latest git tag.

## Setup

1. Copy `changelog.sh` into the root of any git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md` and commit it.

## What It Does

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Falls back to the full history if the repository has no tags.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep a Changelog style `CHANGELOG.md`.

## Optional Claude Code Skill

Copy `SKILL.md` into `~/.claude/skills/generate-changelog/SKILL.md`, then ask Claude Code to run `/generate-changelog` in a project repository.

## Sample Output

See `sample-output.md` for output generated from this repository's git history.
