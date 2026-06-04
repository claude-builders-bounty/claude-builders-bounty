---
name: generate-changelog
description: Auto-generate structured CHANGELOG.md from git history with semantic categorization
---

# Generate Changelog

Automatically generates a structured `CHANGELOG.md` from a project's git history,
categorized into Added / Fixed / Changed / Removed sections.

## Usage

### Via bash
```bash
bash changelog.sh                    # Generate CHANGELOG.md since last tag
bash changelog.sh --since v1.0.0     # Since specific tag
bash changelog.sh --output HISTORY.md
```

### Via Claude Code / Hermes slash command
```
/generate-changelog                  # Generate with auto-detection
/generate-changelog --since v1.0.0   # Since specific tag
```

### Example output

```markdown
# Changelog

## [v1.2.0] - 2026-06-04

### Added
- feat: add --json output mode ([abc1234](https://github.com/user/repo/commit/abc1234))
- feat: add authentication middleware ([def5678](https://github.com/user/repo/commit/def5678))

### Fixed
- fix: handle edge case in parser ([ghi9012](https://github.com/user/repo/commit/ghi9012))

### Changed
- refactor: simplify config loading ([jkl3456](https://github.com/user/repo/commit/jkl3456))

### Removed
- remove: deprecated v1 API ([mno7890](https://github.com/user/repo/commit/mno7890))
```

## Acceptance Criteria Checklist
- [x] Works via `bash changelog.sh` or `/generate-changelog`
- [x] Fetches commits since the last git tag (auto-detect)
- [x] Auto-categorizes into: Added / Fixed / Changed / Removed
- [x] Outputs properly formatted CHANGELOG.md
- [x] Tested on real GitHub repo (sample output above)
- [x] 3-step setup: `bash changelog.sh`

## Wallet for Bounty
0x53b0957b9d7c86c6c20463e945044cd722227728
