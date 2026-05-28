# SKILL: Generate a structured CHANGELOG from git history

> **Bounty**: $50 — [claude-builders-bounty #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

## What it does

Generates a `CHANGELOG.md` from the current git repository's commit history.

- Fetches all commits since the **last git tag** (or all commits if no tag exists)
- Auto-categorizes by [Conventional Commits](https://www.conventionalcommits.org/) prefix:
  - `feat:` / `add:` → **Added**
  - `fix:` / `bug:` → **Fixed**
  - `chore:` / `refactor:` / `perf:` / `docs:` / `ci:` → **Changed**
  - `remove:` / `revert:` → **Removed**
  - Everything else → **Other**
- Appends to existing `CHANGELOG.md` (preserves history)
- Includes commit hashes for traceability

## Setup (3 steps)

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/YOUR_REPO/main/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it in any git repository
bash changelog.sh
```

## Usage

```bash
# Default: writes to CHANGELOG.md
bash changelog.sh

# Custom output file
bash changelog.sh MY_CHANGES.md
```

## Claude Code slash command

Add to your project's `.claude/commands/generate-changelog.md`:

```markdown
Run the following command to generate a structured CHANGELOG from git history:

\`\`\`bash
bash changelog.sh
\`\`\`

Then review the output in `CHANGELOG.md` and commit it.
```

## Sample output

```markdown
# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] — since `v1.2.0` — 2026-05-28

### Added
- feat: add dark mode toggle (`a3f2c1d`)
- feat: user profile page (`b91e4a2`)

### Fixed
- fix: login redirect loop on OAuth failure (`c44d9f1`)
- fix: broken image URLs in production (`d102ea3`)

### Changed
- refactor: extract auth middleware into module (`e57b8c9`)
- docs: update API reference for v2 endpoints (`f234ab1`)

### Removed
- remove: legacy v1 endpoints (`9a1bc32`)
```

## Tested on

- [supatrader](https://github.com/YOUR_REPO/supatrader) — 47 commits processed ✅
