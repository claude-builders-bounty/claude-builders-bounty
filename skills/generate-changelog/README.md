# generate-changelog

A Claude Code skill (`SKILL.md`) and standalone Bash script (`changelog.sh`) that build a Keep-a-Changelog formatted `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `SKILL.md` into `.claude/skills/generate-changelog/SKILL.md` and `changelog.sh` into `scripts/changelog.sh`.
2. Mark the script executable:
   ```bash
   chmod +x scripts/changelog.sh
   ```
3. Run `/generate-changelog` inside Claude Code or invoke the script directly:
   ```bash
   bash scripts/changelog.sh CHANGELOG.md v1.4.0
   ```

## Behavior

- Reads `git describe --tags --abbrev=0` and queries `<last-tag>..HEAD`. Falls back to `HEAD` when a repository has no tags.
- Skips `Merge ...` and `chore(release):` commits.
- Groups commits into `Added`, `Fixed`, `Changed`, and `Removed` using Conventional Commits prefixes (`feat`, `fix`, scoped/breaking variants) and plain imperative verbs.

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.4.0] - 2026-11-26

_Commits since `v1.3.0`_

### Added
- feat(api): add cursor pagination to issues endpoint (`a14f9c2`)
- feat(cli): accept optional version label argument (`8d21e0b`)

### Fixed
- fix(parser): classify scoped breaking-change headers (`4c9b71e`)
- fix(tags): fall back to HEAD when repository has no tags (`2f03a8d`)

### Changed
- refactor(output): align headings with Keep a Changelog 1.1 (`7e62c11`)

### Removed
- remove deprecated v1 markdown template (`19ab402`)
```
