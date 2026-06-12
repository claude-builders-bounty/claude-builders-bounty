# SKILL: Generate a Structured CHANGELOG from Git History

Trigger: `/generate-changelog`

## Overview

This skill runs `changelog.sh` to generate a structured `CHANGELOG.md` file from
the project's Git history. Commits are automatically classified into **Added** /
**Fixed** / **Changed** / **Removed** categories based on conventional commit
prefixes and keyword heuristics.

## Usage

Run from the project root:

```
/generate-changelog
```

Or call the script directly:

```bash
bash changelog.sh
```

## Variants

| Command | Behaviour |
|---------|-----------|
| `/generate-changelog` | Commits since last Git tag → HEAD |
| `/generate-changelog --all` | All commits in the repository |
| `/generate-changelog --tag v1.0.0` | From a specific tag to HEAD |
| `/generate-changelog v1.0.0..v2.0.0` | A range of tags |

To redirect output to a specific file, set the `OUTPUT_FILE` environment
variable:

```bash
OUTPUT_FILE=docs/CHANGELOG.md bash changelog.sh
```

## How It Works

1. Determines the commit range (last tag → HEAD by default).
2. Reads `git log --oneline` for the range.
3. Classifies each commit by prefix:
   - `feat:`, `add`, `implement`, `create`, `introduce`, `new` → **Added**
   - `fix:`, `resolve`, `patch`, `correct`, `hotfix` → **Fixed**
   - `change`, `update`, `refactor`, `perf`, `improve`, `enhance` → **Changed**
   - `remove`, `delete`, `drop`, `deprecate`, `revert` → **Removed**
4. Skips merge commits and reverts.
5. Writes a Keep-a-Changelog–style `CHANGELOG.md`.

## Requirements

- `git` 2.x+
- `bash` 4.x+

No other dependencies.
