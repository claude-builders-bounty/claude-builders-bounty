---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history since the last tag. Use when the user asks for a changelog, release notes, "what changed since v1.2", or before tagging a release. Categorises commits into Added / Fixed / Changed / Removed and prepends the result to CHANGELOG.md.
allowed-tools: Bash(bash:*)
---

# Generate a changelog from git history

Turn `git log` output into a Keep-a-Changelog file — deterministically, without
calling a model per commit.

## Workflow

1. **Preview the range.** Never write to `CHANGELOG.md` before showing the user
   what will be added:

   ```bash
   bash scripts/changelog.sh --dry-run
   ```

   The script picks the range `$(git describe --tags --abbrev=0)..HEAD` for you.
   Pass `--from` / `--to` when the user names a specific release.

2. **Check the grouping.** If a commit landed in the wrong section, fix the
   commit message convention upstream rather than editing the script output:
   `feat: ...` → Added, `fix: ...` → Fixed, `perf|refactor|docs|test|chore: ...`
   → Changed, `remove|revert|deprecate: ...` → Removed. Unprefixed commits fall
   back to keyword matching (`add` / `fix` / `remove`), then default to Changed.

3. **Write the block.** Once the preview looks right:

   ```bash
   bash scripts/changelog.sh --version v2.1.0
   ```

   This prepends a `## [v2.1.0] - YYYY-MM-DD` block to `CHANGELOG.md`, keeping
   every existing entry below it. Use `--stdout` when the user wants the text
   in the reply (release notes, PR body) instead of a file edit.

## Rules

- **Never rewrite history to make the changelog nicer.** The generator reads the
  real log; squash messages and PR titles are the source of truth for a reason.
- **Skip nothing silently.** Commits that are dropped (version bumps, `Merge pull
  request #...`) are dropped because they add no user-facing information — say
  so if the user asks why a commit is missing.
- **One release per block.** Do not append several versions in one run; loop over
  tags instead: `for tag in v1.0.0 v1.1.0; do bash scripts/changelog.sh --to "$tag" --version "$tag"; done`
- **Link-only when the remote is known.** PR and commit links are generated from
  `git remote get-url origin`; override with `--repo-url` for forks and mirrors.

## Options

| Flag | Meaning |
|------|---------|
| `--from <ref>` | Start of the range (exclusive). Default: last reachable tag. |
| `--to <ref>` | End of the range. Default: `HEAD`. |
| `--version <v>` | Heading version. Default: `Unreleased`. |
| `--output <path>` | Target file. Default: `CHANGELOG.md`. |
| `--stdout` | Print only, touch no files. |
| `--dry-run` | Same as `--stdout`, but the wording tells the user nothing was written. |
| `--log-file <path>` | Replay a captured `git log` (CI, tests, repos without git history). |
| `--repo-url <url>` | Link target when `origin` is missing or wrong. |
| `--merges` | Include merge commits (excluded by default). |

## Failure modes

- **No tag yet** → falls back to the root commit and says so on stderr.
- **Empty range** → prints `_No changes._` and exits 0, so CI does not fail.
- **Last line of `git log`** has no trailing newline; the reader loop is written
  to keep it. Do not replace it with a plain `while read` — that silently loses
  the oldest commit of every range.
