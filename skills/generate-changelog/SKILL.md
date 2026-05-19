---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Auto-categorizes commits into Added / Fixed / Changed / Removed sections.
argument-hint: "[version]"
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from git history using the `/generate-changelog` command, or by running `bash changelog.sh [version]`.

## Usage

```
/generate-changelog v1.2.0
```

Or from the terminal:

```bash
bash changelog.sh v1.2.0
```

## What It Does

1. Determines the `since` range: commits since the most recent git tag, or all commits if no tag exists.
2. Scans each commit message and categorizes it by Conventional Commits prefix:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `refactor:`, `perf:`, `style:` → **Changed**
   - `revert:`, `remove:` → **Removed**
   - Everything else → **Changed**
3. Writes a new release section at the top of `CHANGELOG.md` (creates the file if it doesn't exist).

## Implementation

The canonical implementation lives at `changelog.sh` in the repository root.

## Examples

```bash
# Generate changelog for v1.0.0
bash changelog.sh v1.0.0

# Preview without writing (dry run)
DRY_RUN=1 bash changelog.sh v2.0.0
```
