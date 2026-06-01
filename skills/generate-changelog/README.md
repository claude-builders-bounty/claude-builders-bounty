# Generate CHANGELOG Skill

Automatically generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. Copy `SKILL.md` to your Claude Code/Hermes skills directory
2. Make the script executable: `chmod +x generate-changelog.sh`
3. Run from any git repo: `bash generate-changelog.sh`

## Usage

```bash
# Generate CHANGELOG since last tag
bash generate-changelog.sh

# Custom output path
bash generate-changelog.sh --output docs/CHANGELOG.md

# Since a specific tag
bash generate-changelog.sh --since v1.0.0
```

## Example Output

```markdown
# Changelog

## [Unreleased] - 2026-06-01

### Added
- feat: add user authentication module
- feat: implement dark mode toggle

### Fixed
- fix: resolve login redirect loop
- fix: patch mobile layout overflow

### Changed
- refactor: restructure database connection pool
- chore: update dependencies

### Removed
- remove: drop deprecated v1 API
```
