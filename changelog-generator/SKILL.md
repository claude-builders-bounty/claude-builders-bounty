# CHANGELOG Generator Skill

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

```
/generate-changelog [--version VERSION] [--from-tag TAG] [--append]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--version, -v` | Version number for this release | `Unreleased` |
| `--from-tag, -t` | Start from this tag | Last git tag |
| `--output, -o` | Output file path | `CHANGELOG.md` |
| `--append, -a` | Append to existing changelog | `false` |

## Examples

```bash
# Generate changelog from last tag
/generate-changelog

# Generate for a specific version
/generate-changelog --version 1.2.0

# Generate from a specific tag
/generate-changelog --from-tag v1.0.0 --version 1.1.0

# Append to existing changelog
/generate-changelog --version 2.0.0 --append
```

## Categories

Commits are automatically categorized based on conventional commit prefixes:

| Prefix | Category |
|--------|----------|
| `feat:`, `add:` | Added |
| `fix:`, `bugfix:` | Fixed |
| `refactor:`, `update:`, `improve:` | Changed |
| `remove:`, `delete:` | Removed |
| `docs:` | Documentation |
| `test:` | Tests |
| `chore:`, `build:`, `ci:` | Maintenance |

## Output Format

```markdown
# Changelog

## [1.2.0] - 2026-03-27

### Added
- New feature for user authentication (#123)
- Support for dark mode

### Fixed
- Bug in login flow (#120)
- Memory leak in parser

### Changed
- Improved API response time

### Removed
- Deprecated legacy API endpoints
```

## Requirements

- Python 3.8+
- Git repository with commit history
- Optional: Git tags for version tracking

## Installation

```bash
# Copy to your project
cp generate_changelog.py /path/to/project/scripts/

# Make executable
chmod +x /path/to/project/scripts/generate_changelog.py

# Run
python scripts/generate_changelog.py
```

## Notes

- Automatically detects the last git tag
- Works with conventional commits format
- Supports both English and Chinese commit messages
- Preserves issue/PR references as links