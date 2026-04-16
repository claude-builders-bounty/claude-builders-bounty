---
name: generate-changelog
description: >
  Generate a structured CHANGELOG.md from git history.
  Categorizes commits into Added / Fixed / Changed / Removed.
triggers:
  - generate changelog
  - create changelog
  - changelog from git
  - release notes
---

# Generate Changelog

Run `bash scripts/changelog.sh [output_file]` to create a CHANGELOG.md from git commit history.

## What it does

1. Finds the latest git tag (or uses all commits if no tags exist)
2. Parses commits since that tag
3. Categorizes by conventional commit prefix:
   - `feat:` or `feat(scope):` → **Added**
   - `fix:` or `fix(scope):` → **Fixed**
   - `change:`/`refactor:` → **Changed**
   - `remove:`/`delete:` → **Removed**
   - Everything else → **Other**
4. Writes a formatted `CHANGELOG.md`

## Usage

```bash
# Default: writes CHANGELOG.md
bash scripts/changelog.sh

# Custom output path
bash scripts/changelog.sh docs/release-notes.md
```

## Example Output

```markdown
# Changelog (since v1.0.0)

_Generated on 2026-04-16_

### Added
- Add user authentication module (`a1b2c3d`)
- Add dark mode toggle (`e4f5g6h`)

### Fixed
- Fix login redirect loop (`i7j8k9l`)
- Fix null pointer on empty profile (`m0n1o2p`)

### Changed
- Refactor database connection pool (`q3r4s5t`)

### Other
- Update README with install steps (`u6v7w8x`)
```

## Requirements

- Git repository with at least one commit
- Bash 4+ (for associative arrays)
- For best results, use [Conventional Commits](https://www.conventionalcommits.org/) format
