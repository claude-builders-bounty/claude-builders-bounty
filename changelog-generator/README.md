# Changelog Generator

A tool to automatically generate structured CHANGELOG.md files from git commit history.

## Quick Start (3 Steps)

### 1. Download
```bash
git clone https://github.com/yourusername/changelog-generator.git
cd changelog-generator
```

### 2. Install
```bash
# Make script executable
chmod +x changelog.sh

# (Optional) Add to PATH for global access
sudo cp changelog.sh /usr/local/bin/changelog
```

### 3. Generate
```bash
# Navigate to your git repository
cd /path/to/your/repo

# Generate changelog
changelog.sh --output CHANGELOG.md
```

## Features

- **Automatic categorization**: Commits sorted into Added/Fixed/Changed/Removed
- **Tag-aware**: Automatically detects versions from git tags
- **Flexible output**: Customize filename, start tag, and format
- **Lightweight**: Single Python script with no external dependencies (except git)

## Usage

### Basic Usage
```bash
# Generate changelog from latest tag
./changelog.sh

# Specify output file
./changelog.sh --output docs/CHANGELOG.md

# Generate from specific version
./changelog.sh --since v1.0.0

# Include all commits (ignore tags)
./changelog.sh --all
```

### As a Command
```bash
# If installed globally
changelog --output CHANGELOG.md
```

### Python Script Directly
```bash
python3 changelog_generator.py --output CHANGELOG.md
```

## Output Example

```markdown
# Changelog

## v1.2.0
*Generated on 2026-04-02*

### Added
- Implement user authentication system (abc123, 2026-04-01)
- Add password reset functionality (def456, 2026-03-31)

### Fixed
- Fix login page CSS issue (ghi789, 2026-03-30)
- Resolve database connection timeout (jkl012, 2026-03-29)

### Changed
- Update dependencies to latest versions (mno345, 2026-03-28)
- Refactor API response format (pqr678, 2026-03-27)

### Summary
- Total commits: 6
- Added: 2
- Fixed: 2
- Changed: 2
```

## Categorization Rules

The tool automatically categorizes commits based on keywords:

| Category | Keywords |
|----------|----------|
| **Added** | add, create, new, implement, feat, feature |
| **Fixed** | fix, bug, issue, error, resolve, patch, hotfix |
| **Changed** | change, update, modify, refactor, improve, enhance, optimize |
| **Removed** | remove, delete, deprecate, drop |

## Requirements

- **Git** (must be installed and in PATH)
- **Python 3.6+** (for Python version)
- **Bash** (for shell script version)

## Testing

Test the generator on this repository:

```bash
# Generate changelog for this project
./changelog.sh --output TEST_CHANGELOG.md

# View the result
cat TEST_CHANGELOG.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details.