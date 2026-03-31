---
name: generate-changelog
description: >
  Automatically generate a structured CHANGELOG.md from the current
  repository's git history. Categorises commits into Added / Fixed /
  Changed / Removed following the Keep a Changelog convention.
trigger: /generate-changelog
---

# SKILL: Generate CHANGELOG from Git History

## What this skill does

When you run `/generate-changelog`, Claude will:

1. Determine the last git tag (or use the full history if no tags exist).
2. Fetch all commits since that tag, skipping merge commits.
3. Auto-categorise each commit into one of four groups using its subject line:
   - **✨ Added** — `feat`, `add`, `new`, `create`, `implement`, `init` prefixes
   - **🐛 Fixed** — `fix`, `bug`, `patch`, `hotfix`, `resolve`, `close` prefixes
   - **🔄 Changed** — `refactor`, `perf`, `style`, `docs`, `test`, `ci`, `chore`, `update`, `improve`, `bump`, `change` prefixes
   - **🗑️ Removed** — `remove`, `delete`, `drop`, `clean` prefixes
4. Output a properly formatted `CHANGELOG.md` in the repository root.

## Usage

### Option A — Claude Code command (this skill)
```
/generate-changelog
```
Claude will run the generation and show you a preview before writing the file.

### Option B — Standalone bash script
```bash
bash changelog.sh                        # uses last git tag automatically
bash changelog.sh --since v1.2.0         # start from a specific tag
bash changelog.sh --output MY_CHANGES.md # custom output file
```

## Step-by-step instructions for Claude

When the `/generate-changelog` command is triggered:

1. **Check prerequisites**
   ```bash
   git rev-parse --is-inside-work-tree
   ```
   If not inside a git repo, tell the user and stop.

2. **Find last tag**
   ```bash
   LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
   ```
   If no tags exist, process the entire commit history and note it in the output.

3. **Collect commits since last tag**
   ```bash
   git log "${LAST_TAG}..HEAD" --pretty=format:"%h %s" --no-merges
   # If LAST_TAG is empty:
   git log HEAD --pretty=format:"%h %s" --no-merges
   ```

4. **Categorise each commit subject** using these keyword rules (case-insensitive):
   | Category | Keywords to match at start of subject |
   |----------|--------------------------------------|
   | Added    | feat, add, new, create, implement, init |
   | Fixed    | fix, bug, patch, hotfix, resolve, close |
   | Changed  | refactor, perf, style, docs, test, ci, chore, update, improve, bump, change |
   | Removed  | remove, delete, drop, clean |
   | Other    | anything else |

5. **Write CHANGELOG.md** using this template:
   ```markdown
   # Changelog

   All notable changes to this project will be documented in this file.
   Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

   ---

   ## [Unreleased] — YYYY-MM-DD

   > Changes since `<last-tag>`

   ### ✨ Added
   - <subject> (`<hash>`)

   ### 🐛 Fixed
   - <subject> (`<hash>`)

   ### 🔄 Changed
   - <subject> (`<hash>`)

   ### 🗑️ Removed
   - <subject> (`<hash>`)
   ```
   Omit any section that has zero entries.

6. **Confirm** — tell the user: "CHANGELOG.md has been written with N commits categorised."

## Notes

- Merge commits are always skipped (`--no-merges`).
- The script auto-bumps the patch version (e.g. `v1.2.3 → v1.2.4`) when the last tag follows semver.
- Works with any language / stack; no dependencies beyond `git` and `bash`.
