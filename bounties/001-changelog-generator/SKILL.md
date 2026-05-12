---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Categorizes commits into Added/Fixed/Changed/Removed sections using conventional commit prefixes and keyword heuristics. Run in any git repository.
---

# generate-changelog

Generate a structured `CHANGELOG.md` from the current repo's git history.

## What to do

1. Check if `changelog.sh` exists in the current directory. If not, ask the user to download it first.
2. Determine the commit range:
   - If the user specifies a starting tag, use `--from <tag>`
   - Otherwise, run without arguments (auto-detects the last git tag)
3. Run `bash changelog.sh` (optionally with `--from <tag>` or `--output <file>`)
4. Read the generated `CHANGELOG.md` and show the user a summary

## Examples

```bash
# Generate since last git tag (default)
bash changelog.sh

# Generate from a specific tag
bash changelog.sh --from v1.0.0

# Write to a custom output file
bash changelog.sh --output RELEASE_NOTES.md

# Generate all commits (no tags)
bash changelog.sh --from ""
```

## Categories

| Section | Conventional Prefix | Keyword Heuristic |
|---------|--------------------|--------------------|
| Added   | `feat:`, `feature:` | add, new, implement, create, introduce, support |
| Fixed   | `fix:`, `bugfix:`, `hotfix:` | fix, resolve, patch, correct, bug, crash |
| Changed | `refactor:`, `perf:`, `style:`, `change:`, `update:` | update, refactor, improve, optimize, rename, move |
| Removed | `remove:`, `deprecate:` | remove, delete, deprecate, drop |
| Other   | `chore:`, `ci:`, `build:`, `docs:`, `test:` | (everything else) |

## Notes

- Merge commits are excluded automatically (`--no-merges`)
- Re-running is idempotent — replaces the existing `[Unreleased]` section
- Works on any git repository with at least one commit
