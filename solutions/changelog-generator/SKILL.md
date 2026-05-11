---
name: generate-changelog
description: >
  Generate a structured CHANGELOG.md from git history.
  Run `/generate-changelog` to auto-categorize commits since
  the last git tag into Added / Fixed / Changed / Removed /
  Deprecated / Security / Documentation sections.
  Follows Keep a Changelog and Conventional Commits conventions.
---

# Generate Changelog

Automatically generates a `CHANGELOG.md` from the project's git history, using Conventional Commits parsing to categorize changes.

## Usage

Run the command in the project root (must be a git repository):

```
/generate-changelog
```

Or run the standalone script:

```bash
bash changelog.sh
```

### Options

| Argument | Description |
|----------|-------------|
| `--since v1.0` | Start from a specific tag |
| `--full` | Include the entire git history |
| `--stdout` | Print to terminal instead of writing to file |

## What it does

1. Detects the most recent git tag (or uses `--since`/`--full`)
2. Fetches all commits since that tag (excluding merges and version bumps)
3. Parses each commit message using Conventional Commits rules:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `refactor:`, `perf:`, `style:`, `build:`, `ci:` → **Changed**
   - `deprecate:` → **Deprecated**
   - `security:` → **Security**
   - `docs:` → **Documentation**
   - Keyword fallback for non-conventional messages
4. Outputs a properly formatted `CHANGELOG.md` with commit links

## Example output

```markdown
# Changelog

> Auto-generated from git history.

## [Unreleased] (since v1.2.0) - 2026-05-11

### Added
- User authentication via OAuth2 provider ([abc1234])
- Dark mode toggle in settings ([def5678])

### Fixed
- Payment processing timeout on checkout ([ghi9012])
- Memory leak in WebSocket connections ([jkl3456])
```

## Notes

- Requires `git` and `bash 4+`
- Zero external dependencies (no npm, pip, or other package managers needed)
- The script safely skips merge commits and version-bump commits
