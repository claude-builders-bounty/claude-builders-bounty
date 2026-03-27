# SKILL.md — Generate Changelog

Generate a structured `CHANGELOG.md` from git commit history, auto-categorized by Conventional Commits.

## Trigger

Use when the user says:
- `/generate-changelog`
- "generate a changelog"
- "create a changelog from git history"
- "what changed since the last tag"

## How to Run

```bash
bash /path/to/submissions/bounty-1/changelog.sh
```

### Options

```bash
# Default: from latest tag to HEAD
bash changelog.sh

# From a specific tag
bash changelog.sh -t v1.0.0

# Custom output file
bash changelog.sh -o RELEASE_NOTES.md

# Custom title and date
bash changelog.sh -n "Release Notes" -d 2026-03-27
```

## What It Does

1. Finds the latest git tag (or uses all commits if no tags exist)
2. Categorizes each commit by conventional prefix:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `refactor:`, `perf:`, `docs:`, `chore:`, `style:`, `test:`, `build:`, `ci:` → **Changed**
   - `revert:`, `remove:`, `delete:` → **Removed**
   - Breaking changes → **⚠️ Breaking Changes**
   - Non-conventional → **Other**
3. Writes a formatted `CHANGELOG.md`

## Example Output

```markdown
# Changelog

## [Unreleased] since v1.0.0 — 2026-03-27

### Added
- user authentication with JWT tokens
- dark mode toggle

### Fixed
- crash when config file is missing
- off-by-one in pagination

### Changed
- extract validation logic to utils module
- update dependencies

### Removed
- deprecated legacy API endpoints

### Other
- initial project setup
```

## Notes

- Requires git to be installed and the working directory to be a git repo
- Only processes commit subjects (first line), not body
- Supports `feat(scope):` scoped conventional commits
- Breaking changes detected by prefix or `BREAKING` keyword in message
