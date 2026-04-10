# SKILL.md — Generate Changelog

**Bounty:** [$50 — claude-builders-bounty#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

Use this skill when asked to generate, update, or maintain a project's `CHANGELOG.md`.

## Trigger

- `/generate-changelog`
- "update the changelog"
- "add to CHANGELOG"
- "generate release notes"

## How It Works

The skill runs `generate-changelog.sh` which:
1. Finds the most recent git tag (or uses a provided `--since <ref>`)
2. Collects all commits since that tag
3. Categorizes them using [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat*` → **Added**
   - `fix*` → **Fixed**
   - `refactor`, `perf`, `chore`, `docs`, `test`, `ci`, `build`, `deps` → **Changed**
   - Breaking changes (`!` or `BREAKING CHANGE:` in body) → **Breaking**
4. Writes a properly formatted `CHANGELOG.md`

## Usage

```bash
# Generate since last tag (default)
bash generate-changelog.sh

# Generate since a specific tag
bash generate-changelog.sh --since v1.2.0

# Generate since a specific date
bash generate-changelog.sh --since 2026-01-01

# Write to a custom file
bash generate-changelog.sh --output HISTORY.md
```

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2026-04-10] (from v1.2.0)

### Added
  - **auth**: add OAuth2 login support ([`a1b2c3d`](#a1b2c3d))

### Fixed
  - resolve race condition in session store ([`b2c3d4e`](#b2c3d4e))

### Changed
  - **deps**: upgrade Express to v5 ([`c3d4e5f`](#c3d4e5f))

### Breaking
  - **api**: remove deprecated `/v1/users` endpoint ([`d4e5f6g`](#d4e5f6g))
```

## Requirements

- `git`
- Standard Unix tools: `awk`, `grep`, `sed`
- Git history with annotated tags for best results

## Tips

- Tag releases annotatedly for meaningful version headers: `git tag -a v1.2.0 -m "Release v1.2.0"`
- Use Conventional Commits in your commit messages for automatic categorization
- Run the script after merging a release PR, before tagging
- Add to your CI: `bash .claude/scripts/generate-changelog.sh && git add CHANGELOG.md`
