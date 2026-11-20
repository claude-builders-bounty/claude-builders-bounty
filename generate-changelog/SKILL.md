---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag, auto-categorized into Added / Fixed / Changed / Removed. Use when asked to generate or update a changelog, write release notes, or summarize recent commits.
---

# Generate Changelog

1. Run the generator from the repository root:

   ```bash
   bash generate-changelog/changelog.sh -o CHANGELOG.md
   ```

2. Read the generated `CHANGELOG.md`. The script categorizes purely from commit
   messages, so re-verify anything that landed in `Changed` but looks user-facing:
   inspect the diff with `git show <sha>` and move the bullet to the right section
   (`Added` / `Fixed` / `Changed` / `Removed`) when the code says something the
   subject line does not.

3. Rewrite each bullet as a one-line, user-facing summary. Keep the `(sha)`
   reference at the end of every bullet — it is the audit trail back to the commit.

4. If the release is happening now, rename `## [Unreleased] (YYYY-MM-DD)` to
   `## [x.y.z] - YYYY-MM-DD` (Keep a Changelog format).

Extra options: `--since <ref>` to start at an older ref instead of the newest tag,
`--no-tag` for full history, `-o <file>` for another output path, `-f` to overwrite
a hand-written changelog. If the repo has no tags yet, every commit is included.
