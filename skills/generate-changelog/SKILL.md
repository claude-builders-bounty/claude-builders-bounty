---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag (Added/Fixed/Changed/Removed).
---

# generate-changelog

## When to use
User asks for a changelog, release notes from commits, or runs `/generate-changelog`.

## Steps
1. Run `bash scripts/changelog.sh` from the repo root (or pass `REPO_DIR=` and optional `SINCE_REF=`).
2. Read the printed CHANGELOG section and the written `CHANGELOG.md` (or `--stdout-only`).
3. If no tags exist, the script uses the first commit as the lower bound and notes that in the header.
4. Verify categories look right; lightly edit only if a commit is clearly miscategorized.

## Command
```bash
bash scripts/changelog.sh
# or
bash scripts/changelog.sh --stdout-only
SINCE_REF=v1.0.0 bash scripts/changelog.sh
```

## Acceptance mapping
- Commits since last git tag
- Categories: Added / Fixed / Changed / Removed
- Formatted CHANGELOG.md
