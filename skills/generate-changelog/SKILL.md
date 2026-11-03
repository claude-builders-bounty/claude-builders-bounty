---
name: generate-changelog
description: Generate a categorized CHANGELOG.md from the git history since the last tag
---

# Generate a changelog

Run `skills/generate-changelog/changelog.sh` to turn a repository's git history into a
categorized `CHANGELOG.md`. The script needs only git and bash.

## What it does

- Takes the commits **since the most recent tag** (`--from <ref>` to override; when no
  tag exists the whole history is used).
- Sorts each commit into **Added / Fixed / Changed / Removed**:
  - Conventional Commit prefixes (`feat:`, `fix:`, `revert:`, `refactor:`, `chore:`, …)
    map directly; scopes are stripped and `type!:` entries are flagged as breaking.
  - Plain-language messages are classified by leading verb/keyword
    (add, fix, resolve, remove, drop, …).
- Skips merge commits and duplicate subjects, and writes a
  [Keep a Changelog](https://keepachangelog.com/) style file with short commit hashes.

## How to use it

```bash
bash skills/generate-changelog/changelog.sh                    # commits since the last tag
bash skills/generate-changelog/changelog.sh --from v1.2.0      # commits since v1.2.0
bash skills/generate-changelog/changelog.sh --out docs/CHANGELOG.md
bash skills/generate-changelog/tests/test_changelog.sh         # self-contained test suite
```

Flags: `--repo <path>`, `--from <ref>`, `--out <file>`.

## When generating for a user

1. Run the script in their repository; read the summary line it prints on stderr.
2. Read the generated file. If a category is empty the script omits it — do not add
   empty headings back.
3. Entries are the commit subjects, cleaned up (prefix stripped, first letter
   capitalised, trailing period dropped) with a short hash for traceability. Rewrite
   an entry only when its subject is genuinely uninformative, and keep the short hash.
4. The section is titled `Unreleased` by default. If the user is releasing a specific
   version, ask them for the version number and date and retitle the section
   accordingly (e.g. `## [1.2.3] - 2026-11-03`) — do not invent a version number.
5. If the repository has no tags, the full history lands under `Unreleased`; tell the
   user and suggest tagging a release to scope future runs.

See `examples/SAMPLE_CHANGELOG.md` for real output from
`anthropics/anthropic-sdk-python` (commits since `v2.3.0`).
