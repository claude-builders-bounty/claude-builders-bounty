# generate-changelog

A zero-dependency way to generate a structured `CHANGELOG.md` from your git history.

## Setup (3 steps or fewer)

1. Copy this folder into your repo (or anywhere with git access):
   ```bash
   cp -r generate-changelog /path/to/your/repo/
   ```
2. Run it from your repo root:
   ```bash
   bash generate-changelog/changelog.sh
   ```
3. Done — a categorized `CHANGELOG.md` is written next to your repo root.

## What it does
- Fetches commits **since the last git tag** (or all commits if the repo has no tags).
- Auto-categorizes into **Added / Changed / Fixed / Removed** by commit prefix.
- Bumps the patch version (`v1.2.3` → `v1.2.4`) for the new dated entry.
- Prepends the new entry to any existing `CHANGELOG.md`, preserving history.

## Claude Code usage
Drop `SKILL.md` into your `~/.claude/skills/` directory (or your project's
`.claude/skills/`). Then invoke with `/generate-changelog`.

## Example output
```markdown
# Changelog

## v0.2.0 — 2026-07-16

### Added
- new GitHub Actions CI workflow

### Fixed
- fix crash on empty config

### Changed
- refactor parser into modules
```

MIT — NullPointerCo. Built for the [claude-builders-bounty]($50 changelog bounty).
