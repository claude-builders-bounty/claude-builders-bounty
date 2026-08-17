# Changelog Generator

Generates a structured `CHANGELOG.md` from git history, auto-categorized into
**Added / Fixed / Changed / Removed**.

## Setup (3 steps)

```bash
cp changelog.sh /usr/local/bin/changelog.sh && chmod +x /usr/local/bin/changelog.sh
# (optional, Claude Code) copy SKILL.md into your project's .claude/skills/generate-changelog/
cd /your/repo && bash changelog.sh
```

## Usage

```bash
bash changelog.sh                # commits since last git tag
bash changelog.sh v1.2.0         # commits since tag/ref v1.2.0
bash changelog.sh --since HEAD~10
bash changelog.sh --output CHANGES.md
```

## How it works

- Finds the last git tag (`git describe --tags --abbrev=0`), falls back to the
  first commit if no tags exist.
- Reads commits via `git log --no-merges --format="%h|%s"`.
- Categorizes with conventional-commit prefixes:
  - `fix|bugfix|hotfix` → **Fixed**
  - `feat|feature|add|new` → **Added**
  - `refactor|perf|chore|build|docs|test|style` → **Changed**
  - `remove|delete|deprecate` → **Removed**
  - default → **Changed**
- Writes `CHANGELOG.md` with `## Added / ## Fixed / ## Changed / ## Removed` sections.

## Sample output

```markdown
# Changelog

Generated from `git log` since `v1.0.0` on 2026-08-17.

## Added
  - feat: add user profile page (`a1b2c3d`)

## Fixed
  - fix: resolve login redirect loop (`c7d8e9f`)

## Changed
  - refactor: extract auth middleware (`b0c1d2e`)

## Removed
  - remove: drop legacy API v1 (`f1a2b3c`)
```
