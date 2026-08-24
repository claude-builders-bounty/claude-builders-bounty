---
name: generate-changelog
description: Automatically scans git commits since the last tag and creates or updates a structured Keep-a-Changelog formatted CHANGELOG.md categorized into Added, Fixed, Changed, and Removed.
---

# Generate Structured Changelog

## Overview
This skill inspects the repository's git commit history since the most recent release tag, parses Conventional Commits prefixes (`feat`, `fix`, `refactor`, `chore`, `docs`, `revert`), groups them into standard Keep-a-Changelog sections, and prepends the new release section to `CHANGELOG.md`.

## Instructions
1. Run `bash skills/generate-changelog/changelog.sh` or trigger the `/generate-changelog` command.
2. The script will automatically detect the last git tag with `git describe --tags --abbrev=0`.
3. Commits are categorized as follows:
   - `feat: ...` -> `### Added`
   - `fix: ...` -> `### Fixed`
   - `refactor:`, `perf:`, `chore:`, `docs:`, `style:` -> `### Changed`
   - `revert:`, `remove:`, `deprecated:` -> `### Removed`
4. Formats each entry with clean message text and short commit hash links.
5. Prepends the resulting release notes block to `CHANGELOG.md` with the current ISO date.
