---
name: generate-changelog
description: Automatically generates a structured, Keep-a-Changelog compliant CHANGELOG.md from git commit history with automatic categorization (Added, Fixed, Changed, Performance, Security, Removed).
triggers:
  - "/generate-changelog"
  - "generate changelog"
  - "create changelog"
  - "update changelog"
---

# Generate Changelog Skill 📝

Extracts git commit history from the latest git tag or specified commit, groups entries following Conventional Commits standards, and prepends a formatted release block to `CHANGELOG.md`.

## Capabilities
1. **Automatic Tag Detection**: Determines the latest git release tag via `git describe --tags --abbrev=0`.
2. **Conventional Commit Categorization**: Parses `feat:`, `fix:`, `refactor:`, `perf:`, `security:`, `chore:`, etc.
3. **Semantic Versioning Compliance**: Adheres to [Keep a Changelog 1.0.0](https://keepachangelog.com/en/1.0.0/).
4. **Zero Dependencies**: Uses native Python 3 standard library.

## Usage

### Via Claude Code Command:
```bash
/generate-changelog
```

### Via CLI / Bash:
```bash
# Auto-detect latest tag and update CHANGELOG.md
python skills/generate-changelog/generate_changelog.py

# Specify custom version and date
python skills/generate-changelog/generate_changelog.py --version "v1.2.0" --date "2026-08-16"

# Preview changelog output without modifying files
python skills/generate-changelog/generate_changelog.py --stdout
```
