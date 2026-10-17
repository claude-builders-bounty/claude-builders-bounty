---
name: changelog
description: Generate a structured CHANGELOG.md entry (Keep a Changelog format) from git history. Use when asked to write release notes, a changelog, or summarize commits between two refs.
---

Generate a Keep a Changelog (https://keepachangelog.com) entry from git history.

## Procedure

1. Determine the range. Default: commits since the last git tag
   (`git describe --tags --abbrev=0`). Accept an explicit range
   (`v1.2.0..HEAD`) or count (`-n 50`) if the user gives one.
2. Collect commits: `git log --format="%s | %an | %h" <range>` plus
   `git log --format="%b" <range>` for bodies (BREAKING CHANGE footers).
3. Classify each commit into exactly one section, in this order:
   - `### Breaking` — `BREAKING CHANGE` in body, `!:` in subject, or API/ABI removal
   - `### Added` — new features, endpoints, commands, files users call
   - `### Changed` — behavior changes to existing features (incl. dependency bumps)
   - `### Removed` — deleted features, dropped options/platforms/py-versions
   - `### Fixed` — bug fixes ("fix", "correct", "stop", "prevent")
   - `### Internal` — tests, refactors, CI, docs with no user-visible change
4. Write the entry:

   ```markdown
   ## [X.Y.Z] — YYYY-MM-DD

   ### Added
   - One-line summary (`abc1234`)
   ...
   ```

   Rules per bullet: imperative voice, user-visible effect first, short hash in
   parens, PR/issue numbers kept when present in the subject. Merge commits:
   credit the branch's work, skip the merge itself unless it IS the feature.
5. Empty sections are omitted entirely. Prepend to CHANGELOG.md if it exists
   (preserving its header); otherwise create it with the standard header.

## Judgment rules

- A subject like "tests: pin fixture" is Internal even if it touched code.
- "Merge task/X" carries no user meaning — mine the branch commits' subjects.
- When a commit is genuinely ambiguous, place it under `### Changed`, never
  invent an "Added" claim.
- If the range has 0 commits, say so — do not fabricate an empty release.
