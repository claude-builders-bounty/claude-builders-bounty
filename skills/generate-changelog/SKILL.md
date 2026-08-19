---
name: generate-changelog
description: Generate or update CHANGELOG.md from git history since the last tag, grouped into Added/Changed/Deprecated/Removed/Fixed/Security in Keep a Changelog format. Use when the user asks to write, update, cut, or preview a changelog or release notes.
allowed-tools: Bash, Read, Edit
---

# Generate a CHANGELOG from git history

`changelog.sh` (next to this file) does the mechanical work: it reads the commits
between the last tag and `HEAD`, drops housekeeping commits, and writes a Keep a
Changelog section into `CHANGELOG.md`. Your job is to run it, then make the
result read like release notes a human wrote.

## Steps

1. **Preview first.** Never write straight to the file:

   ```bash
   bash .claude/skills/generate-changelog/changelog.sh --stdout
   ```

   Add `--version 1.4.0` to cut a dated release, or `--since v1.2.0` to override
   the range. `--all` keeps `docs`/`chore`/`ci`/`build`/`test` commits, which are
   dropped by default. `--help` lists everything.

2. **Read the preview before showing it.** The script categorizes by commit type
   and, for repos that don't use Conventional Commits, by the subject's leading
   verb — so check for:
   - entries in the wrong section (a `refactor:` that actually removed a feature)
   - subjects written for reviewers rather than users ("wip", "address feedback",
     "fix tests") — either rewrite them for the reader or drop them
   - a change that shipped across several commits and should be one bullet
   - anything user-visible that needs a `**BREAKING**` marker the commit lacked

   Fix these by editing the text, keeping the commit/PR link intact.

3. **Write it.** Re-run without `--stdout` to create or update the file, then
   apply your edits with `Edit`:

   ```bash
   bash .claude/skills/generate-changelog/changelog.sh --version 1.4.0
   ```

   The section is inserted above the newest existing release; the file's preamble
   and older releases are left alone. The script refuses to write a version that
   is already in the file — bump `--version` or edit that section by hand.

4. **Show the user what changed** — the section as written, plus a one-line note
   of any entry you rewrote or dropped, so they can push back.

## Notes

- No dependencies: bash, git, awk, sed. Safe to run in CI.
- With no tags in the repo the whole history is used and the section is titled
  `## [Unreleased]`.
- If the run prints `no changelog-worthy commits`, the range only contained
  housekeeping commits. Say so instead of inventing entries.
- Never write a changelog entry for work that isn't in the git history.
