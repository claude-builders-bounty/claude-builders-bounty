---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history since the last tag. Use when Jon asks to produce a changelog, release notes, or a version diff from git commits.
---

# Generate Changelog

Produces a categorized `CHANGELOG.md` from git history.

## When to use
- "Make a changelog"
- "What changed since the last release?"
- "Write release notes from git"

## How it works
- Range = commits since the last git tag (`git describe --tags --abbrev=0`). If no tag exists, falls back to all history from the first commit.
- Each commit is categorized by its subject prefix:
  - `feat`/`add`/`new` → **Added**
  - `fix`/`bug`/`resolve`/`patch` → **Fixed**
  - `remove`/`rm`/`delete`/`drop` → **Removed**
  - everything else → **Changed**
- Output is written to `CHANGELOG.md` in the repo root.

## Usage
As a command (this skill), or directly:
```bash
bash changelog.sh            # writes CHANGELOG.md
python3 changelog.py out.md  # custom output path
```

## Output format
```markdown
# Changelog

## [2026-07-13] - my-project
_since tag v0.1.0_

### Added
- feat: add export to CSV (a1b2c3d)

### Changed
- refactor: split parser module (e4f5g6h)

### Fixed
- fix: handle empty config (i7j8k9l)

### Removed
- remove: drop legacy XML loader (m0n1o2p)
```

## Notes
- No network calls. Runs fully locally.
- Deterministic: same history → same output (aside from the date line).
