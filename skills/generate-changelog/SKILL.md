# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from git history.

## Usage

Run via bash script:
```bash
bash changelog.sh [OPTIONS]
```

Or invoke directly from Claude Code with `/generate-changelog`.

## What It Does

- Fetches all commits since the last git tag (or from repo creation if no tags)
- Auto-categorizes commits into: **Added**, **Fixed**, **Changed**, **Removed**
- Outputs a properly formatted `CHANGELOG.md` to the project root

## Commit Convention

For best results, use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Category |
|--------|----------|
| `feat:` / `add:` | Added |
| `fix:` / `bug:` | Fixed |
| `change:` / `refactor:` / `chore:` | Changed |
| `remove:` / `deprecate:` | Removed |
| Any other | Changed (default) |

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `-o FILE` | Output file path | `CHANGELOG.md` |
| `-t TAG` | Start from this tag (inclusive) | latest tag |
| `-a` | Include all history, not just since last tag | off |
| `-s` | Summary mode — one-line per commit | off |

## Requirements

- Git installed and repo initialized
- Commits exist in the repository

## Example Output

```markdown
# Changelog

## [Unreleased] - 2026-03-31

### Added
- feat: add user authentication module
- add: API rate limiting middleware

### Fixed
- fix: resolve null pointer in auth handler
- bug: correct timezone offset in date parser

### Changed
- refactor: extract config loading into shared module
- chore: update dependencies to latest versions

### Removed
- remove: deprecated v1 API endpoints
```
