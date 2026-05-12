# Bounty #1 — Changelog Generator

Closes #1

/opire try #1

## What this is

A bash script + Claude Code skill that generates a structured `CHANGELOG.md` from git history, categorizing commits into **Added / Fixed / Changed / Removed / Other** sections.

## Setup (3 steps)

```bash
# 1. Download
curl -sO https://raw.githubusercontent.com/dot-Justin/claude-builders-bounty/main/bounties/001-changelog-generator/changelog.sh

# 2. Make executable
chmod +x changelog.sh

# 3. Run in any git repo
./changelog.sh
```

## Usage

```bash
# Auto-detect last tag (default)
bash changelog.sh

# Start from a specific tag
bash changelog.sh --from v1.2.0

# Custom output file
bash changelog.sh --output RELEASE_NOTES.md
```

## Claude Code skill

Install `SKILL.md` as a Claude Code skill to use `/generate-changelog` in any project:

```bash
mkdir -p ~/.claude/skills
cp SKILL.md ~/.claude/skills/generate-changelog.md
```

Then in Claude Code: `/generate-changelog`

## How it categorizes

| Output Section | Triggers |
|----------------|----------|
| **Added**   | `feat:`, `feature:` prefix · or message contains: *add, new, implement, create* |
| **Fixed**   | `fix:`, `bugfix:`, `hotfix:` · or: *fix, resolve, patch, correct, bug, crash* |
| **Changed** | `refactor:`, `perf:`, `style:`, `update:` · or: *update, refactor, improve, optimize, rename* |
| **Removed** | `remove:`, `deprecate:` · or: *remove, delete, deprecate, drop* |
| **Other**   | `chore:`, `ci:`, `build:`, `docs:`, `test:` · everything else |

## Key features

- **Zero dependencies** — pure bash + git, no npm, no API keys
- **Idempotent** — re-running replaces the `[Unreleased]` section, never duplicates it
- **Tested on a real repo** — see `SAMPLE_OUTPUT.md` (eslint-plugin-unicorn)
- **Merge commits excluded** automatically via `--no-merges`
- **Claude Code skill included** — works via `/generate-changelog` command

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Works via `/generate-changelog` or `bash changelog.sh` | ✅ both |
| Fetches commits since last git tag | ✅ auto-detects |
| Categorizes: Added / Fixed / Changed / Removed | ✅ + Other |
| Outputs formatted `CHANGELOG.md` | ✅ |
| Tested on a real GitHub repo (`SAMPLE_OUTPUT.md`) | ✅ eslint-plugin-unicorn |
| README with setup in ≤ 3 steps | ✅ |
