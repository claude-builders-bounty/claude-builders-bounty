# CHANGELOG Generator

Generate structured CHANGELOG.md from git history with auto-categorization of commits.

## Quick Setup (3 Steps)

### Step 1: Download
```bash
git clone https://github.com/BetsyMalthus/changelog-generator.git
cd changelog-generator
```

### Step 2: Make Executable
```bash
chmod +x changelog.sh scripts/generate_changelog.py
```

### Step 3: Generate CHANGELOG
```bash
# For current repository
./changelog.sh

# For any git repository
./changelog.sh /path/to/your/repo
```

## Usage Examples

### Basic Usage
```bash
# Generate CHANGELOG for current directory
./changelog.sh

# Generate for specific repository
./changelog.sh ~/projects/my-app

# Generate since specific tag
./changelog.sh --since-tag v1.0.0

# Output to different file
./changelog.sh --output RELEASE_NOTES.md

# Different format (json/text)
./changelog.sh --format json
```

### Python Script Direct Usage
```bash
# Using Python script directly
python scripts/generate_changelog.py /path/to/repo

# With all options
python scripts/generate_changelog.py \
  --since-tag v1.0.0 \
  --output CUSTOM_CHANGELOG.md \
  --format markdown
```

## Output Format

The generated CHANGELOG.md follows the Keep a Changelog format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New feature implementation (abc1234)

### Fixed
- Bug fix for login issue (def5678)

### Changed
- Updated dependencies (ghi9012)

### Removed
- Deprecated API endpoints (jkl3456)
```

## How It Works

1. **Fetches commits** since the last git tag (or all commits with `--all`)
2. **Categorizes commits** based on commit message patterns:
   - **Added**: feat, add, new, implement, create
   - **Fixed**: fix, bug, patch, resolve, correct  
   - **Changed**: change, update, modify, refactor, improve
   - **Removed**: remove, delete, deprecate, drop
3. **Generates formatted output** in Markdown, JSON, or plain text

## Testing

Test the generator on this repository:

```bash
# Generate CHANGELOG for this project
./changelog.sh

# View the result
cat CHANGELOG.md
```

## Requirements

- Python 3.6+
- Git installed and in PATH
- Bash shell (for changelog.sh wrapper)

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch  
3. Make your changes
4. Submit a pull request

## Sample Output

Here's an example of generated output:

```
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- User authentication system (a1b2c3d)
- API rate limiting (d4e5f6g)

### Fixed
- Memory leak in image processing (h7i8j9k)
- Timezone handling bug (l1m2n3o)

### Changed
- Updated to React 18 (p4q5r6s)
- Improved error messages (t7u8v9w)

## [1.0.0] - 2024-01-01

*Initial release*
```