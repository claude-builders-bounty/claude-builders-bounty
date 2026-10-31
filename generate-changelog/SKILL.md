---
name: Generate Changelog
description: Generate a structured CHANGELOG.md from git history. Use when the user asks to create or update a changelog, summarize recent commits, or prepare release notes.
---

# Generate Changelog

## Workflow

1. Run `bash scripts/generate-changelog.sh` from the repository root (add a tag name as the first argument to start from a specific tag, or `--output <file>` to change the destination).
2. Review the generated `CHANGELOG.md`:
   - Commits are auto-categorized into **Added / Fixed / Changed / Removed / Other** using conventional-commit prefixes (`feat:`, `fix:`, `chore:`, etc.) and keyword matching.
   - Merge commits are skipped; conventional prefixes and `(PR #N)` suffixes are stripped from entries.
3. If a section is wrong (a commit landed in the wrong bucket), edit the entry manually — the script is a first draft generator, not gospel.
4. Offer the user to commit the changelog, e.g. `git commit -am "docs: update CHANGELOG"`.

## Notes

- Requires `git` on PATH; works on bash 3.2+ (macOS default) and Linux.
- With no tags in the repository, the changelog covers the entire history.
- Re-running the script regenerates the file; it does not append. This is intentional to keep the output idempotent.
