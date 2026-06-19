# Generate Changelog — Claude Code Skill

Automatically generate a structured `CHANGELOG.md` from a project's git history.

## Quick Start (3 steps)

```bash
# 1. Copy the script to your project
cp changelog.sh /path/to/your/project/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it
./changelog.sh > CHANGELOG.md
```

## Usage

```bash
# Generate from last git tag to HEAD (most common)
./changelog.sh

# Generate for a specific tag range
./changelog.sh v1.0.0..v2.0.0

# Generate full history
./changelog.sh --all
```

## Auto-Categorization

The script categorizes commits by prefix:

| Category | Commit Prefixes |
|----------|----------------|
| **Added** | `add`, `feat`, `create`, `introduce`, `implement`, `support`, `new` |
| **Fixed** | `fix`, `bug`, `patch`, `resolve`, `repair`, `correct`, `hotfix` |
| **Changed** | `change`, `update`, `modify`, `refactor`, `rename`, `move`, `upgrade`, `migrate`, `bump`, `improve` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate`, `strip`, `eliminate` |

Commits that don't match any prefix default to **Changed**.

## Sample Output

```markdown
# Changelog

## 2026-06-19 (v1.0.0..HEAD)

### Added
- feat: add user authentication endpoint
- add pagination to list API
- implement rate limiting middleware

### Fixed
- fix: resolve null pointer in user lookup
- hotfix: patch SQL injection vulnerability

### Changed
- update: upgrade dependencies to latest versions
- refactor: simplify config loading logic

### Removed
- remove: deprecated v1 API endpoints
- drop: legacy MySQL adapter
```

## Also usable as Claude Code Skill

Copy the `SKILL.md` file to your project and use `/generate-changelog` in Claude Code.
