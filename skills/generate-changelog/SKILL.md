---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Use when the user asks for a changelog, release notes, or wants to see what changed between tags. Auto-categorizes commits into Added/Fixed/Changed/Removed.
---

# Generate Changelog

A Claude Code skill that turns `git log` into a properly structured `CHANGELOG.md`, following the [Keep a Changelog](https://keepachangelog.com/) convention.

## When to use

- The user asks for a CHANGELOG, release notes, or "what changed since last release"
- The user runs `/generate-changelog`
- A project has git history but no `CHANGELOG.md`
- A user wants to refresh `CHANGELOG.md` before a release

## How it works

1. Reads git tags in reverse chronological order
2. For each tag (and the unreleased range above the latest tag), fetches commits
3. Auto-categorizes each commit into `Added` / `Fixed` / `Changed` / `Removed` based on Conventional Commits prefixes
4. Renders a `CHANGELOG.md` that follows Keep a Changelog format

## Usage

### As a Claude Code skill

```
/generate-changelog
/generate-changelog --since v1.2.0
/generate-changelog --output CHANGELOG.md
```

### As a standalone bash script

```bash
bash skills/generate-changelog/scripts/changelog.sh
bash skills/generate-changelog/scripts/changelog.sh --since v1.2.0 --output CHANGELOG.md
```

### As a Python module

```bash
python3 skills/generate-changelog/scripts/changelog.py --repo . --output CHANGELOG.md
```

## Acceptance Criteria

This implementation satisfies the bounty #1 spec:

- [x] Works via `/generate-changelog` command or `bash changelog.sh`
- [x] Fetches commits since the last git tag
- [x] Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] Tested on a real GitHub repo (sample output in `sample/`)
- [x] README with setup instructions in 3 steps or fewer (this file)

## Categorization rules

We map Conventional Commits prefixes to Keep a Changelog categories:

| Commit prefix               | CHANGELOG section |
| --------------------------- | ----------------- |
| `feat:`, `feat(scope):`     | Added             |
| `fix:`, `fix(scope):`       | Fixed             |
| `refactor:`, `perf:`, `style:` | Changed        |
| `docs:`, `test:`, `chore:`  | _(ignored as noise)_ |
| `BREAKING CHANGE:` in body  | Changed (promoted to top) |
| `revert:` or `removed:`     | Removed           |

Commits without a recognized prefix go to **Changed** by default.

## Files

```
skills/generate-changelog/
├── SKILL.md                    # this file
├── scripts/
│   ├── changelog.sh            # bash implementation
│   └── changelog.py            # python implementation
├── tests/
│   ├── test_categorize.py      # 16 unit tests
│   └── fixtures/               # synthetic git repos for testing
└── sample/
    └── CHANGELOG.md            # generated from a real GitHub repo
```

## Tested with

- bash ≥ 4.0 (uses `[[ ]]`, arrays, parameter expansion)
- python ≥ 3.7 (uses f-strings, dataclasses, pathlib)
- git ≥ 2.20 (uses `--format=%H`, range queries)