# changelog.py

A single-file Python script that generates a structured `CHANGELOG.md` from git history.

Categorizes commits into **Added / Fixed / Changed / Removed** based on [Conventional Commits](https://www.conventionalcommits.org/) prefixes (`feat:`, `fix:`, `refactor:`, etc.) and the `BREAKING CHANGE:` footer.

## Quick Start (3 steps)

```bash
# 1. Drop the script into your repo
curl -o scripts/changelog.py https://raw.githubusercontent.com/phoenix7956/claude-review-bounty/main/scripts/changelog.py
chmod +x scripts/changelog.py

# 2. Tag your last release (if you haven't)
git tag v1.0.0

# 3. Run
python3 scripts/changelog.py
# → writes CHANGELOG.md in the current directory
```

## Usage

```bash
python3 scripts/changelog.py                                    # uses last tag, outputs CHANGELOG.md
python3 scripts/changelog.py --since=v1.0.0                     # from a specific tag/ref
python3 scripts/changelog.py --output=NEWS.md                   # custom output file
python3 scripts/changelog.py --version=v1.2.0                   # custom version label in header
python3 scripts/changelog.py --repo=/path/to/other/repo         # run in another repo
python3 scripts/changelog.py --help                             # show options
```

## What it does

1. Reads git log (`hash|subject|body`) since the last tag (or all commits if no tags)
2. Categorizes each commit by prefix:
   - `feat:` / `feat(` → **Added**
   - `fix:` / `fix(` → **Fixed**
   - `perf:`, `refactor:`, `chore:`, `docs:`, `style:`, `test:`, `build:`, `ci:` → **Changed**
   - `BREAKING CHANGE` / `breaking-change` in body or subject → **Removed (BREAKING CHANGES)**
   - Anything else → **Changed** (uncategorized)
3. Renders a Markdown file with sections + short SHA + commit count footer

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] — 2026-06-12

### Added
- feat(hooks): add block-destructive.py PreToolUse hook (Bounty #3) (4d113a3)
- feat: initial README with bounty board (1aeae2a)

### Fixed
- (none)

### Changed
- Add sample outputs section to README (0aa4c88)
- ...

### Removed (BREAKING CHANGES)
- (none)

---
*13 commits since <beginning>*
```

See [`samples/CHANGELOG-sample-v1.2.0.md`](./samples/CHANGELOG-sample-v1.2.0.md) for a real example run on this repo.

## Why Python (not bash)?

- **Bash 3.2 compat**: macOS ships bash 3.2 (`mapfile`, associative arrays, etc. don't work). Python stdlib handles all of this.
- **Reliable**: One process, no temp file races, deterministic output.
- **No deps**: Pure Python 3.8+ stdlib. Runs anywhere.

## Tested

| Test | Result |
|---|---|
| Default run (no tag, all commits) | ✅ 13 commits categorized |
| `--since=451824b` (specific SHA) | ✅ 3 commits since that ref |
| `--output=/tmp/NEWS.md` | ✅ Wrote to custom path |
| `--version=v1.2.0` | ✅ Custom version in header |
| `--help` | ✅ Usage + options shown |
| Non-git repo | ✅ Exit 1 + clear error |

## Requirements

- Python 3.8+
- git (any recent version)
- A repo with at least one commit (and ideally one tag)

## License

MIT

---

Built by [@phoenix7956](https://github.com/phoenix7956) for [Bounty #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1) ($50).
