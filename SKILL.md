---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
command: /generate-changelog
---

# SKILL: Generate Structured CHANGELOG from Git History

## What This Does
Automatically generates a `CHANGELOG.md` by reading git commits since the last tag,
categorizing them into **Added**, **Fixed**, **Changed**, and **Removed** sections.

## Command
```
/generate-changelog
```

## How It Works
1. Finds the last git tag (or uses all history if no tags)
2. Reads all commits since that tag
3. Categorizes based on conventional commit prefixes and keywords:
   - **Added**: `feat:`, `add`, `create`, `implement`, `new`, `introduce`
   - **Fixed**: `fix:`, `bugfix:`, `resolve`, `patch`
   - **Changed**: `refactor:`, `update`, `change`, `improve`, `chore:`, `docs:`, etc.
   - **Removed**: `remove`, `delete`, `drop`, `deprecate`
4. Outputs a formatted `CHANGELOG.md`

## Usage

### As a bash script:
```bash
bash changelog.sh                  # outputs CHANGELOG.md
bash changelog.sh my-changes.md   # outputs to custom file
```

### As a Claude Code command:
When asked to `/generate-changelog`, run:
```bash
bash changelog.sh
```
Then display the contents of the generated CHANGELOG.md.

## Requirements
- `bash` (standard on most systems)
- `git` (must be in a git repository)

## Output Format
```markdown
# Changelog

## [Unreleased] — 2026-03-30

### Added
- feat: new login page (`a1b2c3d`) — Author Name

### Fixed
- fix: resolve null pointer crash (`e4f5g6h`) — Author Name

### Changed
- refactor: simplify auth flow (`i7j8k9l`) — Author Name

### Removed
- remove: deprecated v1 API (`m0n1o2p`) — Author Name
```
