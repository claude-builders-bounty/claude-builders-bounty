---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag (Added/Fixed/Changed/Removed).
---

# Generate Changelog

## When to use
- User asks for a changelog, release notes, or `/generate-changelog`
- Preparing a release after commits landed since the last git tag

## Steps
1. Ensure cwd is the target git repository (or pass `--repo`).
2. Run:
   ```bash
   python3 bounty1/generate_changelog.py
   # or
   bash bounty1/changelog.sh
   ```
3. Review `CHANGELOG.md` and edit wording if needed before tagging.

## Rules
- Prefer Conventional Commit types (`feat`, `fix`, `chore`, …).
- Merge commits are skipped.
- Empty ranges produce an explicit “No commits” stub.
