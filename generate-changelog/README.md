# Generate Changelog — Claude Code Skill

A bash script + Claude Code SKILL that generates a structured `CHANGELOG.md` from your project's git history.

## Setup (3 Steps)

**Step 1:** Copy `generate-changelog.sh` into your project root:
```bash
curl -O https://raw.githubusercontent.com/lam1688/claude-builders-bounty/main/generate-changelog/generate-changelog.sh
chmod +x generate-changelog.sh
```

**Step 2 (Optional):** Save `SKILL.md` in `.claude/skills/`:
```bash
mkdir -p .claude/skills
curl -O https://raw.githubusercontent.com/lam1688/claude-builders-bounty/main/generate-changelog/SKILL.md
```

**Step 3:** Run:
```bash
bash generate-changelog.sh
# Or specify a repo path and output file:
bash generate-changelog.sh /path/to/repo CHANGELOG.md
```

## Features

- ✅ Parses conventional commits (`feat:`, `fix:`, `chore:`, etc.)
- ✅ Auto-categorizes into **Added / Fixed / Changed / Removed**
- ✅ Detects last git tag automatically
- ✅ Falls back to last 50 commits if no tags exist
- ✅ Standard Keep a Changelog format
- ✅ No external dependencies (just `git` + standard Unix tools)

## Sample Output

```markdown
# Changelog

## [Unreleased]

### Added
- feat: add user authentication
- feat(search): implement full-text search

### Fixed
- fix(api): handle null response from payment gateway
- fix(ui): resolve flash of unstyled content

### Changed
- chore(deps): upgrade dependencies
- docs: update API documentation
- refactor(core): simplify token validation

### Removed
- refactor!: remove deprecated v1 API endpoints
```

## Requirements

- `git`
- Standard Unix tools: `bash`, `awk`, `sed`, `grep` (available on Linux/macOS, use WSL on Windows)

## License

MIT
