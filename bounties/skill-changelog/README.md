# CHANGELOG Generator Skill

A Claude Code skill that generates a structured `CHANGELOG.md` from git history using the Keep a Changelog format.

## Installation

1. Copy `SKILL.md` into `.claude/skills/generate-changelog/SKILL.md`.
2. Open a git repository with Claude Code.
3. Run `/generate-changelog`.

## Usage

```
/generate-changelog
/generate-changelog since v2.1.0
/generate-changelog for the last 10 commits
```

## What It Does

1. Finds commits since the latest git tag, falling back to the last 20 commits when no tags exist.
2. Categorizes commits by type (`feat`, `fix`, `refactor`, `deps`, and related prefixes).
3. Groups user-facing changes into `Added`, `Changed`, `Fixed`, and `Removed`.
4. Outputs a clean Markdown changelog entry that can be inserted into `CHANGELOG.md`.

## Example Output

```markdown
## [Unreleased] - 2026-05-04

### Added
- User authentication with OAuth2 support (#142)
- Export dashboard data as CSV (#138)

### Fixed
- Memory leak in WebSocket connection handler (#145)
- Incorrect timezone handling in scheduling module (#139)

### Changed
- Upgraded database driver to v3.2.0 (#144)
- Improved error messages for API validation (#141)
```

## Skill Prompt

See `SKILL.md` for the full skill definition.
