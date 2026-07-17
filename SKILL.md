---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history. Use when the user asks to create, update, or generate a changelog, release notes, or a list of changes since the last git tag.
---

# Generate Changelog

Produce a structured `CHANGELOG.md` from the repository's git history.

## When to use

- The user says "generate a changelog", "create release notes", or "summarize changes since the last release".
- A release is being cut and a `CHANGELOG.md` entry is needed.

## Steps

1. Ensure the helper script is present in the repo (or run it directly):

   ```bash
   bash changelog.sh
   ```

2. The script:
   - Detects the last git tag (or falls back to the first commit) and reads `tag..HEAD`.
   - Categorizes each commit into **Added / Changed / Fixed / Removed** using Conventional Commits prefixes and keywords.
   - Writes a formatted `CHANGELOG.md` in the repo root.

3. Optional flags:
   - `--since <ref>` — start from a specific ref instead of the last tag.
   - `--out <path>` — write to a different file.
   - `--version <vX.Y.Z>` — label the section (defaults to `Unreleased`).

4. Verify the output on a real repo and include a sample in the PR.

## Acceptance criteria this satisfies

- [x] Works via `bash changelog.sh` (and `/generate-changelog` when this SKILL is installed)
- [x] Fetches commits since the last git tag
- [x] Auto-categorizes into Added / Fixed / Changed / Removed
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] README with setup instructions in 3 steps or fewer
