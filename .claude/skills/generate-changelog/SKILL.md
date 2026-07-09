---
name: generate-changelog
description: Generate a structured Keep a Changelog CHANGELOG.md from git history since the last tag, auto-categorizing commits into Added, Fixed, Changed, and Removed.
argument-hint: "[output-file]"
allowed-tools: Bash(git *), Bash(bash changelog.sh*), Bash(bash generate-changelog.sh*), Bash(python generate_changelog.py*), Bash(python3 generate_changelog.py*), Read, Write, Edit, Glob, Grep
---

# Generate Changelog

Produce a properly formatted `CHANGELOG.md` from the current repository's git history.

## When to use

- User runs `/generate-changelog` or asks to generate/update a changelog
- User wants release notes from commits since the last tag
- Preparing a release and needs categorized change lists

## How to run

Prefer the project scripts (they implement the same rules):

```bash
# Option A — bash entrypoint (acceptance criterion)
bash changelog.sh

# Option B — wrapper
bash generate-changelog.sh

# Option C — Python
python generate_changelog.py
# or
python3 generate_changelog.py
```

Optional output path:

```bash
bash changelog.sh docs/CHANGELOG.sample.md
python generate_changelog.py docs/CHANGELOG.sample.md
```

If scripts are unavailable, follow **Manual algorithm** below and write the file with the Write tool.

## Algorithm

1. Confirm you are inside a git repository (`git rev-parse --show-toplevel`).
2. Resolve the last tag:
   ```bash
   git describe --tags --abbrev=0
   ```
   - If a tag exists → commit range is `TAG..HEAD`
   - If no tags → use the full history (`git log`)
3. List non-merge commits:
   ```bash
   git log TAG..HEAD --no-merges --pretty=format:'%h%x09%s'
   ```
4. Categorize each subject into exactly one of:
   - **Added** — `feat`, `feature`, `add`, or messages about new functionality
   - **Fixed** — `fix`, `bugfix`, `hotfix`, or bug/fix language
   - **Removed** — `remove`, `delete`, `deprecate`, or removal language
   - **Changed** — `refactor`, `style`, `perf`, `chore`, `docs`, `test`, `ci`, `build`, updates, or default bucket
5. Strip conventional-commit prefixes (`feat:`, `fix(scope):`, etc.) for bullet text.
6. Write Keep a Changelog markdown (see template).

## Conventional commit mapping

| Prefix / signal | Section |
|-----------------|---------|
| `feat`, `feature`, `add` | Added |
| `fix`, `bugfix`, `hotfix`, `patch` | Fixed |
| `remove`, `delete`, `deprecate` | Removed |
| `refactor`, `style`, `perf`, `chore`, `docs`, `test`, `ci`, `build`, `update` | Changed |
| unrecognized | Changed (default) |

## Output template

```markdown
# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - YYYY-MM-DD

_Commits since `vX.Y.Z`._

### Added

- Description (`abc1234`)

### Fixed

- Description (`def5678`)

### Changed

- Description (`ghi9012`)

### Removed

- Description (`jkl3456`)
```

Rules:

- Only emit sections that have at least one item
- Use short hashes in backticks after each bullet
- Header date is today (`YYYY-MM-DD`)
- Default output path: `CHANGELOG.md` in the repo root
- If `$ARGUMENTS` is a non-empty path, write there instead

## Arguments

- `$ARGUMENTS` — optional output file path (default `CHANGELOG.md`)

## After generation

1. Briefly report: last tag (or none), commit count, per-category counts
2. Show the path written
3. Offer to commit the changelog only if the user asks
