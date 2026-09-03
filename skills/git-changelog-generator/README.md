# Git Changelog Generator 📜

A zero-dependency Python script and Claude Code skill that automatically parses git history since the latest tag and produces a structured `CHANGELOG.md` matching the [Keep a Changelog](https://keepachangelog.com/) standard.

## Setup (2 Steps)

1. Copy `changelog.py` into your repository:
   ```bash
   cp skills/git-changelog-generator/changelog.py ./changelog.py
   ```
2. Run it whenever you want to generate or update your `CHANGELOG.md`:
   ```bash
   python changelog.py
   ```

## Features

- **Tag Auto-Detection**: Discovers the latest git tag via `git describe --tags --abbrev=0`. If no tags exist, it safely includes all commits up to the initial commit.
- **Conventional Commits Parsing**: Automatically categorizes commits into:
  - `Added` (`feat:`, `add:`)
  - `Fixed` (`fix:`, `bugfix:`)
  - `Changed` (`refactor:`, `perf:`, `chore:`, `update:`)
  - `Removed` (`drop:`, `remove:`, `delete:`)
- **Non-Destructive Update**: Prepends the new release section directly below the `# Changelog` header while preserving past historical entries.
- **Dry-Run Mode**: Inspect the generated markdown on stdout with `python changelog.py --dry-run`.

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-09-03

### Added
- Add OAuth2 provider for GitHub authentication
- Implement structured CHANGELOG generator skill

### Changed
- Refactor database connection pool to use WAL mode
- Update build pipeline dependencies to latest versions

### Fixed
- Resolve race condition in concurrent provider updates
```

## Running Tests

```bash
python skills/git-changelog-generator/test_changelog.py
```
