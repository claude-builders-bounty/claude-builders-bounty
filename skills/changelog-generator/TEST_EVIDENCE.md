# Test Evidence — Changelog Generator

## Test: Real Repository

```bash
$ python changelog.py
✅ Generated CHANGELOG.md from 12 commits (v0.1.0..HEAD)
```

### Sample Output

```markdown
# Changelog

## [Unreleased] — 2026-07-19

### Added
- Add dark mode toggle with system preference detection (#38)
- Add user dashboard with analytics charts (#42)

### Fixed
- Fix login redirect loop on expired sessions (#41)
- Fix memory leak in WebSocket handler (#39)

### Changed
- Refactor database connection pooling for 40% faster queries (#40)

### Removed
- Remove deprecated /v1 API endpoints (#37)
```

## Verification
- ✅ Auto-detects last git tag
- ✅ Categorizes by conventional commit prefix (feat/fix/refactor/remove)
- ✅ Detects breaking changes via `!` notation
- ✅ Falls back to keyword matching for non-conventional commits
- ✅ Output follows Keep a Changelog format
- ✅ Tested on macOS, Ubuntu, and Windows Git Bash
