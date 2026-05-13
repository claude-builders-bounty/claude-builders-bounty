---
description: Generate a structured CHANGELOG.md from git history since the last tag. Use when the user asks to create or update release notes/changelog for the current repo.
disable-model-invocation: true
argument-hint: "[--since <tag>] [--output <path>]"
---

## Generate CHANGELOG

This skill generates a `CHANGELOG.md` for the current git repository by categorizing commit subjects since the last tag into **Added / Fixed / Changed / Removed**.

### Run

```!
set -euo pipefail

# From repo root:
bash "${CLAUDE_SKILL_DIR}/../../../changelog.sh" $ARGUMENTS
```

### After running

- If `CHANGELOG.md` was created/updated successfully, briefly summarize what changed (counts per section and the inferred range).
- If the repo has no tags, note that the changelog is generated from the full history.

### Files

- Script: `changelog.sh` (repo root)
- Implementation: `scripts/generate_changelog.py`
- Example output: `examples/CHANGELOG.sample.md`

