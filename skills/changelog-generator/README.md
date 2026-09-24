# Automated Git History Changelog Generator

> Bounty Solution for Opire / GitHub Issue #1: `SKILL: Generate a structured CHANGELOG from git history` ($50)

Generates clean, standardized `CHANGELOG.md` files adhering to [Keep a Changelog](https://keepachangelog.com) directly from git commit history.

## Quickstart (3 Steps or Fewer)

1. **Clone or copy** `generate_changelog.py` and `changelog.sh` into your repo or skill folder.
2. **Make executable**:
   ```bash
   chmod +x changelog.sh generate_changelog.py
   ```
3. **Run**:
   ```bash
   ./changelog.sh v1.0.0
   ```

## Features
- **Auto-tag detection**: Scans commit history since the latest git tag (`git describe --tags --abbrev=0`), or all commits if greenfield.
- **Semantic Classification**:
  - `Added`: `feat:`, `add:`, `introduce`
  - `Fixed`: `fix:`, `bugfix:`, `patch:`, `resolve`
  - `Changed`: `refactor:`, `perf:`, `docs:`, `chore:`, `update`
  - `Removed`: `remove:`, `deprecate:`, `delete`
- **Idempotent Header**: Inserts new release notes cleanly below the `# Changelog` header without overwriting prior releases.
- **Claude Code Skill**: Includes `SKILL.md` for seamless invocation inside Claude Code / Antigravity as `/generate-changelog`.
