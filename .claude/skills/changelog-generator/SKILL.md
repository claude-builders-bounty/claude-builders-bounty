---
name: changelog-generator
description: Automatically generate a structured CHANGELOG.md from a project's git history — fetches commits, categorizes by type (Added/Fixed/Changed/Removed), and writes a markdown file.
allowed-tools: Bash(bash:*) Bash(git:*)
---

# Changelog Generator

Generate a structured `CHANGELOG.md` from your project's git history. Commits are auto-categorized using conventional commit prefixes.

## Workflow

1. Run `/generate-changelog` in the project root
2. The skill fetches commits since the last tag, categorizes them, and writes `CHANGELOG.md`
3. Review and commit the generated file

## Command

### `/generate-changelog`