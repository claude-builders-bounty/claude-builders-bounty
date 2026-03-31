# Generate Changelog

A Claude Code skill that generates a structured `CHANGELOG.md` from git history, auto-categorizing commits into **Added / Fixed / Changed / Removed**.

## Setup (3 steps)

1. Copy the `skills/generate-changelog/` folder into your project
2. Make the script executable: `chmod +x skills/generate-changelog/changelog.sh`
3. Run it: `bash skills/generate-changelog/changelog.sh`

That's it.

## Usage

```bash
# Basic — generates CHANGELOG.md from commits since last tag
bash changelog.sh

# Output to a custom file
bash changelog.sh -o docs/CHANGELOG.md

# Include ALL history
bash changelog.sh -a

# Start from a specific tag
bash changelog.sh -t v1.0.0

# Help
bash changelog.sh -h
```

## How It Works

The script reads git log and categorizes each commit by its prefix:

| Prefix | Category |
|--------|----------|
| `feat:` / `add:` / `added:` | **Added** |
| `fix:` / `bug:` / `hotfix:` | **Fixed** |
| `refactor:` / `chore:` / `docs:` | **Changed** |
| `remove:` / `deprecate:` / `delete:` | **Removed** |
| _(anything else)_ | **Changed** (default) |

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-03-31

### Added
- feat: add user authentication module
- add: API rate limiting middleware

### Fixed
- fix: resolve null pointer in auth handler
- bug: correct timezone offset in date parser

### Changed
- refactor: extract config loading into shared module
- chore: update dependencies

### Removed
- remove: deprecated v1 API endpoints
```

## Tested On

Tested on multiple real GitHub repositories with conventional and non-conventional commit messages. Works with both `git log` style prefixes and parenthetical scopes like `feat(auth):`.

## Requirements

- Bash 4+
- Git (any recent version)
- A git repository with at least one commit
