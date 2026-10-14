---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag, auto-categorized into Added / Fixed / Changed / Removed (Keep a Changelog format). Use when the user asks to generate a changelog, draft release notes, or summarize what changed since the last release or tag.
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from the current repo's git history using the bundled `changelog.sh` script (bash + git only, no other dependencies).

## Steps

1. **Locate the script.** `changelog.sh` lives in the same directory as this SKILL.md. Refer to it by that absolute path in every command below.

2. **Run the generator.** From the root of the target git repo:

   ```bash
   bash <skill-dir>/changelog.sh
   ```

   This defaults to: commits since the last git tag reachable from `HEAD` (if no tag exists, all commits from the root commit — the script prints which range it used), output to `CHANGELOG.md` in the repo root, version header `Unreleased` with today's date.

   Useful options when the user wants something specific:

   | Option | Meaning |
   |---|---|
   | `--from <ref>` | Start ref (default: last tag) |
   | `--to <ref>` | End ref (default: `HEAD`) |
   | `--version <v>` | Version header, e.g. `--version 1.2.0` |
   | `--date <YYYY-MM-DD>` | Release date (default: today) |
   | `--output <file>` | Output path (default: `<repo>/CHANGELOG.md`) |
   | `--repo <path>` | Repo to read (default: current directory) |

   Example for a release: `bash <skill-dir>/changelog.sh --from v1.1.0 --to v1.2.0 --version 1.2.0`

3. **Present the results.** Read the generated `CHANGELOG.md` and show the user the categorized entries (Added / Fixed / Changed / Removed). Report the range the script used (it prints this to stderr, e.g. `since last tag v0.1.0` or the no-tag fallback) and the per-category counts. If the range was empty, say so plainly — the file will contain a "No changes in this range" note.

## How commits are categorized

- `feat:` → **Added**; `fix:` → **Fixed**; `remove`/`revert` types or remove/delete/drop/deprecate keywords → **Removed**
- `refactor`/`perf`/`style`/`chore`/`docs`/`test`/`build`/`ci` and everything else → **Changed**
- Non-conventional subjects are matched by keywords (`add`, `fix`, `remove`, …); anything unmatched lands in **Changed** — no commit is ever dropped silently
- Merge commits (subjects starting with `Merge `) are skipped
- Conventional prefixes/scopes are stripped from the output; PR/issue refs like `(#123)` are preserved

Full mapping and edge-case behavior are documented in `README.md` next to this file.
