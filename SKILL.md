# CHANGELOG Generator Skill

Generate a structured CHANGELOG.md from a project's git history.

## Usage

Run via Claude Code:
```
/generate-changelog
```

Or standalone:
```bash
bash changelog.sh
```

## How It Works

1. Fetches all commits since the last git tag
2. Auto-categorizes into: Added / Fixed / Changed / Removed
3. Outputs a properly formatted CHANGELOG.md

## Setup

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run: `./changelog.sh`

## Output Format

```markdown
# Changelog

## [Unreleased]

### Added
- list of new features

### Fixed
- list of bug fixes

### Changed
- list of changes

### Removed
- list of removed features
```

## Example

See a working example in a real repo when you test.
