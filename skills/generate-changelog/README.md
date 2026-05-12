# Generate Changelog Skill

A Claude Code skill that generates a structured `CHANGELOG.md` from git history, following the [Keep a Changelog](https://keepachangelog.com/) format.

## Features

- **Conventional Commits support** — Automatically categorizes `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `deprecate:`, `remove:`, `security:`, and more
- **Merge commit handling** — Skips merge commits (`--no-merges`) for clean output
- **Tag-aware** — Uses the last git tag as the starting point; generates from first commit if no tags exist
- **Incremental updates** — Prepends new entries to existing `CHANGELOG.md` without overwriting
- **PR references** — Preserves `#123` PR references from commit subjects

## Usage

### As a Claude Code Skill

Place the `skills/generate-changelog/` directory in your project's `.claude/skills/` or `.devin/skills/` directory. Then invoke with:

```
/generate-changelog
```

Or simply ask Claude to "generate a changelog" or "update the changelog."

### As a Standalone Script

```bash
# Generate changelog for current repo (from last tag)
bash generate-changelog.sh

# Generate for a specific repo path
bash generate-changelog.sh /path/to/repo

# Generate from a specific tag/ref
bash generate-changelog.sh . v1.2.0
```

## Output Format

```markdown
# Changelog

## [Unreleased]

### Added
- feat: add user authentication (#123) by @author

### Fixed
- fix: resolve login redirect loop (#122) by @author

### Changed
- refactor: simplify config loading (#121) by @author

### Deprecated
- deprecate: old-style config format (#119) by @author

### Removed
- remove: legacy API v1 endpoints (#120) by @author

### Security
- security: patch dependency vulnerability (#118) by @author
```

## Commit Categorization

| Prefix | Category |
|--------|----------|
| `feat:`, `feature:`, `add:`, `Added` | Added |
| `fix:`, `bugfix:`, `patch:`, `Fixed` | Fixed |
| `refactor:`, `change:`, `update:`, `chore:`, `docs:`, `test:`, `ci:`, `build:`, `perf:` | Changed |
| `deprecate:`, `Deprecated` | Deprecated |
| `remove:`, `delete:`, `Removed` | Removed |
| `security:` | Security |

Commits without a recognized prefix are categorized as **Changed**.

## Files

- `SKILL.md` — Skill definition for Claude Code
- `generate-changelog.sh` — Standalone bash script (no dependencies beyond git and grep)
