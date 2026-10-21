---
name: generate-changelog
description: Automatically generates or updates CHANGELOG.md from recent git commit history, categorized by conventional commit tags (Added, Fixed, Changed, Removed).
---

# Generate Changelog Skill

Use this skill to automatically audit your project's git commit history and produce a clean, standardized `CHANGELOG.md`.

## Slash Command
`/generate-changelog`

## How it works
1. Detects the latest git tag (e.g. `v1.2.0`). If no tag exists, it parses commits across the entire branch history.
2. Groups commits using Conventional Commit standards:
   - `feat:` $\rightarrow$ **Added**
   - `fix:` $\rightarrow$ **Fixed**
   - `refactor:`, `perf:`, `chore:`, `update:` $\rightarrow$ **Changed**
   - `remove:`, `deprecate:` $\rightarrow$ **Removed**
3. Automatically prepends the new version block into `CHANGELOG.md` with commit hashes and author attribution.

## Execution
Run the embedded script:
```bash
bash changelog.sh CHANGELOG.md
```
