# Skill: Generate Changelog

## Description
Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage
Run the command:
```
/generate-changelog
```

Or from the terminal:
```bash
python changelog/generate_changelog.py
```

## Options
- `--repo PATH` — Path to the git repository (default: current directory)
- `--output FILE` — Output file path (default: CHANGELOG.md)
- `--since TAG` — Git ref to start from (default: last tag, or all commits)
- `--version VERSION` — Version label for this changelog entry
- `--dry-run` — Print to stdout instead of writing a file
- `--json` — Output as JSON instead of markdown

## What It Does
1. Fetches commits since the last git tag (or all commits if no tags exist)
2. Auto-categorizes commits into: **Added**, **Fixed**, **Changed**, **Removed**, **Security**
3. Outputs a properly formatted `CHANGELOG.md` with links to commit SHAs

## Commit Convention Support
Supports [Conventional Commits](https://www.conventionalcommits.org/) format:
- `feat:` → Added
- `fix:` → Fixed
- `refactor:`, `chore:`, `perf:` → Changed
- `remove:`, `revert:` → Removed
- `security:` → Security

Also falls back to keyword detection for non-conventional commit messages.

## Example Output
```markdown
# Changelog

## Changes since v0.1.0 (2026-05-30)

**5 commits** categorized below.

### Added
- add user model ([`abc1234`](...))
- **api**: add pagination support ([`def5678`](...))

### Fixed
- resolve null pointer in auth ([`ghi9012`](...))

### Changed
- clean up service layer ([`jkl3456`](...))

### Removed
- delete legacy migration script ([`mno7890`](...))
```
