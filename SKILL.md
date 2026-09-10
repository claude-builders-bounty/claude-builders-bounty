# SKILL: generate-changelog

A Claude Code skill that generates a structured `CHANGELOG.md` from git commit history.

## Trigger

`/generate-changelog` — when a user asks to generate, create, or update a changelog.

## What It Does

1. Analyzes git commit history using conventional commit format
2. Categorizes commits into: Added, Fixed, Changed, Removed
3. Outputs a properly formatted `CHANGELOG.md` following Keep a Changelog conventions

## How to Use

```bash
# Generate changelog for the current repository
bash changelog.sh

# Generate with custom options
bash changelog.sh --repo /path/to/project --output CHANGES.md

# Generate changelog between two tags
bash changelog.sh --from v1.0.0 --to v2.0.0

# Include all commits (no tag filter)
bash changelog.sh --all --version "2.0.0"
```

## Conventional Commits

The script understands [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix     | Changelog Section |
|------------|-------------------|
| `feat:`    | Added             |
| `fix:`     | Fixed             |
| `revert:`  | Removed           |
| `docs:`    | Changed           |
| `style:`   | Changed           |
| `refactor:`| Changed           |
| `perf:`    | Changed           |
| `test:`    | Changed           |
| `build:`   | Changed           |
| `ci:`      | Changed           |
| `chore:`   | Changed           |

Non-conventional commits default to "Changed".

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-09-10

### Added
- New authentication system (a1b2c3d, Author Name, 2026-09-10)

### Fixed
- Login bug on mobile devices (e4f5g6h, Author Name, 2026-09-09)

### Changed
- Updated dependencies (i7j8k9l, Author Name, 2026-09-08)

---
*Generated on 2026-09-10 by generate-changelog v1.0.0*
*Total commits: 3 (Added: 1, Fixed: 1, Changed: 1, Removed: 0)*
```

## Options

- `--repo PATH` — Path to git repository (default: current directory)
- `--output FILE` — Output file (default: CHANGELOG.md)
- `--from TAG` — Start from this tag
- `--to REF` — End at this ref (default: HEAD)
- `--all` — Include all commits
- `--version VER` — Version header
- `--verbose` — Detailed output

## Requirements

- `bash` 4.0+
- `git`
- Standard Unix utilities (date, basename)
