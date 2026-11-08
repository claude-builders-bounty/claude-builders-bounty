---
name: generate-changelog
description: Automatically generates a structured, categorized CHANGELOG.md adhering to Keep a Changelog standards from git commit history since the last release tag.
---

# Generate Changelog Skill

A skill for Claude Code to automatically audit git history and compile clean, categorized release notes.

## When to Use
Run `/generate-changelog` whenever:
- Preparing a new release or tag
- Reviewing work merged since the last deployment
- Updating the root `CHANGELOG.md` file

## Usage

### Direct Command
```bash
python scripts/generate_changelog.py --version "v1.0.0"
```

Or print directly to console without modifying files:
```bash
python scripts/generate_changelog.py --stdout
```

## How It Categorizes
- `feat:`, `feature:`, `add:` -> **Added**
- `fix:`, `bug:`, `patch:`, `resolve:` -> **Fixed**
- `security:`, `sec:`, `vuln:` -> **Security**
- `remove:`, `deprecate:` -> **Removed**
- `refactor:`, `perf:`, `chore:`, `update:` -> **Changed**
