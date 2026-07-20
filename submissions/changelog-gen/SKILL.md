# SKILL.md — /generate-changelog

## Description
Generate a structured CHANGELOG.md from the project's git history, auto-categorized into Added, Fixed, Changed, and Removed sections.

## Trigger
User says: "generate changelog", "create changelog", "update changelog", or runs `/generate-changelog`

## Instructions

1. Run `bash changelog.sh` in the project root
   - It auto-detects the last git tag
   - Categorizes all commits since that tag
   - Outputs to `CHANGELOG.md`

2. If no `changelog.sh` exists:
   - Ask if the user wants you to create it from the template
   - Read the project's `git log` since last tag
   - Categorize commits manually using the same rules:
     - `add/feat/new/create/implement` → Added
     - `fix/bug/resolve/patch/repair` → Fixed
     - `change/update/refactor/improve/upgrade` → Changed
     - `remove/delete/drop/deprecate` → Removed
   - Write to `CHANGELOG.md`

3. Confirm completion:
   - Report: "✅ Generated CHANGELOG.md with X commits (A added, F fixed, C changed, R removed)"
   - Show a preview of the first 5 entries

## Files
- `changelog.sh` — Standalone bash script (recommended)
- This `SKILL.md` — Claude Code integration
