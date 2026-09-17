# Generate Changelog Skill & CLI

> Automatically analyzes git history since the latest tag and produces a structured, [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) compliant `CHANGELOG.md`.

## Features

- **Claude Code Skill**: Run directly inside Claude Code via `/generate-changelog`.
- **Standalone POSIX Bash**: Zero runtime dependencies; run directly with `./changelog.sh [file] [version]`.
- **Tag Detection**: Scans commits since `git describe --tags --abbrev=0`. Fallbacks to full commit history on untagged repos.
- **Categorization Engine**: Groups commits into `Added`, `Fixed`, `Changed`, `Removed`, and `Maintenance & Chores`.
- **Non-destructive Updates**: Automatically prepends new release sections under the `# Changelog` heading while preserving historical entries.

## Quick Start

```bash
# Standalone execution
chmod +x skills/generate-changelog/changelog.sh
./skills/generate-changelog/changelog.sh CHANGELOG.md 1.0.0

# Claude Code integration
cp skills/generate-changelog/SKILL.md ~/.claude/skills/generate-changelog.md
```
