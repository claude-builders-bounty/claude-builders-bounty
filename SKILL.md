---
name: generate-changelog
description: Generate a structured CHANGELOG.md from the project's git history. Use when the user asks to create or update a changelog, or runs /generate-changelog.
---

# Generate Changelog

Creates a structured `CHANGELOG.md` from git history, categorized by Conventional Commits.

## When to use
- User asks to "generate changelog", "update changelog", "create CHANGELOG.md"
- User runs the `/generate-changelog` command

## Steps

1. **Check git history availability** — confirm the working directory is a git repo:
   ```bash
   git rev-parse --is-inside-work-tree
   ```
   If not a repo, stop and tell the user.

2. **Run the generator**:
   ```bash
   bash changelog.sh
   ```
   This writes `CHANGELOG.md` in the current directory.

3. **Verify the output** — show the user the generated file:
   ```bash
   cat CHANGELOG.md
   ```
   Confirm it contains sections (Added / Fixed / Changed / Removed) and the commit count looks sane.

## Options
- `bash changelog.sh --stdout` — print to stdout instead of writing the file
- `bash changelog.sh --since <tag>` — only commits after a specific tag

## Rules
- Categorization follows Conventional Commits: `feat:` → Added, `fix:` → Fixed, `refactor:`/`chore:`/`docs:`/`test:`/`perf:`/`style:`/`build:`/`ci:` → Changed, `revert:`/`remove:`/`delete:` → Removed, `security:` → Security, `deprecate:` → Deprecated
- Commits without a type prefix go to Changed
- Merge commits are skipped
- If there are no commits in range, the script reports it and exits cleanly
