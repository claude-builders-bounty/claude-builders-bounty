# Git Changelog Generator Skill

A bash script and Claude Code skill that automatically generates a structured `CHANGELOG.md` from git history categorized into `Added`, `Fixed`, `Changed`, and `Removed`.

## Setup & Usage (3 steps)

1. **Make executable**: `chmod +x changelog.sh`
2. **Run script**: `./changelog.sh` (or `bash changelog.sh`)
3. **Check output**: Inspect the generated `CHANGELOG.md` in your repository root.

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-09-10

### Added
- feat: add git changelog generator skill and script (a1b2c3d)

### Fixed
- fix: resolve tag detection edge case (e4f5g6h)
```
