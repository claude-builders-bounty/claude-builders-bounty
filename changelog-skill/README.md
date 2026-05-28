# 📋 Changelog Generator

A Claude Code skill and bash script that generates structured `CHANGELOG.md` files from git history.

**Bounty:** [#1 — $50](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

## Quick Start (3 steps)

```bash
# 1. Clone
git clone https://github.com/RomuloGatto/claude-builders-bounty.git

# 2. Make executable
chmod +x claude-builders-bounty/changelog-skill/changelog.sh

# 3. Run in any git repo
cd your-project && bash /path/to/changelog.sh
```

## What It Does

- Fetches commits since the last git tag
- Auto-categorizes into **Added**, **Fixed**, **Changed**, **Removed** using conventional commit prefixes
- Outputs a properly formatted `CHANGELOG.md`

## Categorization

| Prefix | Category |
|--------|----------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `perf:`, `docs:`, `chore:` | Changed |
| `remove:`, `delete:`, `deprecate:` | Removed |

## Claude Code Integration

This also works as a Claude Code skill — copy `SKILL.md` to your `.claude/skills/` directory.

## Acceptance Criteria

- [x] Works via `bash changelog.sh`
- [x] Fetches commits since last git tag
- [x] Auto-categorizes: Added / Fixed / Changed / Removed
- [x] Outputs properly formatted `CHANGELOG.md`
- [x] README with setup in 3 steps or fewer

## License

MIT
