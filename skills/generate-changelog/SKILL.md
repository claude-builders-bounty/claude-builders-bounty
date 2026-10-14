---
name: generate-changelog
description: Automatically generates a structured, Keep-a-Changelog compliant CHANGELOG.md from git commit history since the last git tag. Categorizes commits into Added, Fixed, Changed, and Removed.
---

# /generate-changelog

Use this skill whenever you need to release a new version or document git commits made since the last release tag.

## Execution

Run the bundled changelog script directly from the repository root:

```bash
bash skills/generate-changelog/changelog.sh
```

Or execute via Python:

```bash
python3 skills/generate-changelog/changelog.py
```

## How It Works

1. **Tag Detection**: Determines the most recent git tag (`git describe --tags --abbrev=0`). If no tag exists, it captures all commits from the repository genesis.
2. **Commit Categorization**: Parses conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `chore:`, `perf:`, `docs:`, etc.) and maps them into Keep a Changelog categories:
   - `Added`: `feat`, `feature`, `new`, `add`
   - `Fixed`: `fix`, `bug`, `patch`, `resolve`
   - `Changed`: `refactor`, `perf`, `chore`, `update`, `style`
   - `Removed`: `remove`, `delete`, `deprecate`
3. **Structured Rendering**: Formats into `CHANGELOG.md` with commit hashes, author attribution, and date stamps.
