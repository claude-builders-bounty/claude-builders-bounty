# Changelog Generator

A Claude Code skill and standalone script that auto-generates structured CHANGELOG.md from git history.

## Setup (3 steps)

1. Save `changelog.sh` in your project root
2. `chmod +x changelog.sh`
3. Run `./changelog.sh` — done.

## Usage

```bash
# Generate CHANGELOG since last git tag
bash changelog.sh

# Specify a starting tag
bash changelog.sh v1.0.0

# Custom output path
bash changelog.sh v1.0.0 docs/CHANGELOG.md
```

## Claude Code Integration

Add this to your project's `CLAUDE.md`:

```markdown
## Changelog
- Run `bash changelog.sh` to generate CHANGELOG.md from commits since last tag
- Categorizes into: Added, Fixed, Changed, Removed
```

Or use the `/generate-changelog` command by adding `SKILL.md` to your project.

## Output Format

```markdown
## v1.2.0 (2026-07-21)

### Added
- Dark mode support
- API rate limiting

### Fixed
- Login timeout on slow connections
- Dashboard chart rendering bug

### Changed
- Upgraded dependencies to latest

### Removed
- Deprecated v1 API endpoints
```

## Categorization Logic

The script auto-categorizes commits by prefix keywords:

| Prefix | Category |
|--------|----------|
| `add`, `feat`, `new`, `create`, `implement` | Added |
| `fix`, `bug`, `resolve`, `patch`, `repair` | Fixed |
| `change`, `update`, `refactor`, `improve`, `upgrade` | Changed |
| `remove`, `delete`, `drop`, `deprecate` | Removed |

Supports both conventional commit format (`feat: message`) and plain commit messages.
