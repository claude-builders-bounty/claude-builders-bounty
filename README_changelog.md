# CHANGELOG Generator

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) skill that automatically generates structured `CHANGELOG.md` files from git history.

## Quick Start

### 1. Install the skill

```bash
# Copy SKILL.md to your Claude Code project
cp SKILL.md .claude/skills/generate-changelog.md
```

### 2. Use it

In any git repository with Claude Code running, type:

```
/generate-changelog
```

## Standalone Script

You can also run the generator as a standalone bash script:

```bash
bash changelog.sh
```

## Sample Output

```markdown
# Changelog

## [1.2.0] - 2026-03-15

### Added
- Add user authentication via OAuth
- Implement rate limiting middleware

### Fixed
- Fix memory leak in WebSocket handler
- Correct pagination offset calculation

### Changed
- Upgrade dependencies to latest versions
- Refactor database query layer
```
