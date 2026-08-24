---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Use when the user asks for a changelog, release notes, or /generate-changelog.
---

# Generate Changelog

Create or update `CHANGELOG.md` from the current repo's git history.

## Steps

1. Confirm cwd is a git repo: `git rev-parse --show-toplevel`. If not, stop and tell the user.
2. Run the bundled script: `bash changelog.sh` (script lives next to this SKILL.md).
3. Read the generated `CHANGELOG.md` back and show the user the new section.
4. If the user wants a release entry instead of `[Unreleased]`, ask for the version tag, then rename the section header to `## [vX.Y.Z] — <date>`.

## Rules

- Never rewrite or delete sections below the one just generated; the script prepends only.
- Categorization is keyword-based on commit subjects: feat/add → Added, fix/bug → Fixed, remove/delete → Removed, everything else → Changed. If the user disputes a category, move the line manually after generation.
- Merges are excluded. If the user wants merges included, edit the script's `--no-merges` flag.
