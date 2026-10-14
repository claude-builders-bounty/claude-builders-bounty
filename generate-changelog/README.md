# generate-changelog

Generate a structured `CHANGELOG.md` from a repository's git history since the
last tag. Works as a bash script or as a native Claude Code skill.

## Setup (2 steps)

1. Copy `changelog.sh` anywhere on your PATH (or run it in place):

   ```bash
   cp changelog.sh /usr/local/bin/changelog.sh
   ```

2. Run it against any git repository:

   ```bash
   bash changelog.sh /path/to/repo        # writes CHANGELOG.md in that repo
   CHANGELOG_OUTPUT=NOTES.md bash changelog.sh /path/to/repo   # custom output path
   ```

As a Claude Code skill: drop the `SKILL.md` + `changelog.sh` pair into your
skills directory and invoke `/generate-changelog`.

## What it does

- **Range**: commits since the last git tag; full history when no tags exist
- **Filtering**: skips merge commits and version-bump commits (`bump version`,
  `release v1.2.3`, `version bump`)
- **Categorization**: conventional-commit aware —
  `feat` → Added, `fix` → Fixed, `refactor`/`perf`/`style`/`chore`/`docs`/`test`/
  `build`/`ci` → Changed, `revert`/`remove`/`deprecate` → Removed; a keyword
  fallback classifies non-conventional messages (`add…`, `fix…`, `remove…`)
- **Format**: Keep a Changelog. Each entry carries the short hash, author, date
- **Idempotent**: re-running replaces the living `## Unreleased` section;
  released sections are never modified

## Tested on

- `aeternity/sophia-tmlanguage` — no-tags path (full history)
- `NousResearch/hermes-agent` — since-tag path (56 commits since
  `rc.11-v0.21.7`), sample output in `examples/sample-changelog.md`

See `examples/PROVENANCE.md` for the exact test methodology.

## Files

- `changelog.sh` — the generator (bash, no dependencies beyond git + coreutils)
- `SKILL.md` — Claude Code skill wrapper
- `examples/sample-changelog.md` — real generated output from the hermes-agent test
- `examples/PROVENANCE.md` — test methodology
