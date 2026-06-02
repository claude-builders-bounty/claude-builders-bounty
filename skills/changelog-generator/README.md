# Changelog Generator

A bash script that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Features

- ✅ Fetches commits since the last git tag (or any specified tag)
- ✅ Auto-categorizes commits into: `Added`, `Fixed`, `Changed`, `Removed`, `Documentation`, `Tests`, `Style`, `Chore`, `Other`
- ✅ Outputs a properly formatted `CHANGELOG.md` with clear sections
- ✅ Color-coded output for better visibility
- ✅ Handles edge cases (no tags, empty repository, etc.)
- ✅ Customizable output file and tag selection

## Quick Start (3 Steps)

### 1. Download the script

```bash
curl -O https://raw.githubusercontent.com/yourusername/changelog-generator/main/changelog-generator.sh
chmod +x changelog-generator.sh
```

### 2. Run the script

```bash
./changelog-generator.sh
```

### 3. Check the output

```bash
cat CHANGELOG.md
```

## Usage

### Basic Usage
```bash
# Generate CHANGELOG.md from latest tag
./changelog-generator.sh

# Generate with custom output file
./changelog-generator.sh docs/HISTORY.md

# Generate since specific tag
./changelog-generator.sh CHANGELOG.md v1.0.0
```

### Advanced Options
```bash
# Show help
./changelog-generator.sh --help

# Generate from all commits (no tag)
./changelog-generator.sh CHANGELOG.md ""
```

## Output Format

The generated `CHANGELOG.md` includes:

1. **Header** - Project title and description
2. **[Unreleased]** section - All changes since last tag
3. **Categorized commits** - Organized by type (Added, Fixed, Changed, etc.)
4. **Previous Releases** section - Reference to older changes
5. **Footer** - Generation timestamp and tool info

Example output:
```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **feat: Add user authentication** (abc1234) - John Doe, 2024-01-15
- **feat: Implement file upload** (def5678) - Jane Smith, 2024-01-14

### Fixed
- **fix: Resolve memory leak** (ghi9012) - Bob Johnson, 2024-01-13

### Changed
- **refactor: Improve API performance** (jkl3456) - Alice Brown, 2024-01-12
```

## Categorization Logic

The script uses keyword matching to categorize commits:

| Category | Keywords |
|----------|----------|
| Added | add, feat, new, implement, create |
| Fixed | fix, bug, patch, resolve, correct |
| Changed | change, update, modif, refactor, improve, optimize |
| Removed | remove, delete, drop, deprecate |
| Documentation | docs, documentation, readme |
| Tests | test, testing |
| Style | style, format, lint |
| Chore | chore, ci, build, deps |
| Other | (everything else) |

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Generate Changelog
on:
  push:
    tags:
      - 'v*'
jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Generate Changelog
        run: |
          curl -sSL https://raw.githubusercontent.com/yourusername/changelog-generator/main/changelog-generator.sh -o changelog.sh
          chmod +x changelog.sh
          ./changelog.sh CHANGELOG.md
      - name: Commit CHANGELOG.md
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add CHANGELOG.md
          git commit -m "docs: Update changelog for ${{ github.ref_name }}" || echo "No changes to commit"
          git push
```

## Testing

Test the script on this repository:

```bash
# Clone a test repository
git clone https://github.com/octocat/Spoon-Knife.git
cd Spoon-Knife

# Run the script
../changelog-generator.sh TEST_CHANGELOG.md

# View the result
cat TEST_CHANGELOG.md
```

## Requirements

- Bash 4.0 or higher
- Git 2.0 or higher
- Standard Unix tools (sed, awk, grep, date, etc.)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

- Report issues: [GitHub Issues](https://github.com/yourusername/changelog-generator/issues)
- Ask questions: [GitHub Discussions](https://github.com/yourusername/changelog-generator/discussions)

---

*This script was created for the [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) bounty program.*