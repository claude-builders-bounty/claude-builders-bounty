# SKILL: Generate Changelog from Git History

## Trigger
`/generate-changelog` — Run this command in any Claude Code project to auto-generate a `CHANGELOG.md`.

## How It Works
1. Reads all commits since the last git tag
2. Parses conventional commit messages (feat:, fix:, etc.)
3. Categorizes into Added / Fixed / Changed / Removed
4. Outputs a formatted `CHANGELOG.md`

## Installation
```bash
# Option A: Direct clone into ~/.claude/skills/
git clone https://github.com/nxz1026/claude-builders-bounty.git ~/.claude/skills/generate-changelog
chmod +x ~/.claude/skills/generate-changelog/changelog.sh

# Option B: Standalone script
curl -O https://raw.githubusercontent.com/nxz1026/claude-builders-bounty/main/changelog.sh
chmod +x changelog.sh
```

## Usage
```bash
# Generate changelog for current repo
bash changelog.sh

# Or from any repo path
bash /path/to/changelog.sh /path/to/repo
```

## Sample Output
```markdown
# Changelog

## [v1.2.0] - 2026-05-19

### Added
- User authentication with JWT
- Dashboard export to CSV

### Fixed
- Race condition in async handler (closes #42)
- Memory leak in cache module

### Changed
- Upgrade to Node.js 22
- Refactor database connection pool

### Removed
- Legacy REST endpoints (deprecated in v1.0)
```

## How It Works (Technical Detail)
The script uses `git tag` to find the last release, then `git log` to enumerate commits between tags. Conventional commits are auto-detected:
- `feat:` → Added
- `fix:` → Fixed
- `perf:` / `refactor:` → Changed
- `chore:` / `docs:` → Changed (minor)

Unconventional commits are grouped under Changed with the raw subject line.

## Requirements
- Git 2.0+
- Bash 4.0+ or Python 3.8+
- No external dependencies
