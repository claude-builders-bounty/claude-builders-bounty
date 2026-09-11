---
name: generate-changelog
description: Generates a structured CHANGELOG.md from git history since the last tag.
---

# Generate Changelog

Auto-categorizes commits since the last git tag into **Added / Fixed / Changed / Removed**
and writes a formatted `CHANGELOG.md`.

## Usage

Run this skill with `/generate-changelog` or call the bundled script:

```bash
bash scripts/generate-changelog.sh            # since last tag
bash scripts/generate-changelog.sh v1.2.0     # since a specific tag
bash scripts/generate-changelog.sh "" CHANGELOG.md  # custom output path
```

## How it classifies commits

| Conventional prefix | Section |
|---|---|
| `feat:`, `add:`, `support:` | **Added** |
| `fix:`, `bug:`, `hotfix:` | **Fixed** |
| `refactor:`, `chore:`, `perf:`, `docs:` | **Changed** |
| `remove:`, `drop:`, `deprecate:` | **Removed** |
| anything else | **Changed** |

## Output format

```
# Changelog

All notable changes since `v1.1.0`.

## 2026-09-11

### Added
- feat(api): add /v2/list endpoint

### Fixed
- fix(auth): refresh token expiry
...
```

## Notes
- Idempotent: safe to run repeatedly; overwrites the target file.
- Works in any git repo; no external dependencies beyond `git` + `bash`.