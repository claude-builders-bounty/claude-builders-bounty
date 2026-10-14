---
name: generate-changelog
description: Build a structured CHANGELOG.md from git history since the last tag, grouping commits into Added / Fixed / Changed / Removed. Use when the user asks to update the changelog, write release notes, or summarise what changed since the last release.
---

# Generate changelog

Turn the repository's git history into a Keep a Changelog section. Every line comes
from `git log` — the skill does not invent entries.

## Steps

1. Check you are at the repository root and that there is history:

   ```bash
   git rev-parse --show-toplevel && git log --oneline -5
   ```

2. Preview the section without touching any file:

   ```bash
   bash .claude/skills/generate-changelog/changelog.sh --stdout
   ```

   Show that output to the user and ask whether the wording needs edits.

3. Write it when the user agrees. Without a version argument the section is
   `[Unreleased]`; with one it is that version. The new section is inserted **above**
   the existing ones, so the file stays newest-first:

   ```bash
   bash .claude/skills/generate-changelog/changelog.sh 1.2.0
   ```

4. Show the result:

   ```bash
   git diff CHANGELOG.md
   ```

## How commits are grouped

| Commit | Section |
| --- | --- |
| `feat:`, `feature:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `refactor:`, `perf:`, `style:`, `change:`, `update:` | Changed |
| `remove:`, `delete:`, `drop:`, `revert:`, `deprecate:` | Removed |
| `docs:`, `chore:`, `test:`, `ci:`, `build:` | skipped unless `--all` |
| anything else | keyword heuristics, then Changed |

`feat!:` / `fix(scope)!:` and bodies containing `BREAKING CHANGE:` are repeated in a
`### Breaking changes` block at the top of the section. Scopes become bold prefixes
(`feat(api): ...` → `- **api:** ...`).

## Options

| Flag | Effect |
| --- | --- |
| `[VERSION]` | Section title; defaults to `[Unreleased]` |
| `--stdout` | Print the section, write nothing |
| `--file <path>` | Output file (default `CHANGELOG.md`) |
| `--since <ref>` | Start after this ref (default: the last tag) |
| `--all` | Include maintenance commits |
| `--hashes` | Append the short hash to each entry |

## Notes

- Needs `git` and `bash`; no other dependency.
- Only commits reachable from `HEAD` are considered, and merge commits are skipped.
- If the range is empty the section says so instead of printing an empty list.
