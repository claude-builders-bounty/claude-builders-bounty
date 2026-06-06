---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history.
---

# Generate Changelog

Automatically creates a structured `CHANGELOG.md` from your project's git
history since the last tag. Works best with conventional commits.

## Usage

In Claude Code:

> `/generate-changelog`

Or from the terminal:

> `bash changelog.sh`

## Options

| Flag | Description |
|------|-------------|
| `--output <file>` | Output filename (default: CHANGELOG.md) |
| `--since <ref>`   | Git ref to start from (default: last tag) |
| `--version <ver>` | Version string (default: last tag name) |

## Output structure

Commits are automatically placed into one of five sections:

- **✨ Added** — `feat:`, `add:`, `new:`, `implement:`, `create:`
- **🐛 Fixed** — `fix:`, `bugfix:`, `hotfix:`, `patch:`, `repair:`
- **🔧 Changed** — `refactor:`, `perf:`, `chore:`, `docs:`, `style:`, `test:`, `ci:` etc.
- **🗑️ Removed** — `remove:`, `delete:`, `deprecate:`, `revert:`
- **🔹 Other** — everything else
