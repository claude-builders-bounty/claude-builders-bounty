---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag, auto-categorizing commits into Added/Fixed/Changed/Removed.
---

# generate-changelog

## Description
Generates a structured `CHANGELOG.md` from the project's git history since the last tag. Commits are auto-categorized into **Added**, **Fixed**, **Changed**, and **Removed** sections by parsing conventional commit prefixes.

## Usage
```bash
# Generate CHANGELOG for the current directory
python3 skills/generate-changelog/changelog.py

# Specify a custom repo path
python3 skills/generate-changelog/changelog.py --repo /path/to/project

# Custom output file
python3 skills/generate-changelog/changelog.py --output CHANGES.md

# Include all commits (ignore tag boundaries)
python3 skills/generate-changelog/changelog.py --all

# Set a custom header for the release
python3 skills/generate-changelog/changelog.py --header "v2.0.0 - 2026-05-13"
```

## Requirements
- Python 3.8+
- Git (installed and available in PATH)
- Must be run inside a git repository (or specify `--repo`)

## Output Format
```markdown
# Changelog

## [Unreleased] - 2026-05-13

### Added
- New feature description (#123)

### Fixed
- Bug fix description (#456)

### Changed
- Refactored module description (#789)

### Removed
- Deprecated feature (#012)
```
