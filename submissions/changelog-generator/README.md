# 📋 changelog-generator — Structured CHANGELOG from git history

**Bounty:** [claude-builders-bounty/claude-builders-bounty#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1) — $50

## Setup (3 steps)

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/davidsineri/claude-builders-bounty/main/submissions/changelog-generator/changelog.sh

# 2. Make executable
chmod +x changelog.sh

# 3. Generate
./changelog.sh
```

## Claude Code Integration

Copy `SKILL.md` to `~/.claude/skills/generate-changelog/` and use `/generate-changelog` in Claude Code.

## Output

```
# Changelog

## [v1.2.0] - 2026-05-30

### Added
- New dashboard charts
- Export to PDF

### Fixed
- Login timeout on Safari
- Null pointer in billing

### Changed
- Updated API rate limits

### Removed
- Deprecated v1 endpoints
```

## Sample

See [`sample-output/`](sample-output/) for example output.
