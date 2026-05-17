# Structured CHANGELOG Generator

Auto-generates a structured `CHANGELOG.md` from git history.

## Install (1 command)

```bash
curl -fsSL https://raw.githubusercontent.com/bgagosmohan/claude-builders-bounty/main/changelog.sh -o /usr/local/bin/changelog && chmod +x /usr/local/bin/changelog
```

## Usage

```bash
# Generate since last git tag
changelog

# Generate since specific tag
changelog --since v1.2.0

# Custom output path
changelog --output docs/CHANGELOG.md
```

## Output Format

```markdown
# Changelog
## 2026-05-17 — since v1.0.0

### Added
- feat: user profile page

### Fixed
- fix: login redirect loop

### Changed
- refactor: database connection pooling

### Removed
- remove: deprecated v1 API endpoints
```

## Auto-Categorization

| Prefix | Category |
|--------|----------|
| `add`, `feat`, `implement`, `introduce`, `create`, `new` | **Added** |
| `fix`, `patch`, `resolve`, `bug`, `hotfix`, `correct` | **Fixed** |
| `change`, `update`, `refactor`, `improve`, `enhance`, `tweak`, `modify` | **Changed** |
| `remove`, `delete`, `drop`, `deprecate`, `retire` | **Removed** |

Commits that don't match any prefix go to **Other**.
