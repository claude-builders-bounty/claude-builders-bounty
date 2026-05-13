# Generate Changelog

Creates a structured `CHANGELOG.md` from git history.

## Usage

```
/generate-changelog
```

Or run the companion script directly:
```bash
bash scripts/changelog.sh
```

## What it does

1. Fetches commits since the last git tag
2. Parses Conventional Commits (feat:, fix:, chore:, docs:, refactor:, etc.)
3. Auto-categorizes into: Added, Fixed, Changed, Removed
4. Groups by version tag
5. Outputs a properly formatted CHANGELOG.md

## How it works

- Runs `scripts/changelog.sh` in the project root
- The script checks for the last tag with `git describe`
- Falls back to first commit if no tags exist
- Parses commit messages using Conventional Commit patterns
- Outputs Markdown-ready changelog

## Output Format

```markdown
# Changelog

## [v1.2.0] - 2026-05-13

### Added
- feat: add changelog generator script
- feat: support multi-language commit parsing

### Fixed
- fix: handle empty tag history gracefully

### Changed
- refactor: improve commit categorization logic
```

## Dependencies

- bash
- git

## Setup

1. Copy `scripts/changelog.sh` to your project
2. Make it executable: `chmod +x scripts/changelog.sh`
3. Run `/generate-changelog` or `bash scripts/changelog.sh`
