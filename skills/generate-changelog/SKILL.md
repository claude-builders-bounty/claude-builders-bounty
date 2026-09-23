---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history. Auto-categorizes commits since the last git tag into Added / Fixed / Changed / Removed.
---

# Generate Changelog

When the user asks to generate or update a changelog (or invokes `/generate-changelog`):

1. Confirm you are at the repository root (`git rev-parse --show-toplevel`).
2. Run `bash scripts/changelog.sh [output-file]` (defaults to `CHANGELOG.md`).
3. Report back the commit count and which categories were populated.

## How it works

- **Range:** commits since the most recent git tag (`git describe --tags --abbrev=0`); the full history when the repo has no tags. Merge commits are skipped.
- **Categorization:**
  - `feat:` prefix, or keywords add / new / feature / introduce / implement / support / create → **Added**
  - `fix:` prefix, or keywords fix / bug / patch / hotfix / resolve / correct → **Fixed**
  - keywords remove / delete / deprecate → **Removed**
  - everything else (refactor, docs, chore, style, perf, update, ci) → **Changed**
- **Output:** Keep-a-Changelog style markdown under `## [Unreleased]`, one bullet per commit with its short hash.

## Notes

- Requires `git` and `bash`. No dependencies.
- If the repo has no tags, the script covers the entire history and says so in the output.
- Re-running overwrites the output file; commit it or back it up if you hand-edit entries.
