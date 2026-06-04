---
name: changelog-from-git
description: Generate a structured CHANGELOG.md from git history. Use when the user asks to "generate a changelog", "build release notes", "summarize commits since the last tag", or prepare a CHANGELOG for a release. Parses Conventional Commits, buckets them by semver tag into Keep a Changelog sections (Added/Changed/Deprecated/Removed/Fixed/Security), and flags breaking changes.
---

# Changelog From Git

Turn raw git history into a clean, release-ready `CHANGELOG.md` that follows the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format and
[Semantic Versioning](https://semver.org/).

## When to use

Trigger this skill when the user wants release notes or a changelog derived from
commits — e.g. "generate a changelog", "what changed since v1.2.0", "draft release
notes for the next version", or before cutting a release.

## How it works

`changelog_gen.py` is a zero-dependency Python script (standard library + the `git`
CLI). It:

1. Reads semver tags (`vX.Y.Z` / `X.Y.Z`) newest-first and buckets commits into one
   release block per tag, with everything after the newest tag under `[Unreleased]`.
2. Parses [Conventional Commits](https://www.conventionalcommits.org/) — `type(scope): desc`
   — and maps each type to a Keep a Changelog section:

   | Commit type | Section |
   |---|---|
   | `feat` / `feature` / `add` | Added |
   | `fix` / `bugfix` | Fixed |
   | `perf` / `refactor` / `revert` / `change` | Changed |
   | `deprecate` | Deprecated |
   | `remove` | Removed |
   | `security` / `sec` | Security |
   | anything else | Changed |

3. Detects breaking changes (`feat!:` or a `BREAKING CHANGE:` body) and lists them
   under a dedicated `### ⚠ BREAKING CHANGES` heading in that release block.
4. Drops noise (`chore`, `ci`, `build`, `test`, `style`, `docs`) by default; include
   it with `--include-all`.

## Usage

```bash
# Full changelog for the current repo, printed to stdout
python3 changelog_gen.py --repo /path/to/repo

# Write straight to CHANGELOG.md
python3 changelog_gen.py --repo /path/to/repo --output CHANGELOG.md

# Only what changed since the latest tag (release-note draft)
python3 changelog_gen.py --repo /path/to/repo --unreleased-only

# Include chore/ci/docs and non-conventional commits
python3 changelog_gen.py --repo /path/to/repo --include-all
```

Flags:

- `-r, --repo` — repository path (default `.`)
- `-o, --output` — write to a file instead of stdout
- `--unreleased-only` — only commits after the most recent semver tag
- `--include-all` — keep chore/ci/docs/test and non-conventional commits
- `--repo-url` — optional repository URL added as a footer link

## Agent workflow

1. Confirm the target repo path (default to the current working directory).
2. Run `changelog_gen.py` with `--unreleased-only` first to preview the next release.
3. If the user wants the full history, run without that flag and write to `CHANGELOG.md`.
4. Show the generated file and offer to refine grouping or wording.

## Notes

- Merge commits are excluded (`--no-merges`) so the changelog stays signal-only.
- Untagged repos produce a single `[Unreleased]` block.
- Non-conventional commit subjects are dropped by default to keep output clean; use
  `--include-all` when the history predates a Conventional Commits convention.
