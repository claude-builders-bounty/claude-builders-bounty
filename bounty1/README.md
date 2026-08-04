# Bounty #1 — Generate structured CHANGELOG from git history

**Reward:** $50 (Opire) · **Issue:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1

## Setup (3 steps)

1. Copy `bounty1/` into your project (or clone this repo).
2. From the target git repo run:
   ```bash
   bash path/to/bounty1/changelog.sh
   # or: python3 path/to/bounty1/generate_changelog.py
   ```
3. Open the generated `CHANGELOG.md`.

Optional Claude Code skill: place `SKILL.md` under `.claude/skills/generate-changelog/`.

## What it does

- Reads commits **since the last git tag** (or all history if untagged)
- Categorizes into **Added / Fixed / Changed / Removed** (+ Other)
- Uses Conventional Commits when present; falls back to subject heuristics
- Writes/merges a Keep-a-Changelog-style `CHANGELOG.md`

## Test

```bash
python3 bounty1/tests/test_generate_changelog.py
```

## Sample output

See `bounty1/samples/CHANGELOG.sample.md` (generated against this repository).
