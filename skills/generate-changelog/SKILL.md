---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag, auto-categorizing commits into Added/Fixed/Changed/Removed sections.
---

# generate-changelog

Generate a structured `CHANGELOG.md` from git history since the last tag.

## Setup

1. Copy `changelog.py` to your project (or anywhere on your `$PATH`)
2. Copy this `SKILL.md` to `~/.claude/skills/generate-changelog.md`
3. Run `/generate-changelog` in any git repo

## Usage

```
/generate-changelog
/generate-changelog path/to/repo
/generate-changelog --preview        # print to terminal instead of writing file
```

Or directly:

```bash
python3 changelog.py                 # current directory
python3 changelog.py /path/to/repo
python3 changelog.py --preview
```

## What it does

- Finds the most recent git tag with `git describe --tags`
- Collects all commits since that tag (skips merge commits)
- Categorizes each commit into **Added**, **Fixed**, **Changed**, or **Removed** using:
  - Conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
  - Plain-English keyword matching as fallback
- Writes a formatted `CHANGELOG.md` to the repo root

## Categorization rules

| Prefix / keyword | Category |
|-----------------|----------|
| `feat`, `add`, `new`, `implement` | **Added** |
| `fix`, `bug`, `patch`, `resolve` | **Fixed** |
| `refactor`, `update`, `bump`, `improve` | **Changed** |
| `remove`, `drop`, `delete`, `deprecate` | **Removed** |
| *(anything else)* | **Changed** |

## Output format

```markdown
# Changelog

## [Unreleased] — 2026-06-26

*Changes since `v1.2.3`*

### Added
- feat: add dark mode support  (`a1b2c3d` — 2026-06-20)

### Fixed
- fix: correct null pointer in login flow  (`e4f5g6h` — 2026-06-18)

### Changed
- refactor: simplify auth middleware  (`i7j8k9l` — 2026-06-15)

### Removed
- drop support for Python 3.8  (`m1n2o3p` — 2026-06-10)
```

## Requirements

- Python 3.10+
- git
