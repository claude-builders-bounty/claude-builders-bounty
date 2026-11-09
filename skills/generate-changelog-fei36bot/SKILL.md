---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag.
---

# Generate Changelog

Run `/generate-changelog` or `bash changelog.sh` in a git repo.

## Behavior
1. Resolve the latest annotated/lightweight tag (fallback: first commit).
2. Collect commits after that tag (`git log <tag>..HEAD`).
3. Categorize by conventional-commit prefixes and keyword heuristics into Added / Fixed / Changed / Removed.
4. Write/overwrite `CHANGELOG.md` at the repo root with an Unreleased section dated today (UTC).

## Categories
- **Added**: `feat`, `add`, `introduce`, `create`, `implement`
- **Fixed**: `fix`, `bug`, `hotfix`, `patch`, `resolve`
- **Changed**: `refactor`, `perf`, `chore`, `update`, `improve`, `docs`, `style`, `test`, `ci`, `build`
- **Removed**: `remove`, `delete`, `drop`, `deprecate`
