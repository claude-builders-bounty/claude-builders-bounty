---
name: generate-changelog
description: Generate or update a structured CHANGELOG.md from this repository's git history, categorized into Added/Fixed/Changed/Removed since the latest tag.
---

# Generate Changelog

Generates (or updates) `CHANGELOG.md` at the repository root from real git
history — never invented content. All logic lives in `changelog.sh`, a
deterministic Bash script; this skill just drives it and reports the result.

## When to use this skill

The user asks to generate, update, or refresh a changelog, or invokes
`/generate-changelog`.

## What to do

1. Confirm the current directory is inside a git work tree. If not, tell the
   user this only works inside a git repository and stop.
2. Run the generator from the repository root:
   ```bash
   bash .claude/skills/generate-changelog/changelog.sh
   ```
3. Report exactly what the script printed: the commit range it analyzed
   (latest tag → HEAD, or "no tags found" full history), and the per-category
   counts (Added/Fixed/Changed/Removed) it wrote.
4. If it printed "No commits found...", tell the user that plainly — do not
   invent entries or edit `CHANGELOG.md` yourself.
5. Show the user the resulting `## Unreleased` section of `CHANGELOG.md` so
   they can review it.

## Rules

- Never write to `CHANGELOG.md` by hand — only `changelog.sh` should touch
  it, so the output stays deterministic and auditable from git history.
- Never fabricate commits, authors, issue numbers, or release notes that
  aren't literally present in `git log`.
- Existing release sections in `CHANGELOG.md` (anything under a `## `
  heading other than `## Unreleased`) must never be edited or removed —
  the script already preserves them; do not "clean up" or rewrite them.
- Running the skill multiple times with no new commits is safe and
  idempotent — it will not duplicate entries.

See `README.md` in this directory for full behavior details (tag detection,
categorization rules, no-tag fallback) and `tests/test_changelog.sh` for the
test suite covering these behaviors.
