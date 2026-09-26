---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Use when the user asks for a changelog, release notes draft, or a summary of recent commits.
---

# Generate Changelog

Build a Keep-a-Changelog style `CHANGELOG.md` from a repository's git history.

## How it works

1. Run the generator script against the target repo:
   ```bash
   bash changelog.sh --repo /path/to/repo
   ```
   This reads commits since the last git tag (or all history if no tag exists),
   categorizes each commit, and writes `CHANGELOG.md`.
2. Useful flags:
   - `--stdout` — print the markdown instead of writing the file
   - `--since v1.2.0` — start from a specific tag instead of the latest one
   - `--output NOTES.md` — write to a different file
3. Review the generated file, then commit it:
   ```bash
   git add CHANGELOG.md && git commit -m "docs: add generated changelog"
   ```

## Categorization rules

| Category  | Matched by (conventional prefix or keywords) |
|-----------|----------------------------------------------|
| Added     | `feat:`, add, new, implement, introduce, support |
| Fixed     | `fix:`, bug, patch, hotfix, resolve |
| Removed   | `remove:`, delete, drop, deprecate |
| Changed   | everything else (`refactor:`, `docs:`, `chore:`, …) |

Conventional-commit prefixes (e.g. `feat(api): …`) take precedence over
keyword matching. Merge commits are skipped.
