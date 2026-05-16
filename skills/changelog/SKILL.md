---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history using conventional commits"
version: 1.0.0
author: Claude Builders Bounty
---

# Generate Changelog

Auto-generates a structured `CHANGELOG.md` from your project's git history.
Intelligently categorizes commits into `Added` / `Fixed` / `Changed` / `Removed` / `Security` / `Performance` / `Documentation` / `Infrastructure`.

## Usage

### As a CLI command
```bash
# Print changelog to stdout
python3 changelog.py

# Write to CHANGELOG.md
python3 changelog.py --write

# Specify a version
python3 changelog.py --version 2.1.0

# Test with sample data (no git repo needed)
python3 changelog.py --sample
```

### As a skill command
```
/generate-changelog
```
Runs `changelog.py --write` in the project root.

### Bash version
```bash
bash changelog.sh          # print to stdout
bash changelog.sh --write  # write to file
```

## Output

Groups commits into clean sections:

```markdown
# Changelog

## [1.0.0] - 2026-05-16

### Added
- Add AI-powered commit categorization ([a1b2c3d4](...))

### Fixed
- Handle empty git repos gracefully ([e5f6g7h8](...))

### Changed
- Simplify classification logic ([m3n4o5p6](...))
```

## Parsing Logic

1. First tries **Conventional Commits** parsing (`feat:`, `fix:`, `docs:`, etc.)
2. Falls back to **keyword detection** in the commit message
3. Everything unmatched goes into "Changed"

Supports scoped prefixes: `feat(auth): add login` → Added
Supports breaking changes: `feat!:` or `feat(scope)!:` → flagged in Added
