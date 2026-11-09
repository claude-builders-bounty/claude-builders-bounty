# generate-changelog skill

Generate a structured `CHANGELOG.md` from a project's git history.

## Usage

```
/generate-changelog
```

Or run the bash script directly:

```bash
bash changelog.sh
```

## What it does

1. Finds the latest git tag (or the beginning of history if none exists)
2. Lists all commits since that tag
3. Categorizes each commit using conventional commit prefixes:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `docs:` → **Changed**
   - `style:` → **Changed**
   - `refactor:` → **Changed**
   - `perf:` → **Changed**
   *`test:`* → **Fixed**
   - `build:` / `ci:` / `chore:` → **Changed**
   - anything else → **Changed**
4. Outputs a properly formatted `CHANGELOG.md` with sections:
   - `## Added` — new features
   - `## Fixed` — bug fixes
   - `## Changed` — modifications
   - `## Removed` — removals
5. Includes a sample output tested on a real repository

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude Code skill definition |
| `changelog.sh` | Standalone bash script |

## Example output

```markdown
# Changelog

## [Unreleased]

### Added
- Add user authentication flow (@alice)
- Add dark mode toggle (@bob)

### Fixed
- Fix login redirect on expired session (@alice)
- Fix mobile menu overlap (@charlie)

### Changed
- Update dependency versions (@bob)
- Improve error message clarity (@diana)

### Removed
- Remove deprecated v1 API endpoints (@alice)
```

## Requirements

- Git 2.0+
- Bash 4.0+ (for `changelog.sh`)
- No external dependencies
