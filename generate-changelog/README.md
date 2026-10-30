# generate-changelog

Generates a structured `CHANGELOG.md` from a project's git history. Bounty solution for [#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).

## Setup

1. Copy `scripts/generate-changelog.sh` into your repository (anywhere on `PATH` or the repo root).
2. Requires `git` and `bash` — both already present on macOS and most Linux systems.
3. Done.

## Usage

```bash
# Since the latest tag (default)
bash generate-changelog.sh

# Since a specific tag
bash generate-changelog.sh v1.2.0

# Custom output file
bash generate-changelog.sh v1.2.0 --output RELEASE-NOTES.md

# As a Claude Code skill: install generate-changelog/ into ~/.claude/skills/ or .claude/skills/
# then ask Claude to "generate a changelog" — it runs the script and reviews the output.
```

## How it works

1. Resolves the start point: the explicit tag argument, or the latest tag via `git describe --tags --abbrev=0`; with no tags it covers the whole history.
2. Collects non-merge commits in that range.
3. Categorizes each commit into **Added / Fixed / Changed / Removed / Other** by conventional-commit prefix (`feat:`, `fix:`, `chore:`, …) and keyword matching (`add`, `fix`, `remove`, `update`, `refactor`, …).
4. Cleans entries: strips type prefixes like `feat(auth):` and PR references like `(#123)`, shortens the hash to 7 chars, deduplicates.
5. Writes `CHANGELOG.md` with `Added → Fixed → Changed → Removed → Other` sections.

## Example output

Given commits `feat: add user login`, `fix: handle empty password (fixes #12)`, `refactor: split auth module` since tag `v1.0.0`:

```markdown
# Changelog

## Changes since v1.0.0 (2026-10-31)

### Added
- user login (`a1b2c3d`)

### Fixed
- handle empty password (`e4f5g6h`)

### Changed
- split auth module (`i7j8k9l`)
```

## Edge cases handled

- Repository with no tags → full-history changelog.
- Repository with no new commits since the tag → exits cleanly with a message, does not write an empty file.
- Merge commits are skipped (their content is duplicated by the merged commits).
- Conventional-commit scopes (`feat(api):`) and breaking-change markers (`feat!:`) are stripped from the entry text.
