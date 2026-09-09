---
name: generate-changelog
description: Generate a structured CHANGELOG.md (Added / Fixed / Changed / Removed) from git history since the last tag. Use when the user asks to create, update, or regenerate a changelog.
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from the repository's git history.

## When to use

- The user asks to "create / update / regenerate a changelog"
- A release is being prepared and release notes are needed
- The repository has no `CHANGELOG.md` yet, or it is stale

## Steps

1. Confirm you are inside a git repository:

   ```bash
   git rev-parse --show-toplevel
   ```

2. Run the generator script (optionally pass an output path):

   ```bash
   bash changelog-skill/changelog.sh [OUTPUT_FILE]
   ```

   - Default output is `CHANGELOG.md` in the repository root.
   - The script reads commits since the **last git tag** (`git describe --tags --abbrev=0`). Repositories without tags fall back to full history.

3. Sanity-check the result:

   ```bash
   head -n 40 CHANGELOG.md
   ```

   - Sections with no commits are omitted automatically.
   - Commit subjects are categorized by conventional-commit prefix (`feat`, `fix`, `revert`, …) plus keyword fallbacks (`add`, `new`, `remove`, `delete`, …). Everything else lands in `Changed`.

## Notes

- Merge commits are excluded (`--no-merges`).
- The generated file keeps an `## Unreleased (since <tag>)` section; move its contents under a versioned heading when you cut a release.
- If categorization looks wrong for your project's commit style, adjust the `category()` function in `changelog.sh`.
