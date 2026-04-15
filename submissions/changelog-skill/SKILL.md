---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history
triggers:
  - "/generate-changelog"
  - "generate changelog"
  - "create changelog"
---

# Generate Structured CHANGELOG

Generate a well-organized `CHANGELOG.md` from the project's git commit history.

## Quick Start

```bash
bash changelog.sh
```

Or ask Claude: "Generate a changelog for this project"

## What It Does

1. Reads git log (all commits or since last tag)
2. Categorizes commits by type prefix
3. Groups by version/tag if tags exist
4. Generates structured `CHANGELOG.md`

## Commit Type Mapping

| Prefix | Section | Example |
|--------|---------|---------|
| `feat:` | **Added** | `feat: add user auth` |
| `fix:` | **Fixed** | `fix: resolve login crash` |
| `change:` / `refactor:` / `perf:` | **Changed** | `refactor: simplify API` |
| `remove:` / `delete:` | **Removed** | `remove: deprecated v1 endpoints` |
| `docs:` | **Documentation** | `docs: update API guide` |
| `test:` | **Tests** | `test: add auth unit tests` |
| `chore:` / `ci:` / `build:` | **Maintenance** | `ci: update GitHub Actions` |
| (no prefix) | **Other** | Plain commit messages |

## Steps for Claude

When the user asks to generate a changelog:

1. Run `git log --oneline --no-merges` to get commit history
2. Run `git tag -l --sort=-v:refname` to find version tags
3. Parse each commit into the type mapping above
4. If tags exist, group commits by tag ranges
5. Generate the CHANGELOG.md with this structure:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- feat: description (abc1234)

### Fixed
- fix: description (def5678)

## [v1.0.0] - 2026-01-15

### Added
- feat: initial release (aaa1111)
```

6. Write to `CHANGELOG.md` in project root
7. Show a summary of what was generated

## Customization

- Set `CHANGELOG_SINCE_TAG=v1.0.0` to only include commits since that tag
- Set `CHANGELOG_INCLUDE_MERGES=true` to include merge commits
- Set `CHANGELOG_GROUP_BY=month` to group by month instead of tags

## Output

A `CHANGELOG.md` file with:
- Reverse chronological order (newest first)
- Commits grouped by type (Added, Fixed, Changed, Removed)
- Version sections if git tags exist
- Commit short hashes for traceability
- Unreleased section for commits after latest tag
