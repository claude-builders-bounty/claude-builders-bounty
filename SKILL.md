---
name: generate-changelog
description: Generate a structured CHANGELOG.md from the project's git history
---

# `/generate-changelog`

Generates or updates `CHANGELOG.md` by analyzing the project's git log since the last tag.

## Usage

Run from the project root:

```bash
bash changelog.sh
```

Or invoke via Claude Code:

```bash
/generate-changelog
```

## What it does

1. Finds the most recent git tag (or uses initial commit if none exist)
2. Scans all commits since that point
3. Categorizes each commit as **Added**, **Fixed**, **Changed**, or **Removed**
4. Writes a clean `CHANGELOG.md` to the project root

## Categorization rules

| Prefix | Category |
|--------|----------|
| `feat:`, `feature:`, `add:`, `new:` | Added |
| `fix:`, `bugfix:`, `bug:`, `hotfix:` | Fixed |
| `change:`, `refactor:`, `update:`, `perf:` | Changed |
| `remove:`, `delete:`, `deprecate:`, `drop:` | Removed |
| `docs:`, `doc:`, `readme:` | Documentation |
| `test:`, `spec:` | Testing |
| Everything else | Changed |
