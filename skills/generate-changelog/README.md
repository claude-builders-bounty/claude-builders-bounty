# Generate Changelog Skill

Automatically generate a structured `CHANGELOG.md` from git commit history.

## Quick Start

```bash
cd your-git-repo
cp skills/generate-changelog/generate_changelog.sh .
chmod +x generate_changelog.sh
./generate_changelog.sh
```

## Features

- ✅ Fetches commits since last git tag
- ✅ Auto-categorizes: Added / Fixed / Changed / Removed
- ✅ Follows Keep a Changelog format
- ✅ Works in any git repository
- ✅ Zero dependencies (bash + git only)

## How it works

1. Detects the last git tag
2. Fetches all commits since that tag
3. Parses commit messages for categorization keywords
4. Generates a properly formatted CHANGELOG.md

## Categorization Rules

| Category | Keywords |
|----------|----------|
| **Added** | feat, add, new, implement, introduce |
| **Fixed** | fix, bug, repair, correct, resolve |
| **Changed** | update, change, modify, refactor, improve, enhance, perf |
| **Removed** | remove, delete, drop, deprecate |

## Example

```bash
$ ./generate_changelog.sh
✓ Generated CHANGELOG.md

$ cat CHANGELOG.md
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] — Changes since v1.0.0

### Added
- feat: add user authentication
- new: implement dark mode

### Fixed
- fix: resolve login redirect bug
```

## Testing

Tested on this repository. See PR for sample output.

## Requirements

- Git 2.0+
- Bash 4.0+
