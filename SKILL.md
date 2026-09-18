---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history. Use when the user asks to build or refresh a changelog, summarize what changed since a release, or categorize commits into Added/Fixed/Changed/Removed.
---

# Generate Changelog

Produce a structured `CHANGELOG.md` from the project's git history, categorized into
`Added` / `Fixed` / `Changed` / `Removed`.

## When to use

- The user asks to generate, update, or build a changelog.
- The user asks "what changed since the last release/tag".
- A release is being prepared and the release notes need a commit-derived draft.

## Quick start

```bash
bash changelog.sh
```

The script is dependency-free (bash + git only), writes `CHANGELOG.md` in the
current directory, and prints the same content to stdout so it can be piped or
reviewed before writing.

## Behavior

- Commits are collected **since the most recent git tag** (or all history when no
  tag exists).
- Each commit subject is categorized by conventional-commit prefix:
  - `feat:` / `add:` / `new:` / `feature:` → **Added**
  - `fix:` / `bugfix:` / `hotfix:` → **Fixed**
  - `remove:` / `delete:` / `rm:` → **Removed**
  - anything else → **Changed**
- Commit hashes are shortened to 7 characters.
- Sections with no entries are omitted from the output.
- The top of the file records the range covered (`<oldest-tag>..<HEAD>`) and the
  generation timestamp.

## Configuration

All behavior is configurable via environment variables:

| Variable               | Default                       | Meaning                                             |
| ---------------------- | ----------------------------- | --------------------------------------------------- |
| `CHANGELOG_OUT`        | `CHANGELOG.md`                | Output file path. `-` prints to stdout only.        |
| `CHANGELOG_TITLE`      | `# Changelog`                 | Top-level heading.                                  |
| `CHANGELOG_SINCE`      | *(last tag)*                  | Override the commit range start.                    |
| `CHANGELOG_CATEGORIES` | `Added,Fixed,Changed,Removed` | Comma-separated section order and selection.        |

## Manual invocation

```bash
# all history (no tags yet)
CHANGELOG_OUT=CHANGES.md bash changelog.sh

# explicit range
CHANGELOG_SINCE=v1.0.0 bash changelog.sh

# stdout only, no file written
CHANGELOG_OUT=- bash changelog.sh
```

## Notes

- The script never modifies anything outside the working tree; it only reads
  git history and writes the requested output file.
- Body text beyond the subject line is intentionally ignored so the changelog
  stays compact. For richer release notes, edit the generated file by hand.
- Works on macOS / Linux stock bash. No associative arrays, no external tools
  beyond `git`, `date`, `mktemp`, `printf`.