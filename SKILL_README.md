# Generate Changelog — Claude Code Skill

Generate a structured `CHANGELOG.md` from git history in one command.

## Setup (3 steps)

```bash
# 1. Copy the skill to your project
cp SKILL.md .claude/skills/generate-changelog.md
cp changelog.sh scripts/changelog.sh
chmod +x scripts/changelog.sh

# 2. (Optional) Add to .gitignore if you don't want the script tracked
# echo "scripts/changelog.sh" >> .gitignore

# 3. Run it
bash scripts/changelog.sh
```

Or via Claude Code: just type `/generate-changelog`

## What it does

- 🔍 Fetches commits since the **latest git tag**
- 🏷️ Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
- 📝 Outputs a properly formatted `CHANGELOG.md`
- 🔄 Prepends new entries (won't overwrite existing changelog)
- ⏭️ Skips merge commits automatically

## Example output

```markdown
# Changelog

## Unreleased (since v1.2.0) — 2026-05-19

### Added
- Dark mode toggle in settings (a1b2c3d)
- Export to PDF feature (e4f5g6h)

### Fixed
- Login redirect loop on Safari (i7j8k9l)
- Memory leak in WebSocket handler (m0n1o2p)

### Changed
- Updated dependencies to latest versions (q3r4s5t)

### Removed
- Deprecated /v1 API endpoint (u6v7w8x)
```

## Requirements

- `git` installed
- Bash 4.0+ (macOS / Linux / WSL)
- No external dependencies

## Dry run

```bash
bash changelog.sh --dry-run
```

Print the changelog to stdout without writing any files.

---

Part of the [Claude Builders Bounty](https://github.com/claude-builders-bounty) program.
