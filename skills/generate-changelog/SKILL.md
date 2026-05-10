---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history using Conventional Commits. Use when the user asks to "create a changelog", "generate CHANGELOG.md", "update changelog", or runs the /generate-changelog command. Categorizes commits since the last git tag into Added / Changed / Fixed / Removed and surfaces breaking changes.
---

# generate-changelog

Generate a [Keep a Changelog](https://keepachangelog.com/) formatted `CHANGELOG.md`
from a repo's git history. Parses [Conventional Commits](https://www.conventionalcommits.org/)
and groups them into sections.

## When to use

- User says: "generate a changelog", "update CHANGELOG.md", "what's changed since last release"
- User invokes the `/generate-changelog` slash command
- Preparing release notes for a tag bump

## How to run

The skill ships a single bash script. Always invoke it from the repo root.

```bash
bash skills/generate-changelog/changelog.sh                   # write CHANGELOG.md (since last tag)
bash skills/generate-changelog/changelog.sh --stdout          # preview without writing
bash skills/generate-changelog/changelog.sh --version v1.2.0  # set the section heading
bash skills/generate-changelog/changelog.sh --from v1.0.0     # commits since v1.0.0
bash skills/generate-changelog/changelog.sh --all             # full changelog across all tags
```

## Decision flow

1. If `CHANGELOG.md` already exists and the user only wants new entries, run with
   `--stdout`, then merge the new section above existing content rather than overwriting.
2. If no git tags exist yet, omit `--from` — script falls back to all history under
   an `[Unreleased]` heading.
3. If the user wants a specific version label (`v1.2.0`), pass `--version v1.2.0`.
4. After generating, show the diff and ask the user to confirm before committing.

## Categorization rules

| Conventional type             | Section            |
| ----------------------------- | ------------------ |
| `feat` / `feature`            | Added              |
| `fix` / `bugfix` / `hotfix`   | Fixed              |
| `perf`, `refactor`, `style`, `docs`, `build`, `ci`, `chore`, `test` | Changed |
| `revert`                      | Removed            |
| Anything with `!` or `BREAKING CHANGE:` in body | ⚠ Breaking Changes (top) |
| Non-conventional subjects     | Heuristic match on "add/fix/remove" verbs, else `Other` |

Scope (e.g. `feat(api): ...`) is preserved as a bold prefix on the entry. Each
entry links back to the commit on GitHub when `origin` points at github.com.

## Example output

```markdown
# Changelog

## [v1.2.0] - 2026-05-10

### ⚠ Breaking Changes
- **api:** drop /v1 endpoints ([`a1b2c3d`](...))

### Added
- **cli:** add --json output flag ([`b2c3d4e`](...))

### Fixed
- handle empty git history ([`c3d4e5f`](...))

### Changed
- **deps:** bump tokio to 1.40 ([`d4e5f6a`](...))
```

See `README.md` in this skill folder for setup as a slash command.
