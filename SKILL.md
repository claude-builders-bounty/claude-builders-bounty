---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# generate-changelog

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

In any git repository, run:

```
/generate-changelog
```

This will scan commits since the last git tag and produce a formatted changelog.

## Features

- Scans commits since the last semantic version tag
- Auto-categorizes into: `Added`, `Fixed`, `Changed`, `Removed`, `Security`
- Groups by version (using git tags)
- Outputs a properly formatted `CHANGELOG.md`
- Handles conventional commit prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, etc.)

## Configuration

You can customize the output in your `CLAUDE.md`:

```yaml
changelog:
  output_file: CHANGELOG.md
  categories:
    feat: Added
    fix: Fixed
    refactor: Changed
    chore: Changed
    docs: Changed
    style: Changed
    perf: Changed
    test: Changed
    revert: Removed
    security: Security
  date_format: "%Y-%m-%d"
```

## Examples

### Sample output

```markdown
# Changelog

## [1.2.0] - 2026-03-15

### Added
- Add user authentication via OAuth
- Implement rate limiting middleware
- Add unit tests for API routes

### Fixed
- Fix memory leak in WebSocket handler
- Correct pagination offset calculation

### Changed
- Upgrade dependencies to latest versions
- Refactor database query layer
```

### Run as standalone script

```bash
bash changelog.sh
```
