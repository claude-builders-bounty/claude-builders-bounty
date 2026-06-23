# CHANGELOG Generator

A Python script + Claude Code skill that automatically generates structured `CHANGELOG.md` from git history.

## Quick Start (3 steps)

1. **Copy** `changelog.py` and `SKILL.md` to your project
2. **Run** `python3 changelog.py` to generate `CHANGELOG.md`
3. **Done!** Your changelog is ready.

## Features

- Auto-detects the last git tag as a version boundary
- Categorizes commits into Added / Fixed / Changed / Removed
- Uses conventional commit prefixes (feat:, fix:, chore:, etc.)
- Clean output with short commit hashes
- Works as a standalone script or Claude Code skill

## Sample Output

```markdown
# Changelog

## [v1.0.0]

### Added
- New user authentication system (a1b2c3d)
- API rate limiting middleware (e5f6g7h)

### Fixed
- Memory leak in background worker (i9j0k1l)
```

## License

MIT
