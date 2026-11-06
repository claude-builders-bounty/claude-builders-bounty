# Automated Structured Changelog Generator & Claude Skill

Automatically generates a structured `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com) from git history since the last git tag.

## 3-Step Setup

1. **Copy `changelog.sh`** into your repository root or bin directory:
   ```bash
   chmod +x changelog.sh
   ```

2. **Run manually or via Claude Code**:
   - Bash: `bash changelog.sh`
   - Claude Code / Slash command: `/generate-changelog`

3. **Check results**: Your commits are parsed and categorized in `CHANGELOG.md`.

## Sample Output

```markdown
# Changelog

All notable changes to this project are documented in this file.
Format conforms to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-11-05 (Changes since tag: v1.2.0)

### Added
- feat: add automatic sse stream reconciliation ([a1b2c3d](commit/a1b2c3d))
- feat: implement prefix-aware kv-cache partitioning ([e4f5g6h](commit/e4f5g6h))

### Fixed
- fix: resolve utf-8 chunk boundary parse aborts ([789abc0](commit/789abc0))

### Changed
- chore: upgrade build dependencies ([def1234](commit/def1234))
```
