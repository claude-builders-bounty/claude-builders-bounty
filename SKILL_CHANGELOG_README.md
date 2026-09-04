# Generate Changelog Skill

Automatically generates a structured `CHANGELOG.md` from git history using conventional commit prefixes.

## Setup

1. Copy `generate-changelog.sh` to your project root
2. Make it executable: `chmod +x generate-changelog.sh`
3. Run: `./generate-changelog.sh` (outputs `CHANGELOG.md`)

## How It Works

- Fetches all commits since the last git tag
- Categorizes by conventional commit prefix:
  - `feat:` → **Added**
  - `fix:` → **Fixed**
  - `refactor:`, `style:`, `perf:` → **Changed**
  - `revert:`, `remove:`, `delete:` → **Removed**
  - `docs:`, `test:`, `ci:`, `chore:`, `build:` → **Other**
- Outputs formatted Markdown with date-stamped unreleased section

## Sample Output

```markdown
# Changelog

## [Unreleased] - 2026-09-04

### Added
- add app entry point

### Fixed
- add helper utility

### Other
- update readme
```

## Requirements

- Bash 4+
- Git installed and initialized repository
- At least one git tag present (uses `git describe --tags`)
