# generate-changelog

> Claude Code skill — generate a structured `CHANGELOG.md` from git history in seconds.

## Setup (3 steps)

**1. Copy the script to your repo**

```bash
curl -o scripts/changelog.sh \
  https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/bounty-1/scripts/changelog.sh
chmod +x scripts/changelog.sh
```

**2. Register the skill with Claude Code**

```bash
mkdir -p .claude/skills
cp skills/generate-changelog/SKILL.md .claude/skills/generate-changelog.md
```

**3. Run it**

```bash
# Via Claude Code
/generate-changelog

# Or directly
bash scripts/changelog.sh
```

---

## Features

| Feature | Details |
|---------|---------|
| Auto range detection | Uses last git tag; falls back to first commit when no tags exist |
| Conventional commits | Parses `feat:`, `fix:`, `chore:`, `remove:`, `refactor:`, etc. |
| Keyword fallback | Categorizes commits without conventional prefixes by scanning subject text |
| `--since` flag | Override range with a tag, commit hash, or date string |
| `--dry-run` | Preview in terminal — nothing written to disk |
| `--no-color` | CI-friendly plain-text mode |
| `--version` | Override the version heading |
| Merge-commit safe | `--no-merges` ensures clean output |
| Zero dependencies | Pure bash + git — works everywhere |

## Output format

```markdown
## [v1.3.0] — 2025-06-15

### Added
- feat: add dark mode toggle (`a1b2c3d`) — *Jane Dev*

### Fixed
- fix: correct timezone offset in scheduler (`d4e5f6a`) — *Bob Ops*

### Changed
- chore: upgrade dependencies to latest (`7890abc`) — *Jane Dev*
```

## Options

```
--since <tag|date>   Commits since this ref (tag, hash, or "YYYY-MM-DD")
--output <file>      Output file path (default: CHANGELOG.md)
--dry-run            Print to stdout only, no file written
--no-color           Disable ANSI colors (auto-detected in CI)
--version <label>    Version heading (default: next patch from last tag)
--help               Show usage
```
