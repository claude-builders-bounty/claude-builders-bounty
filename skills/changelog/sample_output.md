# Sample Output — Tested on Real Git Repo

## Test setup

Created a git repo with 8 commits spanning a `v1.0.0` tag:
- 3 commits before the tag (feat, fix, refactor)
- 4 commits after the tag (feat, add, remove, update)

## Command run

```bash
bash changelog.sh --dry-run --version v1.1.0
```

## Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Commits follow [Conventional Commits](https://www.conventionalcommits.org/) where possible.

## [v1.1.0] — 2026-03-31

### Added

- add rate limiting middleware for API (`b0e197c`)
- introduce Prometheus metrics endpoint (`e03282f`)

### Changed

- update CI workflow to use Ubuntu 22.04 (`0a88a82`)

### Removed

- remove deprecated /v1/legacy endpoint (`2c194a4`)
```

## Summary

```
Added:   2
Fixed:   0
Changed: 1
Removed: 1
```

All 4 commits since the `v1.0.0` tag were correctly fetched and categorised.
Conventional-commit prefixes (`feat:`, `fix:`, etc.) were automatically stripped.
