# Generate Changelog

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from a project's git history using conventional commit parsing.

## Usage

### As a Claude Code Command
```
/generate-changelog
```

### As a Standalone Script
```bash
bash generate-changelog.sh [output_file] [since_tag]
```

**Arguments:**
- `output_file` — Path to the output file (default: `CHANGELOG.md`)
- `since_tag` — Git tag to start from (default: last tag, or all commits)

## Examples

```bash
# Generate CHANGELOG.md from the last tag
bash generate-changelog.sh

# Generate to a custom file
bash generate-changelog.sh docs/CHANGELOG.md

# Generate since a specific tag
bash generate-changelog.sh CHANGELOG.md v1.0.0

# Generate from all commits (if no tags exist)
bash generate-changelog.sh
```

## Features

- **Conventional Commit Parsing**: Automatically categorizes commits based on their type prefix (`feat:`, `fix:`, `refactor:`, `perf:`, `docs:`, `style:`, `chore:`, `ci:`, `test:`)
- **Keep a Changelog Format**: Output follows the [Keep a Changelog](https://keepachangelog.com/) standard
- **Commit Links**: Each entry includes a clickable link to the commit
- **Smart Tag Detection**: Automatically finds the latest git tag if none specified
- **Summary Statistics**: Shows counts of each change category

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased] - 2024-01-15

### Added
- New user authentication system ([abc1234](../../commit/abc1234))
- Email verification flow ([def5678](../../commit/def5678))

### Fixed
- Login redirect bug ([ghi9012](../../commit/ghi9012))
- Password validation errors ([jkl3456](../../commit/jkl3456))

### Changed
- Updated dependencies ([mno7890](../../commit/mno7890))
- Improved error messages ([pqr1234](../../commit/pqr1234))
```

## Commit Type Mapping

| Commit Prefix | Changelog Section |
|---------------|-------------------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:` | Changed |
| `perf:` | Changed |
| `docs:` | Changed |
| `style:` | Changed |
| `chore:` | Changed |
| `ci:` | Changed |
| `test:` | Changed |
| `remove:` / `delete:` | Removed |

## Requirements

- Git repository with commits
- Bash shell
- No external dependencies

## Setup

1. Copy `generate-changelog.sh` to your project root
2. Make it executable: `chmod +x generate-changelog.sh`
3. Run: `bash generate-changelog.sh`

## Integration with CI/CD

Add to your release workflow:

```yaml
# GitHub Actions example
- name: Generate Changelog
  run: bash generate-changelog.sh

- name: Commit Changelog
  run: |
    git config user.name "github-actions"
    git config user.email "github-actions@github.com"
    git add CHANGELOG.md
    git commit -m "docs: update changelog [skip ci]" || true
    git push
```

## License

MIT
