# CHANGELOG Generator

Automatically generates a structured `CHANGELOG.md` from git history.

## Quick Start (3 Steps)

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/lisaxiao299-maker/claude-builders-bounty/main/changelog-generator/generate_changelog.py

# 2. Run
python3 generate_changelog.py

# 3. Check output
cat CHANGELOG.md
```

## Usage

### Python Script

```bash
# Generate from last tag
python3 generate_changelog.py

# Generate for specific version
python3 generate_changelog.py --version 1.2.0

# Generate from specific tag
python3 generate_changelog.py --from-tag v1.0.0 --version 1.1.0

# Append to existing changelog
python3 generate_changelog.py --version 2.0.0 --append
```

### Bash Wrapper

```bash
chmod +x changelog.sh
./changelog.sh 1.2.0
```

### Claude Code Skill

```
/generate-changelog --version 1.2.0
```

## Features

- ✅ Auto-detects last git tag
- ✅ Auto-categorizes: Added / Fixed / Changed / Removed
- ✅ Supports conventional commits (`feat:`, `fix:`, etc.)
- ✅ Extracts issue/PR references
- ✅ Works with English and Chinese commits
- ✅ Standard KEEP-A-CHANGELOG format

## Categories

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `新增:` | Added |
| `fix:`, `bug:`, `修复:` | Fixed |
| `refactor:`, `update:`, `优化:` | Changed |
| `remove:`, `delete:`, `删除:` | Removed |

## Sample Output

```markdown
# Changelog

## [1.2.0] - 2026-03-27

### Added
- New user authentication system (#123)
- Dark mode support
- API rate limiting

### Fixed
- Memory leak in image processing (#120)
- Login redirect bug

### Changed
- Improved database query performance
- Updated dependencies

### Removed
- Deprecated legacy API endpoints
```

## Requirements

- Python 3.8+
- Git

## License

MIT