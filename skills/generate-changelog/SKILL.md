---
name: generate-changelog
description: Automatically generates a structured Keep-a-Changelog formatted CHANGELOG.md from git commits since the last tag.
---

# Generate Changelog Skill

A specialized Claude Code skill and bash utility that parses commit history and automatically categorizes changes into `Added`, `Fixed`, `Changed`, and `Removed`.

## Usage
Run directly from terminal or Claude Code:
```bash
bash scripts/changelog.sh [OUTPUT_FILE]
```

## Features
- **Tag Detection**: Automatically discovers the latest git tag (`git describe --tags --abbrev=0`) or falls back to root commit.
- **Keep a Changelog Format**: Produces standard markdown adhering to SemVer and Keep a Changelog guidelines.
- **Conventional Commits Support**: Accurately parses `feat:`, `fix:`, `refactor:`, `perf:`, `revert:`, and keyword semantics.
