---
name: generate-changelog
description: Automatically generate a structured Keep-a-Changelog (CHANGELOG.md) from git commit history since the latest tag, categorizing commits into Added, Fixed, Changed, and Removed.
---

# `/generate-changelog` — Structured Git Changelog Generator Skill

Generate a clean, Keep-a-Changelog 1.1.0 compliant `CHANGELOG.md` from any Git repository's commit history since the last tag (or full history when no tags exist).

## Usage

### Option A: Invoke via Claude Code Slash Command
```text
/generate-changelog
```
When invoked, run:
```bash
python3 skills/generate-changelog/changelog.py --repo . --output CHANGELOG.md
```

### Option B: Run via Bash CLI
```bash
bash skills/generate-changelog/changelog.sh --repo . --output CHANGELOG.md
```

## Categorization Rules
Commits are parsed using Conventional Commits prefixes and semantic action verbs:
- **Added**: `feat`, `add`, `new`, `introduce`, `implement`, `support`, `create`
- **Fixed**: `fix`, `bug`, `hotfix`, `resolve`, `patch`, `repair`, `correct`
- **Changed**: `change`, `refactor`, `perf`, `update`, `upgrade`, `enhance`, `improve`, `docs`, `chore`, `style`, `build`, `ci`
- **Removed**: `remove`, `delete`, `drop`, `deprecate`, `prune`, `uninstall`

## Options
- `--repo <path>`: Path to target Git repository (default: `.`)
- `--since-tag <tag>`: Override base tag (default: latest reachable git tag via `git describe --tags --abbrev=0`)
- `--version <ver>`: Version header label for the generated section (default: `Unreleased`)
- `--output <file>`: Output markdown path (default: `CHANGELOG.md`, or `-` for stdout)
