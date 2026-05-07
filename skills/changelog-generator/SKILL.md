---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history since the last tag. Categorizes commits into Added / Changed / Fixed / Removed using conventional-commit prefixes (feat, fix, refactor, etc.) with keyword fallback. Triggers on requests like "generate changelog", "update CHANGELOG", "draft release notes", "what changed since last release".
version: v1.0
---

# Changelog Generator

Produces a Keep-A-Changelog-formatted `CHANGELOG.md` (or release-notes section) from a project's git history.

## When to use

- Cutting a release and need to summarize what changed
- Drafting release notes for a tagged version
- Adding a changelog to a project that doesn't have one yet

## Quick path

1. **Detect the range.** From the most recent annotated tag (or the project root if none) to `HEAD`.
2. **Run the generator.** Pick one:
   - Python: `python <skill_dir>/scripts/changelog.py [--since vX.Y.Z] [--out CHANGELOG.md]`
   - Bash: `bash <skill_dir>/scripts/changelog.sh [--since vX.Y.Z] [--out CHANGELOG.md]`
   - Slash command: `/generate-changelog`
3. **Review the output.** Every commit lands in one of four buckets; uncategorized commits go under `### Other`. Reorder, edit, or strip noise.
4. **Prepend to `CHANGELOG.md`** (don't overwrite — keep prior entries).

## Categorization rules

| Bucket    | Conventional-commit prefixes                | Keyword fallback (case-insensitive)    |
|-----------|----------------------------------------------|----------------------------------------|
| Added     | `feat`, `add`                                | `add`, `introduce`, `new`              |
| Changed   | `refactor`, `perf`, `style`, `chore`, `docs`, `build`, `ci` | `update`, `change`, `improve`, `bump`  |
| Fixed     | `fix`, `bugfix`, `patch`                     | `fix`, `repair`, `correct`, `resolve`  |
| Removed   | `revert`, `remove`                           | `remove`, `drop`, `delete`             |

Anything else lands in `### Other` so nothing is silently dropped.

## Output format

```
## [Unreleased] - 2026-05-06

### Added
- New feature description (commit_short_sha)

### Fixed
- Fix description (commit_short_sha)

...
```

If `--since vX.Y.Z` is given, the heading is `## [vX.Y.Z+1] - DATE` instead of `[Unreleased]`.

## Sample

See [samples/CHANGELOG.example.md](samples/CHANGELOG.example.md) for output generated against this very repository.

## Installation in another project

Drop the `skills/changelog-generator/` directory anywhere a Claude Code session will read it. The scripts are zero-dependency (Python stdlib + git).

## Acceptance-criteria mapping (issue #1)

| Criterion                                                       | Evidence                                          |
|------------------------------------------------------------------|---------------------------------------------------|
| Works via `/generate-changelog` or `bash changelog.sh`           | This `SKILL.md` (slash) + `scripts/changelog.sh`  |
| Fetches commits since the last git tag                           | `git describe --tags --abbrev=0` in both scripts  |
| Auto-categorizes into Added / Fixed / Changed / Removed          | Tables above + functions `categorize()` in scripts|
| Outputs a properly formatted `CHANGELOG.md`                      | Keep-A-Changelog spec                             |
| Tested on a real GitHub repo (sample output in PR)               | `samples/CHANGELOG.example.md`                    |
| README with setup instructions in 3 steps or fewer               | [README.md](README.md), 3 steps                   |
