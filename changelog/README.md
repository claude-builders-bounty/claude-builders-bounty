# Generate CHANGELOG from Git History

Automatically generates a structured CHANGELOG.md from git commit history with smart categorization.

## Quick Setup (3 steps)

```bash
# 1. Copy to your project
cp changelog/generate-changelog.sh /path/to/your/project/

# 2. Make executable
chmod +x generate-changelog.sh

# 3. Run
./generate-changelog.sh
```

## Usage

```bash
# Generate since last tag (default)
./generate-changelog.sh

# Generate since specific tag
./generate-changelog.sh v1.0.0

# Generate to custom file
./generate-changelog.sh v1.0.0 CUSTOM.md
```

## Features

- ✅ Auto-detects latest git tag
- ✅ Categorizes: Added / Fixed / Changed / Removed / Other
- ✅ Supports conventional commits (feat:, fix:, etc.)
- ✅ Includes commit links and authors
- ✅ Follows Keep a Changelog format
- ✅ Appends to existing CHANGELOG

## Commit Format

Use conventional commit prefixes for best results:

```
feat: add new feature
fix: resolve login bug
chore: update dependencies
remove: delete deprecated code
```

## Claude Code Integration

This tool can be used as a Claude Code skill. See [SKILL.md](SKILL.md) for details.
