---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history since the last tag. Use when asked to create or update a changelog, write release notes, or run /generate-changelog.
allowed-tools: Bash, Read, Write
---

# Generate Changelog

Run the bundled script from the repository root:

```bash
bash skills/generate-changelog/changelog.sh
```

## Options

- `--since <tag>` — start from a specific tag instead of the latest
- `--output <file>` — write to a different file (default: `CHANGELOG.md`)
- `--preview` — print to stdout without writing a file

## Behavior

1. Detects the latest git tag (or uses `--since`)
2. Collects commits after that tag
3. Categorizes conventional commits into **Added**, **Fixed**, **Changed**, and **Removed**
4. Writes a Keep a Changelog-style `CHANGELOG.md`

## Classification

| Commit prefix | Section |
|---------------|---------|
| `feat:`, `add:`, `implement:`, `create:` | Added |
| `fix:`, `bug:`, `hotfix:`, `patch:`, `resolve:` | Fixed |
| `update:`, `change:`, `refactor:`, `migrate:`, `perf:` | Changed |
| `remove:`, `delete:`, `deprecat:` | Removed |
