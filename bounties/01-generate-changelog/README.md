# Generate structured CHANGELOG from git history

**Bounty:** #1 — $50 (Opire)

## Setup (3 steps)

1. Copy this folder into your repo (or keep the path).
2. Prefer `python3 changelog.py` (portable) **or** `bash changelog.sh` (Unix/Git Bash).
3. Run either command → writes `CHANGELOG.md` (optional path arg).

Claude Code skill: place `SKILL.md` under `.claude/skills/generate-changelog/` for `/generate-changelog`.

## What it does

- Commits **since the latest git tag** (or full history if untagged)
- Buckets subjects into **Added / Fixed / Changed / Removed**
- Writes a dated `CHANGELOG.md`

## Sample

See `sample-CHANGELOG.md` generated from this repository’s history.
