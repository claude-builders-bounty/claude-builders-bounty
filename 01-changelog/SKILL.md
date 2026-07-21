# SKILL.md — Changelog Generator

## Description
Generate a structured CHANGELOG.md from git history. Categorizes commits into Added, Fixed, Changed, and Removed sections using conventional commit prefixes.

## Usage
Trigger this skill by typing `/generate-changelog` or running `bash changelog.sh`.

## Instructions
1. Run the `changelog.sh` script in the project root
2. The script auto-detects the last git tag and collects commits since then
3. Commits are categorized by prefix: feat/add → Added, fix/bug → Fixed, refactor/perf/style → Changed, remove/drop → Removed
4. Output is written to `CHANGELOG.md` in Keep a Changelog format
