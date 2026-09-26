---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from a project's git history. Categories commits into Added / Fixed / Changed / Removed since the last git tag. Use when the user asks to build, update, or regenerate a changelog, or runs /generate-changelog."
---

# Skill: generate-changelog

Generates a Keep-a-Changelog style `CHANGELOG.md` from the git history of the current repository.

## When to use

- The user asks to create/regenerate a `CHANGELOG.md`.
- The user invokes `/generate-changelog`.
- You are preparing a release note and want the summary of changes since the last tag.

## How to run

Run one of the scripts in this skill's directory inside the target git repo:

- **Python** (cross-platform, recommended):
  `python changelog.py [project_dir] [output_file]`

- **Bash** (Linux/macOS/Git-Bash):
  `bash changelog.sh [project_dir] [output_file]`

- **PowerShell** (Windows):
  `powershell -ExecutionPolicy Bypass -File changelog.ps1 -ProjectDir <dir> -Output CHANGELOG.md`

All three scripts do the same thing:

1. Detect the last git tag (falls back to full history if there are no tags).
2. Fetch commits since that tag.
3. Classify each commit by Conventional Commit prefix:
   - `feat|feature|add|new` → **Added**
   - `fix|bugfix|bug|hotfix|patch` → **Fixed**
   - `remove|delete|drop|deprecate|breaking` → **Removed**
   - anything else (refactor, chore, docs, test, perf, build, ci…) → **Changed**
4. Write a `CHANGELOG.md` with `## [Unreleased]` sections grouped by category.

## Verification

After generating, confirm the file contains the four category sections and
that the commit list matches the output of `git log <last-tag>..HEAD --oneline`.

Tested with commits like `feat(api): ...`, `fix: ...`, `refactor: ...`,
`remove: ...`, `refactor!: ...` (breaking → Removed) and on a repo with no tags
(falls back to full history).

## Notes

- The scripts never modify git state; they only read history and write the output file.
- If no tags exist, the range covers the entire history.