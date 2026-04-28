# Generate Changelog

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

In Claude Code, type:

```
/generate-changelog
```

Or run directly:

```bash
bash skills/generate-changelog/changelog.sh
```

## What it does

1. Detects the last git tag in the repository
2. Fetches all commits since that tag
3. Auto-categorizes commits into: **Added**, **Fixed**, **Changed**, **Removed**
4. Outputs a properly formatted `CHANGELOG.md` entry

## Categorization Rules

Commits are categorized by their prefix:

| Prefix            | Category |
|-------------------|----------|
| `feat:`, `add:`   | Added    |
| `fix:`, `bugfix:` | Fixed    |
| `refactor:`, `change:`, `update:` | Changed  |
| `remove:`, `delete:`, `deprecate:` | Removed  |

Commits without a recognized prefix are placed in **Changed**.

## Sample Output

```markdown
# Changelog

## [Unreleased] - 2026-04-28

### Added
- feat: add user authentication endpoint
- feat: implement dark mode toggle

### Fixed
- fix: resolve null pointer in payment flow
- bugfix: correct timezone offset calculation

### Changed
- refactor: simplify database connection pooling
- update: bump dependencies to latest versions

### Removed
- remove: deprecated legacy API v1 endpoints
```

## Setup

1. Clone this repository
2. Run `bash skills/generate-changelog/changelog.sh` from the project root
3. The changelog entry will be prepended to `CHANGELOG.md` (created if missing)

That's it — no dependencies beyond `git` and standard Unix tools.
