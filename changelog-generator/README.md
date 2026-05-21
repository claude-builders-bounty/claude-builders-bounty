# Changelog Generator

A simple, zero-dependency tool that generates structured `CHANGELOG.md` files from git history.

## Quick Start

```bash
# 1. Copy to your project
cp changelog.sh /path/to/your/project/

# 2. Make executable
chmod +x changelog.sh

# 3. Generate
bash changelog.sh
```

## Features

- **Zero dependencies** — works with just `git` and `bash`
- **Auto-categorization** — sorts commits into Added/Fixed/Changed/Removed
- **Conventional Commits** — recognizes `feat:`, `fix:`, `refactor:`, etc.
- **Tag-aware** — generates changelog since the last git tag
- **Claude Code compatible** — includes a `SKILL.md` for use with `/generate-changelog`

## Options

```bash
bash changelog.sh                  # Default: writes to CHANGELOG.md
bash changelog.sh docs/CHANGES.md  # Custom output path
```

## Commit Prefix Mapping

| You write | It becomes |
|---|---|
| `feat:`, `add:`, `new:`, `create:` | Added |
| `fix:`, `bugfix:`, `patch:` | Fixed |
| `refactor:`, `update:`, `change:`, `docs:`, `chore:` | Changed |
| `remove:`, `delete:`, `deprecate:` | Removed |

## Example

```bash
$ git log --oneline
abc1234 feat: add user auth
def5678 fix: resolve login timeout
ghi9012 docs: update README
jkl3456 remove: delete old API

$ bash changelog.sh
✓ Changelog written to CHANGELOG.md
  Commits processed: 4
```

Output:

```markdown
# Changelog

## [Unreleased]

_Generated on 2026-05-21_

### Added
- feat: add user auth (`abc1234`) — Author (2026-05-21)

### Fixed
- fix: resolve login timeout (`def5678`) — Author (2026-05-21)

### Changed
- docs: update README (`ghi9012`) — Author (2026-05-21)

### Removed
- remove: delete old API (`jkl3456`) — Author (2026-05-21)
```

## License

MIT
