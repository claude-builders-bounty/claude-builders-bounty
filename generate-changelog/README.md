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

**Tested on:** [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty)

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2026-03-29]

### Added
- feat(template): add CLAUDE.md for Next.js + SQLite SaaS projects
- feat(hook): add pre-tool-use hook that blocks destructive bash commands
- feat: add CHANGELOG generator skill
- feat: initial README with bounty board

### Changed
- Initial commit
```

**Generated on claude-builders-bounty repo with:** `bash generate-changelog.sh /path/to/repo CHANGELOG.md`

## Requirements

- `git`
- Standard Unix tools: `bash`, `awk`, `sed`, `grep` (available on Linux/macOS, use WSL on Windows)

## License

MIT
