# CHANGELOG Generator

## Description

Generate a structured, categorized `CHANGELOG.md` from your git history.

## Commands

### `/generate-changelog`

Generates a CHANGELOG.md from git commits since the last tag.

**What it does:**

1. Finds the most recent git tag (or uses all commits if no tags exist)
2. Reads all non-merge commits since that tag
3. Auto-categorizes each commit into: **Added**, **Fixed**, **Changed**, **Removed**
4. Outputs a properly formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format

**Categorization rules:**

| Prefix/Keyword | Category |
|----------------|----------|
| `feat:`, `add`, `new`, `implement`, `create`, `introduce` | Added |
| `fix:`, `bugfix`, `hotfix`, `resolve`, `repair`, `patch` | Fixed |
| `refactor`, `chore`, `update`, `improve`, `enhance`, `docs`, `test`, `ci`, `build`, `style`, `perf` | Changed |
| `remove`, `delete`, `deprecate`, `drop` | Removed |

**Usage:**

```bash
# Commits since last tag (default)
bash changelog.sh

# Commits since a specific tag
bash changelog.sh v1.0.0

# All commits
bash changelog.sh --all
```

**Output example:**

```markdown
# Changelog

## [Unreleased] — 2026-04-04

### Added
- feat: add user authentication (`a1b2c3d`) — *Developer Name*
- implement dark mode toggle (`e4f5g6h`) — *Another Dev*

### Fixed
- fix: resolve login timeout issue (`i7j8k9l`) — *Developer Name*

### Changed
- refactor: simplify database queries (`m0n1o2p`) — *Another Dev*
- docs: update API reference (`q3r4s5t`) — *Developer Name*
```
