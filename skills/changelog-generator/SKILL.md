---
name: changelog-generator
description: Generate structured CHANGELOG.md from git history
---

# Changelog Generator

Generates a structured `CHANGELOG.md` from git commit history, auto-categorized by conventional commit type.

## Usage

```bash
bash changelog.sh
```

## What It Does

1. Finds the latest git tag (or falls back to first commit)
2. Extracts all commits since that tag
3. Categorizes by conventional commit prefix:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `refactor:`, `perf:`, `style:` → **Changed**
   - `remove:`, `delete:` → **Removed**
   - Everything else → **Miscellaneous**
4. Outputs formatted `CHANGELOG.md`

## Output Example

```markdown
# Changelog

## Unreleased - 2026-05-14

_Generated from git commits after v1.0.0._

### Added
- feat: add user authentication (abc1234)
- feat: add dark mode toggle (def5678)

### Fixed
- fix: resolve login timeout (ghi9012)

### Changed
- refactor: simplify database queries (jkl3456)

### Removed
- remove: deprecated API endpoints (mno7890)
```

## Requirements

- Git repository with commits
- bash 4+
- No external dependencies

## Customization

Edit the category mappings in `changelog.sh` to change how commit prefixes map to sections.
