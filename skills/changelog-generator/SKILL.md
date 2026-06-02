# SKILL.md - Changelog Generator Skill

## Skill Metadata
- **Name**: changelog-generator
- **Description**: Automatically generates a structured CHANGELOG.md from git history
- **Version**: 1.0.0
- **Author**: baconag
- **Created**: 2026-06-02

## Commands

### `/generate-changelog`
Generates a structured CHANGELOG.md file from git commit history.

**Usage:**
```
/generate-changelog [output_file] [since_tag]
```

**Arguments:**
- `output_file` (optional): Path to output file (default: CHANGELOG.md)
- `since_tag` (optional): Git tag to start from (default: latest tag)

**Examples:**
```
/generate-changelog
/generate-changelog CHANGELOG.md
/generate-changelog CHANGELOG.md v1.0.0
/generate-changelog docs/HISTORY.md v2.0.0
```

**Features:**
- ✅ Fetches commits since the last git tag (or any specified tag)
- ✅ Auto-categorizes commits into: Added, Fixed, Changed, Removed, Documentation, Tests, Style, Chore, Other
- ✅ Outputs a properly formatted CHANGELOG.md with clear sections
- ✅ Color-coded output for better visibility
- ✅ Handles edge cases (no tags, empty repository, etc.)

## Installation

### Option 1: Direct download
```bash
curl -O https://raw.githubusercontent.com/baconag/changelog-generator/main/changelog-generator.sh
chmod +x changelog-generator.sh
```

### Option 2: Clone repository
```bash
git clone https://github.com/baconag/changelog-generator.git
cd changelog-generator
chmod +x changelog-generator.sh
```

## Integration with Claude Code

Add this to your Claude Code configuration:

```yaml
skills:
  changelog-generator:
    type: shell
    command: ./changelog-generator.sh
    description: "Generate structured CHANGELOG.md from git history"
    arguments:
      - name: output_file
        optional: true
        default: CHANGELOG.md
        description: "Output file path"
      - name: since_tag
        optional: true
        default: ""
        description: "Git tag to start from"
```

## Sample Output

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

### Documentation
- **docs: Update README** (mno7890) - Charlie Wilson, 2024-01-11
```

## Categorization Logic

The script uses intelligent keyword matching:

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

## Testing

Test the script on any git repository:

```bash
# Clone a test repository
git clone https://github.com/octocat/Spoon-Knife.git
cd Spoon-Knife

# Run the script
../changelog-generator.sh TEST_CHANGELOG.md

# View the result
cat TEST_CHANGELOG.md
```

## CI/CD Integration

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
          curl -sSL https://raw.githubusercontent.com/baconag/changelog-generator/main/changelog-generator.sh -o changelog.sh
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

## Requirements

- Bash 4.0 or higher
- Git 2.0 or higher
- Standard Unix tools (sed, awk, grep, date, etc.)

## License

MIT License

## Support

- Report issues: [GitHub Issues](https://github.com/baconag/changelog-generator/issues)
- Ask questions: [GitHub Discussions](https://github.com/baconag/changelog-generator/discussions)

---

*Created for the [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) bounty program.*
*Bounty: $50*