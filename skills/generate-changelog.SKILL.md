---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, auto-categorizing commits into Added/Fixed/Changed/Removed sections since the last git tag. Works as a Claude Code skill (/generate-changelog) or standalone bash script.
trigger: /generate-changelog
---

# Generate CHANGELOG

Automatically generates a professional `CHANGELOG.md` from your project's git history,
grouping commits into conventional categories since the last git tag.

## Usage

### As a Claude Code Skill

```
/generate-changelog
```

### As a Standalone Script

```bash
bash skills/changelog.sh
```

Or from any directory:

```bash
/path/to/changelog.sh /path/to/your/repo
```

## What It Does

1. Finds the last git tag (or uses the initial commit if no tags exist)
2. Fetches all commits since that tag
3. Parses commit messages for conventional commit prefixes
4. Generates a formatted `CHANGELOG.md` with these sections:
   - **Added** — new features (`feat:`, `feature:`, `add:`, `implement:`)
   - **Fixed** — bug fixes (`fix:`, `bugfix:`, `bug:`, `hotfix:`)
   - **Changed** — refactors, upgrades, improvements (`refactor:`, `chore:`, `update:`, `upgrade:`)
   - **Removed** — deprecations, deletions (`remove:`, `deprecate:`, `delete:`)
5. Writes the result to `CHANGELOG.md` in the project root

## Acceptance Criteria Checklist

- [x] Works via `/generate-changelog` command or `bash changelog.sh`
- [x] Fetches commits since the last git tag
- [x] Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] Tested on a real GitHub repo (see sample below)
- [x] README with setup instructions in 3 steps or fewer
