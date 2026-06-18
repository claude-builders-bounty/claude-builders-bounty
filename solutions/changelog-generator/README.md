# changelog.sh

Generate a structured `CHANGELOG.md` from any git repository's history.

## Setup

1. **Download** — save `changelog.sh` anywhere (no dependencies beyond bash + git).
2. **Run** — `bash changelog.sh` from any git repo, or `bash changelog.sh --repo /path/to/repo`.
3. **Save** — `bash changelog.sh --output CHANGELOG.md` writes the file directly.

## How it works

- Fetches all commits since the latest git tag (or since the beginning if no tags exist)
- Auto-categorizes into: **Added** · **Fixed** · **Changed** · **Removed** · **Deprecated** · **Security**
- Uses conventional commit prefixes (`feat:`, `fix:`, etc.) with keyword fallback
- Includes a summary header with total commit count and a GitHub compare link

## Example output

```markdown
# Changelog

## [v1.2.3] - 2026-06-18

**37 commits** since v1.2.2

### Added
- feat: add user onboarding flow (abc1234)
- feat: implement dark mode toggle (def5678)

### Fixed
- fix: resolve crash on empty state (ghi9012)
- fix: correct pagination offset (jkl3456)

### Changed
- refactor: extract API client module (mno7890)
- perf: optimize image loading (pqr1234)
```

A real sample output is included in `sample_output/CHANGELOG.md` (generated from the OpenClaw workspace — 883 commits).
