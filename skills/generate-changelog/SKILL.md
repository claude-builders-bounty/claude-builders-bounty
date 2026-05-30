# Generate Changelog Skill

## Trigger
Use this skill when asked to `/generate-changelog` or when the user wants to generate a CHANGELOG.md from git history.

## What it does
Runs `changelog.sh` against the current git repository and produces a structured `CHANGELOG.md` grouped by: Added, Fixed, Changed, Removed.

## Usage
1. Copy `changelog.sh` to the root of any git repository
2. Run: `bash changelog.sh`
3. Review the generated `CHANGELOG.md`

## Options
- `bash changelog.sh OUTPUT.md` — write to a custom filename
- Works with or without git tags; auto-detects range

## Output format
```md
## [Unreleased] - YYYY-MM-DD
### Added
### Fixed
### Changed
### Removed
```

## Requirements
- bash 4+
- git (any modern version)
