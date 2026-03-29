# generate-changelog

A Claude Code skill and standalone bash script that generates a structured `CHANGELOG.md` from git history, following the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

## Setup (3 Steps)

1. **Copy the skill directory** into your project:
   ```bash
   cp -r bounty-1-changelog-skill/ your-project/.claude/skills/generate-changelog/
   ```

2. **Make the script executable**:
   ```bash
   chmod +x your-project/.claude/skills/generate-changelog/changelog.sh
   ```

3. **Run it** (Claude Code or standalone):
   ```bash
   # Via Claude Code
   /changelog

   # Or directly
   bash changelog.sh
   ```

## Features

- Auto-detects the last git tag and scopes commits accordingly
- Categorizes commits into **Added** / **Fixed** / **Changed** / **Removed** / **Other**
- Primary detection via conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
- Fallback keyword scanning for non-conventional commits
- Strips commit prefixes for clean, readable entries
- Includes short commit hash and author attribution
- Supports `--append` to prepend new sections to an existing CHANGELOG
- Supports `--dry-run` for preview without writing files
- Colored terminal output with `--no-color` override
- Works on any git repository via `--repo` flag

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--output`, `-o` | Output file path | `CHANGELOG.md` |
| `--since` | Tag, commit hash, or date to start from | last git tag |
| `--version` | Override version label | auto-increment patch |
| `--dry-run` | Print to stdout, don't write | off |
| `--append` | Prepend new section to existing file | off |
| `--no-color` | Disable colored terminal output | auto |
| `--repo` | Path to git repository | current directory |

## Commit Prefix Mapping

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `new:`, `feature:` | Added |
| `fix:`, `bug:`, `bugfix:`, `hotfix:`, `patch:` | Fixed |
| `refactor:`, `perf:`, `chore:`, `build:`, `ci:`, `style:`, `docs:`, `test:`, `update:`, `bump:`, `revert:` | Changed |
| `remove:`, `delete:`, `drop:`, `deprecate:` | Removed |

Commits without a recognized prefix are classified via keyword analysis, or placed in **Other**.

## Requirements

- Bash 4+ (for `mapfile` and associative features)
- Git
