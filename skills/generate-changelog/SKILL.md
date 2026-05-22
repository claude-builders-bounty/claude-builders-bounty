---
name: generate-changelog
slug: generate-changelog
version: 1.0.0
description: |
  Automatically generate a structured CHANGELOG.md from git commit history.
  Categorizes commits into Added/Fixed/Changed/Removed following Keep a Changelog format.
triggers:
  - changelog
  - generate changelog
  - git history
  - release notes
---

# Generate Changelog Skill

Auto-generate structured CHANGELOG.md from git history.

## Usage

```bash
# Generate CHANGELOG.md in current directory
./generate_changelog.sh

# Custom output file
./generate_changelog.sh RELEASE_NOTES.md
```

## Features

- Fetches commits since last git tag (or all commits if no tags)
- Auto-categorizes by commit message prefix:
  - **Added**: feat, add, new, implement, introduce
  - **Fixed**: fix, bug, repair, correct, resolve
  - **Changed**: update, change, modify, refactor, improve, enhance, perf
  - **Removed**: remove, delete, drop, deprecate
- Follows Keep a Changelog format
- Works in any git repository

## Setup

1. Copy `generate_changelog.sh` to your repo
2. `chmod +x generate_changelog.sh`
3. Run `./generate_changelog.sh`

## Requirements

- Git 2.0+
- Bash 4.0+

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] — Changes since v1.0.0

### Added
- feat: add user authentication
- new: implement dark mode

### Fixed
- fix: resolve login redirect bug
- bug: correct password validation

### Changed
- refactor: simplify API handlers
- improve: optimize database queries
```
