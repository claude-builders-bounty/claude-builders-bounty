# SKILL: Generate CHANGELOG from git history

## Trigger
Activated when user says "generate changelog", "/generate-changelog", or asks to create a CHANGELOG.md from git history.

## What it does

This skill generates a structured CHANGELOG.md from a project's git history. It:
1. Fetches commits since the last git tag
2. Auto-categorizes them into: **Added**, **Fixed**, **Changed**, **Removed**
3. Outputs a properly formatted CHANGELOG.md

## Usage

```bash
./changelog.sh [options]
```

**Options:**
- `--since-tag <tag>` — generate changelog from a specific tag
- `--output <file>` — output file path (default: CHANGELOG.md)
- `--dry-run` — preview without writing file

## How it works

### Categorization Logic
Uses conventional commit prefixes to categorize:
| Prefix | Category |
|--------|----------|
| `feat:`, `feat(` | **Added** |
| `fix:`, `fix(` | **Fixed** |
| `chore:`, `docs:`, `style:`, `refactor:` | **Changed** |
| `BREAKING CHANGE`, `!:` | **Removed** (breaking) |

Unmatched commits → **Changed** (misc)

### Output Format
```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - YYYY-MM-DD

### Added
- feature description (#PR_NUMBER)

### Fixed
- bug fix description

### Changed
- change description

### Removed
- removed feature description

---

## [1.0.0] - YYYY-MM-DD
...
```

## Requirements
- `git`
- `bash`
- `gnu sed` (for cross-platform compatibility)

## See also
- `changelog.sh` — the underlying bash implementation
- `sample-output.md` — sample changelog generated from this repo
