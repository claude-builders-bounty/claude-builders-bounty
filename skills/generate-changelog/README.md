# Generate Changelog

A simple tool to automatically generate `CHANGELOG.md` from git history.

## Quick Start (3 steps)

```bash
# 1. Copy the script to your project
curl -O https://raw.githubusercontent.com/HuiNeng6/claude-builders-bounty/main/skills/generate-changelog/scripts/generate-changelog.sh

# 2. Make it executable
chmod +x generate-changelog.sh

# 3. Run it
./generate-changelog.sh
```

## Output

The script generates a `CHANGELOG.md` file with:

- **Unreleased** section with all changes since the last tag
- **Version sections** for each git tag
- Auto-categorized entries:
  - `feat:`, `add:` → Added
  - `fix:`, `bugfix:` → Fixed
  - `refactor:`, `perf:`, `chore:` → Changed
  - `remove:`, `deprecate:` → Removed

## Example Output

```markdown
# Changelog

## [Unreleased]

### Added
- New feature for user authentication
- Support for dark mode

### Fixed
- Memory leak in image processing

### Changed
- Improved API response times

## [1.0.0] - 2026-03-27

### Added
- Initial release
```

## Conventional Commits

For best results, use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Category |
|--------|----------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `perf:`, `chore:` | Changed |
| `remove:`, `deprecate:` | Removed |
| `docs:` | Documentation |

## Requirements

- Git
- Bash 4.0+

## License

MIT