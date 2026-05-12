# Generate Changelog Skill

Generates a structured CHANGELOG.md from git history, organized by type.

## Usage

```bash
# In your project directory
bash generate-changelog.sh

# Or specify repo and since tag
bash generate-changelog.sh --repo /path/to/project --since v1.0.0
```

## Output Format

```
# Changelog

## [Unreleased] - 2026-05-12

### Added
- New feature description (abc1234)

### Fixed
- Bug fix description (def5678)

### Changed
- Refactored module description (ghi9012)

### Removed
- Deprecated API removal (jkl3456)
```

## Sample Output

$SAMPLE_CHANGELOG

## Categorization Rules

| Commit Prefix | Category |
|--------------|----------|
| `feat:`, `feature:`, `add:`, `implement:`, `introduce:` | Added |
| `fix:`, `bugfix:`, `hotfix:`, `patch:`, `resolve:` | Fixed |
| `refactor:`, `improve:`, `update:`, `upgrade:`, `rework:` | Changed |
| `remove:`, `delete:`, `deprecate:`, `drop:` | Removed |
| `chore:`, `docs:`, `style:`, `test:`, `build:`, `ci:`, `perf:` | Other |

## Requirements

- `git` (with tags for proper version detection)
- `bash`
