# Changelog Generator

Auto-generate a structured `CHANGELOG.md` from git history.

## Setup

1. Save `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh > CHANGELOG.md`

### Claude Code integration

Add to `CLAUDE.md`:
```
/generate-changelog = bash changelog.sh > CHANGELOG.md && echo "Generated CHANGELOG.md"
```

## Sample Output

Using this repo's own commits:
```
# Changelog

### Added
- feat: add changelog generator with categorized sections (#abc1234, @user, 2026-05-29)
- feat: add README with setup instructions (#def5678, @user, 2026-05-29)

### Changed
- refactor: simplify commit categorization logic (#ghi9012, @user, 2026-05-28)
```
