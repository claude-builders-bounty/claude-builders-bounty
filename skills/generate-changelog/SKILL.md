---
name: generate-changelog
description: Generate a structured Keep-a-Changelog CHANGELOG.md from git history since the last tag. Use when the user asks for /generate-changelog, a release notes draft, or CHANGELOG.md from commits.
---

# /generate-changelog

Produce a Keep-a-Changelog-style `CHANGELOG.md` from commits **since the last git tag**.

## When to use

- User invokes `/generate-changelog` or asks to refresh `CHANGELOG.md`
- Preparing a release and needs Added / Fixed / Changed / Removed sections
- Auditing what landed after the previous tag

## Steps

1. Confirm the working directory is a git repo (`git rev-parse --git-dir`).
2. Run the generator (stdlib Python, no pip deps):

```bash
python3 skills/generate-changelog/scripts/changelog.py
# or from repo root after install:
bash changelog.sh
```

3. Open the written `CHANGELOG.md`, skim for miscategorized lines, then commit if the user wants.

## Optional flags

| Flag | Meaning |
|------|---------|
| `--stdout` | Print instead of writing a file |
| `-o PATH` | Custom output path |
| `--cwd PATH` | Another git repo |
| `--max-count N` | Cap commits scanned (default 200) |
| `--repo-name NAME` | Title used in the header |

## Categorization rules (opinionated)

1. **Conventional Commits** first: `feat`→Added, `fix`→Fixed, `docs|refactor|perf|test|build|ci|chore|style`→Changed.
2. **Removed wins on wording**: if the subject contains remove/delete/drop, categorize as Removed even when the type is `docs` or `chore`.
3. **Keyword fallback** for non-conventional subjects: add/introduce→Added, fix/bug→Fixed, change/update/upgrade→Changed, remove/delete→Removed.
4. **Breaking**: `type!:` or the word `breaking` prefixes the bullet with `⚠️ **BREAKING**`.
5. Merge/WIP subjects are kept under Changed (not dropped silently) so review stays honest.

## Output shape

```markdown
# Changelog

## [Unreleased] — YYYY-MM-DD

_Generated from commits since `vX.Y.Z`._

### Added
- ...

### Fixed
- ...

### Changed
- ...

### Removed
- ...
```

## Do not

- Invent commits that are not in `git log`
- Call external APIs or require network
- Overwrite an existing handwritten changelog without the user asking (default write path is `CHANGELOG.md` in `--cwd`)
