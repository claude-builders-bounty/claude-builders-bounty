# CHANGELOG Generator

Automatically generates a structured `CHANGELOG.md` from git history.

## Usage

```bash
# Generate CHANGELOG.md in current repo
python3 changelog.py

# Specify output file
python3 changelog.py --output CHANGELOG.md

# Specify repo path
python3 changelog.py --repo /path/to/project
```

## Output Format

The generated changelog groups commits by category:

```
# Changelog

## [Unreleased]
### Added
- New feature description

### Fixed
- Bug fix description

## [v1.0.0]
### Added
- Initial release
```

## Requirements

- Python 3.8+
- Git repository with conventional commit messages

## Sample Output

See [CHANGELOG.md](./CHANGELOG.md) for a generated example.
