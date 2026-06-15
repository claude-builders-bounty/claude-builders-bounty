---
name: changelog
description: "Generate a structured CHANGELOG.md from git history — auto-categorizes commits by type and writes to file."
version: 1.0.0
metadata:
  hermes:
    tags: [git, changelog, automation, productivity]
---

# Changelog Generator

Generate a structured `CHANGELOG.md` from git history between tags.

## When to use

- User asks to "generate changelog", "create CHANGELOG", or "update CHANGELOG"
- Preparing a release
- Tracking changes since last tag

## Usage

```bash
# Generate changelog between two most recent tags
python3 changelog.py

# With tag prefix (e.g. 'v' for v1.0.0)
python3 changelog.py --tag-prefix v

# Append to existing CHANGELOG.md
python3 changelog.py --append

# Custom output path
python3 changelog.py --output docs/CHANGELOG.md
```

## How it works

1. Fetches commits since the last git tag
2. Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
3. Outputs a formatted `CHANGELOG.md` file

## Categorization Logic

| Category | Triggers |
|----------|----------|
| Added    | add, feat, new, implement, create, introduce |
| Fixed    | fix, bug, patch, resolve, repair, correct |
| Changed  | update, change, modify, refactor, improve, tweak, adjust (default) |
| Removed  | remove, delete, drop, deprecate, clean |

## Requirements

- Python 3.8+
- Git installed
- At least 2 git tags in the repository

## Sample Output

```markdown
# Changelog

## [v1.2.0] - 2026-06-15

### Added
- Introduce dark mode support (a1b2c3d)
- Create user settings page (e4f5g6h)

### Fixed
- Fix login redirect on timeout (i7j8k9l)
- Patch memory leak in worker pool (m0n1o2p)

### Changed
- Refactor auth middleware (q3r4s5t)
- Update dependencies (u6v7w8x)
```
