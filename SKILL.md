---
name: generate-changelog
description: "Auto-generate a structured CHANGELOG.md from git history. Categorizes commits into Added/Fixed/Changed/Removed."
triggers:
  - generate changelog
  - create changelog
  - update changelog
  - changelog from git
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from a project's git history.

## Usage

Run via command line:

```bash
bash changelog.sh
```

Or with options:

```bash
bash changelog.sh --since-tag v1.0.0 --output CHANGES.md
```

## How It Works

1. **Finds the last git tag** (or uses all commits if no tags exist)
2. **Fetches all commits** since that tag
3. **Auto-categorizes** each commit by prefix:
   - `feat:`, `add:`, `new:`, `create:`, `implement:` → **Added**
   - `fix:`, `bugfix:`, `patch:`, `resolve:`, `correct:` → **Fixed**
   - `refactor:`, `update:`, `improve:`, `change:`, `chore:` → **Changed**
   - `remove:`, `delete:`, `drop:`, `deprecate:` → **Removed**
   - Everything else → **Other**
4. **Outputs** a formatted `CHANGELOG.md`

## Conventional Commits

Works best with [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add user authentication
fix: resolve login timeout
refactor: simplify database queries
docs: update API reference
chore: upgrade dependencies
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--since-tag TAG` | Only include commits after this tag | Last tag |
| `--output FILE` | Output file path | `CHANGELOG.md` |

## Requirements

- `git` installed
- `bash 4+` (for arrays)
- Must run from inside a git repository
