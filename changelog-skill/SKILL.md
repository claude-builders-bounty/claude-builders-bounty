---
name: changelog-generator
description: Generate a structured CHANGELOG.md (Added/Fixed/Changed/Removed) from git history since the last tag. Use when asked to write a changelog or summarize recent commits.
allowed-tools: Bash
---

# Changelog Generator Skill

## What it does
Reads `git log` since the last tag (or `--since`), classifies subjects by
conventional-commit prefix into Added/Fixed/Changed/Removed, writes `CHANGELOG.md`.

## Usage
```bash
bash changelog.sh
bash changelog.sh --since v1.2.0 --out CHANGELOG.md --repo /path/to/repo
```

## Classification
- `feat/add/new` → Added · `fix/bug/hotfix/patch` → Fixed
- `remove/delete/drop/deprecat` → Removed · everything else → Changed

## Rules
- Read-only on git history; only file written is the output changelog.
- Subjects go verbatim into bullets — never invent entries.
