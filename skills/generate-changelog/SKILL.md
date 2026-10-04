---
name: generate-changelog
description: >-
  Generate a structured CHANGELOG.md from git history since the latest tag.
  Use when the user runs /generate-changelog or asks to build a changelog from commits.
allowed-tools: Bash(changelog.sh:*), Bash(git:*), Read, Write
---

# Generate Changelog

Build or refresh `CHANGELOG.md` from git commits since the most recent tag.

## When invoked (`/generate-changelog`)

1. Resolve the repository root (current project directory unless the user passed a path).
2. Run the bundled script from this skill directory:

   ```bash
   bash "$(dirname "$0")/changelog.sh" .
   ```

   If this skill lives at `.claude/skills/generate-changelog/SKILL.md`, use:

   ```bash
   bash .claude/skills/generate-changelog/changelog.sh .
   ```

3. Read the generated `CHANGELOG.md` and show the user a short summary (commit count per section: Added, Fixed, Changed, Removed).
4. If git reports no tags, note that all branch commits were included (expected behavior).

## Script behavior (do not reimplement by hand)

- Range: `latest_tag..HEAD`, or all commits on the branch when no tags exist.
- Categories: **Added**, **Fixed**, **Changed**, **Removed** (conventional commits + keyword heuristics).
- Output: Keep a Changelog–style `## [Unreleased]` with `###` sections.

## Options

Pass through script flags when the user asks:

- `-f` / `--stdout` — print instead of writing `CHANGELOG.md`
- `-o PATH` — custom output path
- `REPO_PATH` — generate for another checkout
