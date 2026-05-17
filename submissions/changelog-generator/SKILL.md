---
name: changelog-generator
description: "Generate a structured CHANGELOG.md from git history with automatic commit categorization"
version: 1.0.0
author: "Claude Builders Bounty"
---

# Changelog Generator Skill

Automatically generates a structured `CHANGELOG.md` from a project's git history. Categorizes commits into **Added**, **Fixed**, **Changed**, and **Removed** sections using conventional commit parsing.

## Usage

### Via slash command

When this skill is loaded, use:

```
/generate-changelog [--repo PATH] [--output FILE]
```

This runs the bundled `changelog.py` script against the specified repo (defaults to current directory).

### Via direct script

```bash
python changelog.py
python changelog.py --repo /path/to/project
python changelog.py --repo . --output CHANGELOG.md --from-tag v1.0.0
```

## How it works

1. Finds the most recent git tag (e.g. `v1.0.0`)
2. Fetches all non-merge commits since that tag
3. Parses each commit message using conventional commit format
4. Auto-categorizes into:
   - **✨ Added** — `feat:`, `add:`, `create:`, `new:`
   - **🔄 Changed** — `refactor:`, `update:`, `chore:`, `docs:`, `test:`, `improve:`
   - **🐛 Fixed** — `fix:`, `bug:`, `hotfix:`, `patch:`
   - **🗑️ Removed** — `remove:`, `delete:`, `drop:`, `cleanup:`
5. Writes a properly formatted `CHANGELOG.md`

## Example output

```markdown
# Changelog

> my-user/my-repo

## [v1.0.0] — 2026-05-17

### ✨ Added
- Add user authentication module ([`abc1234`](https://github.com/my-user/my-repo/commit/abc1234))
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--repo` | Path to the git repository | `.` (current directory) |
| `--output` | Output file path | `CHANGELOG.md` |
| `--from-tag` | Start from a specific tag | Most recent tag |
| `--to-ref` | End reference | `HEAD` |

## Requirements

- Python 3.6+
- `git` must be installed and available in PATH
