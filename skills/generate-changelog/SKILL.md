---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, auto-categorised into Added / Fixed / Changed / Removed.
---

# generate-changelog

Generate a structured `CHANGELOG.md` from a project's git history since the last tag.

## Usage

```bash
./changelog.sh [repo-path] [output-file]
```

- `repo-path` — target repository (default: current directory)
- `output-file` — output path (default: `CHANGELOG.md`)

## What it does

1. Finds the last git tag (`git describe --tags --abbrev=0`).
2. Collects commits from that tag to `HEAD` (or full history if no tag).
3. Categorises each commit by Conventional Commit prefix:
   - `feat`, `feature`, `add`, `new` → **Added**
   - `fix`, `bugfix`, `hotfix` → **Fixed**
   - `refactor`, `style`, `change`, `update`, `perf` → **Changed**
   - `remove`, `delete`, `rm`, `deprecat` → **Removed**
4. Writes a Keep-a-Changelog style `CHANGELOG.md` with commit links.

## Requirements

- `bash` 4+, `git`
