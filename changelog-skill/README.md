# changelog.sh

Generate a structured `CHANGELOG.md` from git history. Zero dependencies, pure bash + git.

## Setup (3 steps)

1. Copy `changelog.sh` into your repo root.
2. `chmod +x changelog.sh`
3. Run `bash changelog.sh`

## What it does

- Finds the last git tag reachable from HEAD (`git describe --tags --abbrev=0`).
- Lists every non-merge commit since that tag (or all history if no tags exist).
- Categorizes each commit subject into **Added / Fixed / Changed / Removed** by keyword (feat/add, fix/bug, remove/delete, everything else).
- Writes a dated `[Unreleased]` section. On re-run it prepends the new section above existing entries, so history is preserved.

## Usage

```bash
bash changelog.sh              # writes CHANGELOG.md
bash changelog.sh CHANGES.md   # custom output file
```

## Sample output

From a test repo with 5 commits after tag `v0.1.0`:

```markdown
# Changelog

## [Unreleased] — 2026-08-24

_myrepo: commits since v0.1.0_

### Added

- feat: add CSV export option (`4dabbae`)

### Fixed

- fix: correct off-by-one in pagination (`f46d8aa`)

### Changed

- refactor: simplify parser loop (`f2e94bf`)

### Removed

- remove legacy XML support (`a1e41bd`)
```

## Claude Code integration

Also shipped as a skill: see `SKILL.md`. Invoke with `/generate-changelog` after installing the skill folder.
