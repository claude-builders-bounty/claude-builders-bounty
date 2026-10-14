# generate-changelog

Generate a structured `CHANGELOG.md` from git history — commits since the
last tag, auto-categorized **Added / Changed / Deprecated / Removed /
Fixed / Security** in [Keep a Changelog](https://keepachangelog.com)
format, with version headings, dates, and compare links when a git remote
exists.

Ships in both accepted forms:

- **`SKILL.md`** — a native Claude Code skill; invoking `/generate-changelog`
  in Claude Code runs the workflow.
- **`changelog.sh`** — the standalone engine; pure bash + git, no other
  dependencies, no network use.

## Setup (3 steps)

1. Copy this folder where you want it: for the Claude Code skill, place it
   at `.claude/skills/generate-changelog/` in your project (or
   `~/.claude/skills/generate-changelog/` for all projects). For script-only
   use, put `changelog.sh` anywhere.
2. There is no step 2 for dependencies — if `git` and `bash` exist, it runs.
   (Optional: `chmod +x changelog.sh`.)
3. From your project's root, run it:

   ```bash
   bash changelog.sh                      # Unreleased section, commits since last tag
   bash changelog.sh --version 1.4.0      # release section for v1.4.0
   bash changelog.sh --all                # full history, one section per tag
   ```

   In Claude Code, just type `/generate-changelog`.

## How it categorizes

Conventional Commit prefixes win: `feat` → Added, `fix` → Fixed,
`perf`/`refactor`/`docs`/`chore`/… → Changed, `security` → Security,
`deprecate` → Deprecated, `remove` → Removed. Messy, non-conventional
subjects fall back to keyword rules (`Add …`, `Fixed …`, `Remove …`, …) and
land in Changed when nothing matches. `!` markers and `BREAKING CHANGE:`
footers flag an entry **BREAKING:**. Merge commits, bare version subjects,
and duplicates are skipped.

Re-running is safe: the script inserts the new section under your existing
changelog's preamble, refreshes the compare-link references, and refuses
to create a duplicate section for the same version (use `--overwrite` to
regenerate from scratch).

## Sample output

[`examples/sample-changelog.md`](examples/sample-changelog.md) is real
output from this script. Its provenance — which repository and tag range
produced it — is recorded in
[`examples/PROVENANCE.md`](examples/PROVENANCE.md).
