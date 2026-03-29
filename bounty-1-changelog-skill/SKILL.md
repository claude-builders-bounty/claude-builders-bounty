---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history using conventional commits
command: /changelog
aliases:
  - /generate-changelog
tags:
  - git
  - changelog
  - release
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from a project's git history, categorized by conventional commit types.

## When to Use

- Before a release to document what changed
- To audit recent work since the last tag
- To generate release notes for a PR or GitHub Release

## How It Works

1. Detect the last git tag (or use all history if none exists)
2. Parse each commit using conventional-commit prefix detection
3. Categorize into **Added**, **Fixed**, **Changed**, **Removed**, **Other**
4. Write a properly formatted CHANGELOG following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## Instructions

Run the bundled bash script from the project root:

```bash
bash bounty-1-changelog-skill/changelog.sh
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--output`, `-o` | Output file path | `CHANGELOG.md` |
| `--since` | Tag, commit hash, or date to start from | auto-detect last tag |
| `--dry-run` | Print to stdout, don't write file | off |
| `--append` | Prepend new section to existing CHANGELOG | off |
| `--version` | Override version label (e.g. `v2.0.0`) | auto-increment from last tag |
| `--no-color` | Disable colored terminal output | auto-detect |
| `--repo` | Path to git repository | current directory |

### Examples

```bash
# Generate CHANGELOG.md in project root
bash bounty-1-changelog-skill/changelog.sh

# Preview without writing
bash bounty-1-changelog-skill/changelog.sh --dry-run

# Custom output path
bash bounty-1-changelog-skill/changelog.sh -o docs/CHANGELOG.md

# Append to existing changelog
bash bounty-1-changelog-skill/changelog.sh --append

# Specific range
bash bounty-1-changelog-skill/changelog.sh --since v1.2.0

# Override version label
bash bounty-1-changelog-skill/changelog.sh --version v3.0.0
```

## Commit Convention

For best categorization, use conventional commit prefixes:

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `new:`, `feature:` | Added |
| `fix:`, `bug:`, `bugfix:`, `hotfix:`, `patch:` | Fixed |
| `refactor:`, `perf:`, `chore:`, `build:`, `ci:`, `style:`, `docs:`, `test:`, `update:`, `bump:`, `revert:` | Changed |
| `remove:`, `delete:`, `drop:`, `deprecate:` | Removed |

Commits without a recognized prefix are classified via keyword fallback analysis, or placed in **Other**.

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v1.1.0] - 2026-03-29

> 12 commit(s) since v1.0.0

### Added
- feat(auth): add OAuth2 PKCE flow (`a1b2c3d`)

### Fixed
- fix: resolve timezone offset in scheduler (`e5f6a7b`)

### Changed
- refactor(api): migrate to Redis sliding window (`c9d0e1f`)

### Removed
- remove: drop legacy v1 endpoints (`a9b0c1d`)
```

## Requirements

- Bash 4+ (associative arrays / mapfile)
- Git repository with commit history
