# CHANGELOG Generator Skill

A Claude Code / Hermes Agent skill that generates structured, categorized CHANGELOG files from conventional commit messages.

## Overview

This skill analyzes git history and produces a well-formatted `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/) standard. It intelligently parses conventional commit prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, `perf:`, `test:`, `chore:`, `style:`), detects breaking changes, and organizes them into semantic sections.

## Installation

### Option 1: As a Claude Code Skill (`.claude/skills/`)

```bash
mkdir -p .claude/skills/changelog
cp SKILL.md .claude/skills/changelog/
```

Then in Claude Code:
```
/skill changelog
```

### Option 2: As a Standalone Script

```bash
# Make executable
chmod +x changelog_generator.sh

# Symlink to PATH
ln -s "$(pwd)/changelog_generator.sh" ~/.local/bin/changelog
```

## Usage

### Basic
```bash
# Generate from last tag to HEAD
./changelog_generator.sh
```

### Specific Range
```bash
./changelog_generator.sh --since v1.0.0 --to v2.0.0
```

### Custom Output
```bash
./changelog_generator.sh --since v1.0.0 --output CHANGES-v2.md
```

### Custom Tag Pattern
```bash
./changelog_generator.sh --tag-pattern "release-*"
```

## Output Format

The generated `CHANGELOG.md` follows this structure:

```markdown
# Changelog

## [v2.0.0]

### ⚠ Breaking Changes
- 3a1b2c3 refactor!: drop Python 3.8 support

### ✨ Features
- 1a2b3c4 feat: add batch processing mode
- 2b3c4d5 feat: implement retry logic with backoff

### 🐛 Bug Fixes
- 3c4d5e6 fix: handle empty input gracefully

### 📚 Documentation
- 4d5e6f7 docs: add API reference

## [v1.0.0]
...
```

## Automation

### GitHub Actions Integration

```yaml
# .github/workflows/changelog.yml
name: Update Changelog
on:
  release:
    types: [published]
jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Generate Changelog
        run: |
          curl -sL https://raw.githubusercontent.com/your-repo/main/changelog_generator.sh
          chmod +x changelog_generator.sh
          ./changelog_generator.sh --since "$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo '')" --output CHANGELOG.md
      - name: Commit & Push
        run: |
          git config user.name "changelog-bot"
          git config user.email "bot@example.com"
          git add CHANGELOG.md
          git commit -m "docs: update changelog" || true
          git push
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
./changelog_generator.sh --since HEAD~1 --output .git/changelog-staging.md
```

## Requirements

- Git (2.x+)
- Bash (4.x+)
- Conventional commit messages recommended but not required

## Edge Cases Handled

- **No tags**: Generates a flat changelog from the last 100 commits
- **No commits**: Returns "No commits found" message
- **Non-conventional commits**: Categorized as "Other Changes"
- **Empty repos**: Graceful error message
- **Large histories**: Only processes the last 100 commits when no tags present

## Exit Codes

| Code | Meaning |
|:----:|---------|
| 0 | Success |
| 1 | Not a git repository |
| 2 | No commits found |

## License

MIT
