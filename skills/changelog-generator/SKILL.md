# Changelog Generator

Generate a structured `CHANGELOG.md` from git history automatically.

## Usage

When the user says `/generate-changelog`, run the changelog generator script:

```bash
bash {{SKILL_DIR}}/changelog.sh
```

This will:
1. Detect the last git tag (or use all commits if no tags exist)
2. Collect all commits since that tag
3. Auto-categorize each commit based on its prefix (conventional commits style)
4. Output a formatted `CHANGELOG.md` in the current directory

## Categorization Rules

Commits are categorized by their prefix keyword (case-insensitive):

| Category | Prefixes |
|----------|----------|
| **Added** | `feat`, `add`, `new`, `implement`, `introduce`, `create`, `support` |
| **Fixed** | `fix`, `bugfix`, `patch`, `resolve`, `repair`, `correct`, `hotfix` |
| **Changed** | `refactor`, `update`, `change`, `modify`, `improve`, `enhance`, `perf`, `style`, `rename`, `move`, `migrate`, `adjust`, `optimize`, `upgrade`, `bump`, `ci`, `build`, `chore`, `docs`, `test` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate`, `clean`, `strip`, `uninstall` |

Commits that don't match any prefix are listed under **Other**.

Conventional commit scopes are supported — e.g., `feat(auth): add login` is correctly categorized as **Added**.

## Custom Output Path

To write the changelog to a custom file:

```bash
bash {{SKILL_DIR}}/changelog.sh path/to/CHANGELOG.md
```

## Output Format

The generated changelog follows the [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [Unreleased]

### Added
- feat: new feature (`abc1234`)

### Fixed
- fix: bug fix (`def5678`)

### Changed
- refactor: code improvement (`ghi9012`)

### Removed
- remove: deprecated code (`jkl3456`)
```

## Requirements

- Git repository with at least one commit
- Bash 4.0+
